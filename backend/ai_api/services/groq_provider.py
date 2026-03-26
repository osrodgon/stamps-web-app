"""
Groq LLM Provider for AI-powered stamp series extraction.

This module provides integration with Groq API to perform AI-powered
research and extraction of stamp series information. It processes stamp issue
data and extracts structured information using Groq's high-performance LLMs.

The Groq provider is designed to work as a drop-in replacement for other LLM
providers, maintaining the same interface while leveraging Groq's optimized
inference capabilities for faster response times.

The provider supports batch processing for large stamp series to avoid
output token limits. When a series has more stamps than the configured
LLM_BATCH_SIZE threshold, the extraction is split into:
1. A header extraction for series-level information
2. Multiple batch extractions for stamp data
3. A final merge of all results

Dependencies:
    - groq: Groq API client for AI processing
    - common.api.messages: For standardized error messages
    - common.log.logger: For consistent application logging
    - ai_api.services.base_llm_provider: For the base provider interface
    - ai_api.services.prompts: For prompt templates

Integration:
    - Used by LLMService via the provider factory
    - Part of the ai_api.services module
    - Works with SearchService and ScrapingService for complete series extraction

Usage:
    from ai_api.services.groq_provider import GroqProvider
    provider = GroqProvider()
    result = provider.series_extract("Olimpiadas", "1992", "cleaned_data")
"""

import os
import json
from typing import Dict, Any, List
from groq import Groq
from common.api.messages import Messages
from common.log.logger import Logger
from ai_api.services.base_llm_provider import BaseLLMProvider
from ai_api.services.prompts import (
    SERIES_EXTRACTION_PROMPT_TEMPLATE,
    SERIES_HEADER_EXTRACTION_PROMPT_TEMPLATE,
    SERIES_BATCH_EXTRACTION_PROMPT_TEMPLATE
)


