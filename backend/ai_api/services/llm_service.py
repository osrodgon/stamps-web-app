"""
LLM service for AI-powered stamp series extraction.

This module provides integration with Google Gemini API to perform AI-powered
research and extraction of stamp series information. It processes stamp issue
data and extracts structured information using large language models.

The service is designed to work in conjunction with the SearchService and 
ScrapingService to gather comprehensive data about stamp series for the 
philatelic collection management application.

Dependencies:
    - google.genai: Google Gemini API client for AI processing
    - common.api.messages: For standardized error messages
    - common.log.logger: For consistent application logging
    - ai_api.services.prompts: For prompt templates

Integration:
    - Used by SeriesExtractionView in the AI workflow
    - Part of the ai_api.services module
    - Works with SearchService for complete series extraction
"""

import json
import re
from typing import Dict, Any
from _backend.settings import GEMINI_API_KEY, GEMINI_MODEL_NAME
from google import genai
from google.genai import types

from common.api.messages import Messages
from common.log.logger import Logger
from ai_api.services.prompts import SERIES_EXTRACTION_PROMPT_TEMPLATE


class LLMService(Logger):
    """
    Service for performing AI-powered research on stamp series using Google Gemini.
    
    This service handles the integration with Google Gemini API to research
    stamp series information based on issue name, date, and optional Edifil number.
    
    The service provides methods for:
    - Initializing and configuring the Google Gemini API client
    - Formatting prompts for series extraction
    - Cleaning and validating AI responses
    - Performing complete series extraction workflows
    
    Attributes:
        client: Google Gemini API client instance
        generation_config: Configuration for AI content generation
        prompt_template: Template for series extraction prompts
        
    Usage:
        llm_service = LLMService()
        result = llm_service.series_extract("Olimpiadas", "1992", "cleaned_data")
    """
    
    def __init__(self):
        """
        Initialize the LLMService.
        
        Sets up Google Gemini API configuration and loads the series extraction prompt template.
        """
        super().__init__()
        
        # Configure Google Gemini API
        api_key = GEMINI_API_KEY
        if not api_key:
            raise ValueError(Messages.AI.missing_api_key())
        
        if not GEMINI_MODEL_NAME:
            raise ValueError(Messages.AI.missing_model_name())
        
        self.client = genai.Client(api_key=api_key)
        
        # Create the configuration  
        self.generation_config = types.GenerateContentConfig(
            temperature=0.0,
            top_p=1.0,
            top_k=1,
            max_output_tokens=8192,
            response_mime_type="application/json"
        )
        
        # Load the series extraction prompt template
        self.prompt_template = SERIES_EXTRACTION_PROMPT_TEMPLATE
    
    def _format_prompt(self, input_data: str) -> str:
        """
        Format the prompt template with the provided input data.
        
        This method replaces the placeholder {{ input_data }} in the prompt template
        with the actual cleaned data to be processed by the AI model.
        
        Args:
            input_data (str):   The cleaned input data to be inserted into the prompt template.
                                This should be the processed stamp issue information.

        Returns:
            str: The formatted prompt with the input data inserted into the template.
            
        Example:
            >>> service = LLMService()
            >>> formatted = service._format_prompt("Olimpiadas 1992 data")
            >>> print(formatted)  # Returns template with "Olimpiadas 1992 data" inserted
            
        Note:
            This is a private method used internally by the series_extract method.
            The prompt template is loaded during initialization from the prompts module.
        """
        formatted_prompt = self.prompt_template.replace(
            "{{ input_data }}", input_data
        )
        
        return formatted_prompt
    
    def _clean_json_response(self, response_text: str) -> str:
        """
        Clean the AI response text by removing markdown code blocks.
        
        Args:
            response_text: Raw response text from the AI model.
            
        Returns:
            Cleaned JSON string.
        """
        # Use regex to find the JSON block within markdown code fences or standalone
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", response_text, re.DOTALL)
        if match:
            return match.group(1)
        
        # Fallback: find the first '{' and the last '}'
        start = response_text.find('{')
        end = response_text.rfind('}')
        
        if start != -1 and end != -1:
            return response_text[start:end+1]
            
        return response_text.strip()

    def series_extract(
        self,
        name: str,
        date: str,
        clean_data: str
    ) -> Dict[str, Any]:
        """
        Perform AI-powered extraction of stamp series information using Google Gemini.
        
        This is the main method that orchestrates the complete AI extraction workflow.
        It takes stamp issue parameters and cleaned data, formats them into a prompt,
        sends the request to Google Gemini API, and processes the response.
        
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
            >>> llm_service = LLMService()
            >>> result = llm_service.series_extract(
            ...     name="Olimpiadas",
            ...     date="1992", 
            ...     clean_data="Olimpiadas Barcelona 1992 stamp series information..."
            ... )
            >>> print(result)  # Returns structured data about the stamp series
            
        Note:
            This method includes comprehensive error handling and logging. It validates
            input parameters, formats prompts using the internal template, makes the
            API call to Google Gemini, cleans the response, and parses it as JSON.
            Any errors during this process are logged and re-raised with descriptive messages.
        """
        self.log.debug(f"Starting AI extraction for series: {name} ({date})")
        
        # Validate input parameters
        if not clean_data or not clean_data.strip():
            raise ValueError(Messages.AI.missing_input_data())
        
        
        try:
            # Format the prompt with the provided parameters
            prompt = self._format_prompt(clean_data)
                        
            # Call the AI model
            self.log.debug("Sending request to Google Gemini API")
            response = self.client.models.generate_content(
                model=GEMINI_MODEL_NAME,
                contents=prompt,
                config=self.generation_config
            )
            
            if not response or not response.text:
                self.log.warning("Received empty response from Google Gemini API")
                raise ValueError(Messages.AI.empty_response())
            
            self.log.debug(f"Received AI response (length: {len(response.text)})")
            
            # Validate and parse the response
            self._clean_json_response(response.text)
            
            self.log.debug(f"AI extraction completed successfully for series: {name}")
            return json.loads(response.text)
            
        except Exception as e:
            self.log.error(f"AI extraction failed for series {name}: {str(e)}")
            raise Exception(Messages.AI.service_error(str(e)))
