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

from abc import ABC, abstractmethod
from typing import Dict, Any
from common.log.logger import Logger


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
            clean_data (str): The cleaned and processed data about the stamp issue
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
        import re
        
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