class GroqProvider(BaseLLMProvider):
    """
    Groq LLM provider for AI-powered research on stamp series.
    
    This provider handles the integration with Groq API to research
    stamp series information based on issue name, date, and cleaned data.
    
    The provider provides methods for:
    - Initializing and configuring the Groq API client
    - Formatting prompts for series extraction
    - Cleaning and validating AI responses
    - Performing complete series extraction workflows
    
    Attributes:
        client: Groq API client instance
        generation_config: Configuration for AI content generation
        prompt_template: Template for series extraction prompts
        
    Usage:
        groq_provider = GroqProvider()
        result = groq_provider.series_extract("Olimpiadas", "1992", "cleaned_data")
    """
    
    def __init__(self):
        """
        Initialize the GroqProvider.
        
        Sets up Groq API configuration and loads the series extraction prompt template.
        """
        super().__init__()
        
        # Configure Groq API
        api_key = self._get_groq_api_key()
        if not api_key:
            raise ValueError(Messages.AI.missing_api_key())
        
        model_name = self._get_groq_model_name()
        if not model_name:
            raise ValueError(Messages.AI.missing_model_name())
        
        self.client = Groq(api_key=api_key)
        self.model_name = model_name
        
        # Load the series extraction prompt templates
        self.prompt_template = SERIES_EXTRACTION_PROMPT_TEMPLATE
        self.header_prompt_template = SERIES_HEADER_EXTRACTION_PROMPT_TEMPLATE
        self.batch_prompt_template = SERIES_BATCH_EXTRACTION_PROMPT_TEMPLATE
        
        self.log.debug(f"GroqProvider initialized with model: {model_name}")
    
    def _get_groq_api_key(self) -> str:
        """
        Get the Groq API key from environment variables.
        
        Returns:
            str: The Groq API key
            
        Raises:
            ValueError: If GROQ_API_KEY environment variable is not set
        """
        api_key = os.getenv('GROQ_API_KEY')
        if not api_key:
            self.log.error("GROQ_API_KEY environment variable is required")
        return api_key
    
    def _get_groq_model_name(self) -> str:
        """
        Get the Groq model name from environment variables.
        
        Returns:
            str: The Groq model name
            
        Raises:
            ValueError: If GROQ_MODEL_NAME environment variable is not set
        """
        model_name = os.getenv('GROQ_MODEL_NAME', 'llama3-8b-8192')
        return model_name
    
    def series_extract(
        self,
        name: str,
        date: str,
        clean_data: str
    ) -> Dict[str, Any]:
        """
        Perform AI-powered extraction of stamp series information using Groq.
        
        This is the main method that implements the BaseLLMProvider interface.
        It takes stamp issue parameters and cleaned data, formats them into a prompt,
        sends the request to Groq API, and processes the response.
        
        For large series (more than LLM_BATCH_SIZE stamps), this method automatically
        splits the extraction into batches:
        1. Extract series-level information (header)
        2. Process stamps in batches
        3. Merge all results into a single response
        
        Args:
            name (str): The name of the stamp issue (e.g., "Olimpiadas", "Animales")
            date (str): The publication date of the stamp issue (e.g., "1992", "2023")
            clean_data (str):   The cleaned and processed data about the stamp issue
                                that will be used as input for the AI model. This should
                                contain relevant information extracted from previous
                                processing steps.

        Returns:
            Dict[str, Any]: A dictionary containing the extracted stamp series information
                            in structured format as returned by the AI model. The exact
                            structure depends on the prompt template and model response.

        Raises:
            ValueError: If clean_data is empty or None
            ValueError: If the AI service returns an empty response
            Exception: If the AI service call fails or returns invalid data
            
        Example:
            >>> groq_provider = GroqProvider()
            >>> result = groq_provider.series_extract(
            ...     name="Olimpiadas",
            ...     date="1992", 
            ...     clean_data="Olimpiadas Barcelona 1992 stamp series information..."
            ... )
            >>> print(result)  # Returns structured data about the stamp series
            
        Note:
            This method includes comprehensive error handling and logging. It validates
            input parameters, formats prompts using the inherited template, makes the
            API call to Groq, cleans the response, and parses it as JSON.
            Any errors during this process are logged and re-raised with descriptive messages.
        """
        self.log.debug(f"Starting Groq extraction for series: {name} ({date})")
        
        # Validate input parameters
        if not clean_data or not clean_data.strip():
            raise ValueError(Messages.AI.missing_input_data())
        
        try:
            # Parse the clean_data to check if batching is needed
            parsed_data = self._parse_clean_data(clean_data)
            stamps = parsed_data.get("stamps", [])
            serie_info = parsed_data.get("serie_info", {})
            
            # Check if batch processing is needed
            if self._should_batch(len(stamps)):
                self.log.debug(f"Batch processing required for {len(stamps)} stamps")
                return self._batch_extract(name, date, serie_info, stamps)
            
            # Single extraction for small series
            self.log.debug(f"Single extraction for {len(stamps)} stamps")
            return self._single_extract(clean_data)
            
        except Exception as e:
            self.log.error(f"Groq extraction failed for series {name}: {str(e)}")
            raise Exception(Messages.AI.service_error(str(e)))
    
    def _single_extract(self, clean_data: str) -> Dict[str, Any]:
        """
        Perform a single extraction for small series.
        
        Args:
            clean_data (str): The cleaned data to process.
            
        Returns:
            Dict[str, Any]: The extracted series information.
        """
        # Format the prompt with the provided parameters
        prompt = self._format_prompt(clean_data)
                    
        # Call the Groq model
        self.log.debug(f"Sending request to Groq API with model: {self.model_name}")
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.0,
            max_tokens=8192,
            response_format={"type": "json_object"}
        )
        
        if not response or not response.choices or not response.choices[0].message:
            self.log.warning("Received empty response from Groq API")
            raise ValueError(Messages.AI.empty_response())
        
        response_text = response.choices[0].message.content
        self.log.debug(f"Received Groq response (length: {len(response_text)})")
        self.log.debug(response_text)
        
        # Validate and parse the response
        cleaned_response = self._clean_json_response(response_text)
        return self._parse_json_response(cleaned_response)
    
    def _extract_header(self, serie_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract series-level information (header).
        
        Args:
            serie_info (Dict[str, Any]): The series information to process.
            
        Returns:
            Dict[str, Any]: Extracted series-level data.
        """
        prompt = self._format_header_prompt(serie_info)
        
        self.log.debug("Sending header extraction request to Groq API")
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.0,
            max_tokens=8192,
            response_format={"type": "json_object"}
        )
        
        if not response or not response.choices or not response.choices[0].message:
            self.log.warning("Received empty response for header extraction")
            raise ValueError(Messages.AI.empty_response())
        
        cleaned_response = self._clean_json_response(response.choices[0].message.content)
        
        self.log.debug(f"Received Groq header response (length: {len(cleaned_response)})")
        self.log.debug(cleaned_response)
        
        return self._parse_json_response(cleaned_response)
    
    def _extract_batch(
        self,
        serie_info: Dict[str, Any],
        stamp_batch: List[Dict[str, Any]],
        batch_number: int,
        total_batches: int
    ) -> Dict[str, Any]:
        """
        Extract a batch of stamps.
        
        Args:
            serie_info (Dict[str, Any]): Series context for the extraction.
            stamp_batch (List[Dict[str, Any]]): The batch of stamps to process.
            batch_number (int): Current batch number (1-indexed).
            total_batches (int): Total number of batches.
            
        Returns:
            Dict[str, Any]: Extracted stamp data for this batch.
        """
        prompt = self._format_batch_prompt(serie_info, stamp_batch, batch_number, total_batches)
        
        self.log.debug(f"Sending batch {batch_number}/{total_batches} extraction request to Groq API")
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.0,
            max_tokens=8192,
            response_format={"type": "json_object"}
        )
        
        if not response or not response.choices or not response.choices[0].message:
            self.log.warning(f"Received empty response for batch {batch_number}")
            raise ValueError(Messages.AI.empty_response())
        
        cleaned_response = self._clean_json_response(response.choices[0].message.content)
        
        self.log.debug(f"Received Groq batch response (length: {len(cleaned_response)})")
        self.log.debug(cleaned_response)
        
        return self._parse_json_response(cleaned_response)
