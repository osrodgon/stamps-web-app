"""
Base LLM Provider Interface for AI-powered stamp series extraction.

This module defines the abstract base class for LLM providers, enabling
support for multiple LLM services (Google Gemini, Groq, etc.) with a
consistent interface.

The base provider defines the contract that all LLM providers must implement,
ensuring consistent behavior across different AI services while allowing
for provider-specific optimizations and configurations.

Dependencies:
    - abc: For abstract base class implementation
    - typing: For type hints and Union types
    - common.log.logger: For consistent application logging

Integration:
    - Used by LLMService to provide a unified interface for different LLM providers
    - Implemented by specific provider classes (GeminiProvider, GroqProvider, etc.)
    - Part of the ai_api.services module

Usage:
    class MyProvider(BaseLLMProvider):
        def series_extract(self, name: str, date: str, clean_data: str) -> Dict[str, Any]:
            # Implementation specific to the provider
            pass
"""
import re
import json
from abc import ABC, abstractmethod
from typing import Dict, Any, List
from common.log.logger import Logger
from _backend.settings import LLM_BATCH_SIZE


class BaseLLMProvider(Logger, ABC):
    """
    Abstract base class for LLM providers.
    
    This class defines the contract that all LLM providers must implement.
    It provides a consistent interface for different LLM services while
    allowing for provider-specific optimizations and configurations.
    
    All LLM providers should inherit from this class and implement the
    required methods to ensure consistent behavior across different AI services.
    
    Attributes:
        prompt_template (str): The template for series extraction prompts
        
    Usage:
        class GeminiProvider(BaseLLMProvider):
            def __init__(self):
                super().__init__()
                # Initialize provider-specific configuration
    """
    
    def __init__(self):
        """
        Initialize the base LLM provider.
        
        Sets up the logger and initializes the prompt template.
        Subclasses should call super().__init__() in their __init__ method.
        """
        super().__init__()
        self.prompt_template = None
    
    @abstractmethod
    def series_extract(
        self,
        name: str,
        date: str,
        clean_data: str
    ) -> Dict[str, Any]:
        """
        Perform AI-powered extraction of stamp series information.
        
        This is the main method that all LLM providers must implement.
        It takes stamp issue parameters and cleaned data, processes them
        using the specific LLM service, and returns structured information.
        
        Args:
            name (str): The name of the stamp issue (e.g., "Olimpiadas", "Animales")
            date (str): The publication date of the stamp issue (e.g., "1992", "2023")
            clean_data (str):   The cleaned and processed data about the stamp issue
                                that will be used as input for the AI model
        
        Returns:
            Dict[str, Any]: A dictionary containing the extracted stamp series
                            information in structured format as returned by the AI model.
                            The exact structure depends on the prompt template and model response.
        
        Raises:
            ValueError: If clean_data is empty or None
            ValueError: If the AI service returns an empty response
            Exception: If the AI service call fails or returns invalid data
        
        Note:
            This method must be implemented by all subclasses and should include
            comprehensive error handling and logging specific to the provider.
        """
        pass
    
    def _format_prompt(self, input_data: str) -> str:
        """
        Format the prompt template with the provided input data.
        
        This helper method replaces the placeholder {{ input_data }} in the
        prompt template with the actual cleaned data to be processed by the AI model.
        
        Args:
            input_data (str): The cleaned input data to be inserted into the prompt template.
        
        Returns:
            str: The formatted prompt with the input data inserted into the template.
        
        Raises:
            ValueError: If prompt_template is not set
            ValueError: If input_data is empty or None
        
        Note:
            This is a common implementation that can be used by all providers.
            Providers can override this method if they need provider-specific formatting.
        """
        if not self.prompt_template:
            raise ValueError("Prompt template not set. Please set self.prompt_template in __init__.")
        
        if not input_data or not input_data.strip():
            raise ValueError("Input data cannot be empty or None.")
        
        formatted_prompt = self.prompt_template.replace("{{ input_data }}", input_data)
        return formatted_prompt
    
    def _clean_json_response(self, response_text: str) -> str:
        """
        Clean the AI response text by removing markdown code blocks.
        
        This helper method extracts clean JSON from AI responses that may
        include markdown formatting or other non-JSON content.
        
        Args:
            response_text (str): Raw response text from the AI model.
        
        Returns:
            str: Cleaned JSON string.
        
        Note:
            This is a common implementation that can be used by all providers.
            Providers can override this method if they need provider-specific cleaning.
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
    
    def _should_batch(self, stamps_count: int) -> bool:
        """
        Determine if batch processing is needed based on stamp count.
        
        Args:
            stamps_count (int): The number of stamps in the series.
        
        Returns:
            bool: True if the stamp count exceeds the batch threshold, False otherwise.
        """
        return stamps_count > LLM_BATCH_SIZE
    
    def _split_into_batches(self, stamps: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """
        Split a list of stamps into batches for processing.
        
        Args:
            stamps (List[Dict[str, Any]]): The list of stamp dictionaries to split.
        
        Returns:
            List[List[Dict[str, Any]]]: A list of batches, where each batch contains
                                        at most LLM_BATCH_SIZE stamps.
        """
        batches = []
        for i in range(0, len(stamps), LLM_BATCH_SIZE):
            batches.append(stamps[i:i + LLM_BATCH_SIZE])
        return batches
    
    def _format_header_prompt(self, serie_info: Dict[str, Any]) -> str:
        """
        Format the header extraction prompt with series info.
        
        Args:
            serie_info (Dict[str, Any]): The series-level information dictionary.
        
        Returns:
            str: The formatted prompt for header extraction.
        
        Raises:
            ValueError: If the header prompt template is not set.
        """
        if not self.header_prompt_template:
            raise ValueError("Header prompt template not set. Please set self.header_prompt_template in __init__.")
        
        input_data = json.dumps(serie_info, ensure_ascii=False)
        return self.header_prompt_template.replace("{{ input_data }}", input_data)
    
    def _format_batch_prompt(
        self,
        serie_info: Dict[str, Any],
        stamp_batch: List[Dict[str, Any]],
        batch_number: int,
        total_batches: int
    ) -> str:
        """
        Format the batch extraction prompt with stamp data and series context.
        
        Args:
            serie_info (Dict[str, Any]): The series-level information for context.
            stamp_batch (List[Dict[str, Any]]): The batch of stamps to process.
            batch_number (int): The current batch number (1-indexed).
            total_batches (int): The total number of batches.
        
        Returns:
            str: The formatted prompt for batch extraction.
        
        Raises:
            ValueError: If the batch prompt template is not set.
        """
        if not self.batch_prompt_template:
            raise ValueError("Batch prompt template not set. Please set self.batch_prompt_template in __init__.")
        
        series_context = json.dumps(serie_info, ensure_ascii=False)
        input_data = json.dumps({"stamps": stamp_batch}, ensure_ascii=False)
        
        prompt = self.batch_prompt_template.replace("{{ series_context }}", series_context)
        prompt = prompt.replace("{{ batch_number }}", str(batch_number))
        prompt = prompt.replace("{{ total_batches }}", str(total_batches))
        prompt = prompt.replace("{{ input_data }}", input_data)
        
        return prompt
    
    def _parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse the cleaned JSON response into a dictionary.
        
        Args:
            response_text (str): The cleaned JSON response text.
            
        Returns:
            Dict[str, Any]: Parsed JSON as a dictionary.
            
        Raises:
            ValueError: If the response cannot be parsed as JSON.
        """
        try:
            return json.loads(response_text)
        except json.JSONDecodeError as e:
            self.log.error(f"Failed to parse JSON response: {str(e)}")
            self.log.error(f"Response text: {response_text}")
            raise ValueError(f"Invalid JSON response: {str(e)}")
    
    def _parse_clean_data(self, clean_data: str) -> Dict[str, Any]:
        """
        Parse the clean_data string into a dictionary.
        
        This method attempts to parse the cleaned data string, which may be
        in JSON format or Python literal format, into a dictionary structure.
        
        Args:
            clean_data (str): The cleaned data as a string (may be JSON or dict string).
            
        Returns:
            Dict[str, Any]: Parsed data as a dictionary with 'serie_info' and 'stamps' keys.
        
        Note:
            If parsing fails, returns an empty structure with 'serie_info' and 'stamps' keys.
        """
        try:
            # Try JSON parse first
            return json.loads(clean_data)
        except json.JSONDecodeError:
            # Try evaluating as Python literal
            try:
                import ast
                return ast.literal_eval(clean_data)
            except (ValueError, SyntaxError):
                # Return empty structure if parsing fails
                self.log.warning("Could not parse clean_data, using empty structure")
                return {"serie_info": {}, "stamps": []}
    
    @abstractmethod
    def _single_extract(self, clean_data: str) -> Dict[str, Any]:
        """
        Perform a single extraction for small series.
        
        This method must be implemented by all LLM providers to handle
        the provider-specific API call for series extraction.
        
        Args:
            clean_data (str): The cleaned data to process.
            
        Returns:
            Dict[str, Any]: The extracted series information.
        """
        pass
    
    @abstractmethod
    def _extract_header(self, serie_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract series-level information (header).
        
        This method must be implemented by all LLM providers to handle
        the provider-specific API call for header extraction during batch processing.
        
        Args:
            serie_info (Dict[str, Any]): The series information to process.
            
        Returns:
            Dict[str, Any]: Extracted series-level data.
        """
        pass
    
    @abstractmethod
    def _extract_batch(
        self,
        serie_info: Dict[str, Any],
        stamp_batch: List[Dict[str, Any]],
        batch_number: int,
        total_batches: int
    ) -> Dict[str, Any]:
        """
        Extract a batch of stamps.
        
        This method must be implemented by all LLM providers to handle
        the provider-specific API call for batch extraction during batch processing.
        
        Args:
            serie_info (Dict[str, Any]): Series context for the extraction.
            stamp_batch (List[Dict[str, Any]]): The batch of stamps to process.
            batch_number (int): Current batch number (1-indexed).
            total_batches (int): Total number of batches.
            
        Returns:
            Dict[str, Any]: Extracted stamp data for this batch.
        """
        pass
    
    def _batch_extract(
        self,
        name: str,
        date: str,
        serie_info: Dict[str, Any],
        stamps: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Perform batch extraction for large series.
        
        This method provides the orchestration logic for batch processing,
        delegating the actual API calls to the provider-specific implementations
        of _extract_header and _extract_batch.
        
        The process is:
        1. Extract header (series-level information)
        2. Process stamps in batches
        3. Merge all results
        
        Args:
            name (str): The name of the stamp issue.
            date (str): The publication date.
            serie_info (Dict[str, Any]): Series-level information.
            stamps (List[Dict[str, Any]]): List of stamp dictionaries.
            
        Returns:
            Dict[str, Any]: Merged extraction results.
            
        Raises:
            Exception: If any batch extraction fails.
        """
        # Step 1: Extract header (series-level information)
        self.log.debug("Extracting series header information")
        header_result = self._extract_header(serie_info)
        
        # Step 2: Process stamps in batches
        batches = self._split_into_batches(stamps)
        total_batches = len(batches)
        all_stamps = []
        
        self.log.debug(f"Processing {total_batches} batches")
        
        for i, batch in enumerate(batches, start=1):
            self.log.debug(f"Processing batch {i}/{total_batches} with {len(batch)} stamps")
            batch_result = self._extract_batch(serie_info, batch, i, total_batches)
            batch_stamps = batch_result.get("stamps", [])
            all_stamps.extend(batch_stamps)
        
        # Step 3: Merge results
        header_result["stamps"] = all_stamps
        self.log.debug(f"Batch extraction completed with {len(all_stamps)} stamps total")
        
        return header_result
