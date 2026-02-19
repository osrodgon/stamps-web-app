"""
LLM service for AI-powered stamp series extraction.

This module provides a unified interface for AI-powered research and extraction
of stamp series information using multiple LLM providers (Google Gemini, Groq, etc.).

The service acts as a facade that delegates to the appropriate LLM provider based
on configuration, providing a consistent interface regardless of the underlying
AI service being used.

Dependencies:
    - ai_api.services.provider_factory: For provider instantiation
    - ai_api.services.base_llm_provider: For the base provider interface
    - common.api.messages: For standardized error messages
    - common.log.logger: For consistent application logging

Integration:
    - Used by SeriesExtractionView in the AI workflow
    - Part of the ai_api.services module
    - Works with SearchService and ScrapingService for complete series extraction
"""

from typing import Dict, Any
from common.api.messages import Messages
from common.log.logger import Logger
from ai_api.services.provider_factory import ProviderFactory
from ai_api.services.base_llm_provider import BaseLLMProvider


class LLMService(Logger):
    """
    Service for performing AI-powered research on stamp series using configurable LLM providers.
    
    This service handles the integration with various LLM APIs to research
    stamp series information based on issue name, date, and optional Edifil number.
    
    The service provides methods for:
    - Initializing and configuring the appropriate LLM provider based on environment
    - Delegating series extraction to the configured provider
    - Handling provider-specific error handling and logging
    
    Attributes:
        provider: The configured LLM provider instance
        
    Usage:
        llm_service = LLMService()
        result = llm_service.series_extract("Olimpiadas", "1992", "cleaned_data")
    """
    
    def __init__(self):
        """
        Initialize the LLMService.
        
        Sets up the provider factory and loads the configured LLM provider.
        """
        super().__init__()
        
        # Initialize the provider factory
        self.provider_factory = ProviderFactory()
        
        # Get the configured provider
        self.provider = self.provider_factory.create_provider()
        
        self.log.debug(f"LLMService initialized with provider: {type(self.provider).__name__}")
    
    def series_extract(
        self,
        name: str,
        date: str,
        clean_data: str
    ) -> Dict[str, Any]:
        """
        Perform AI-powered extraction of stamp series information using the configured LLM provider.
        
        This is the main method that delegates to the appropriate LLM provider
        based on the current configuration. It takes stamp issue parameters and
        cleaned data, and processes them using the selected AI model.
        
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
            This method delegates to the configured provider's series_extract method.
            The actual AI service used depends on the LLM_PROVIDER environment variable.
        """
        self.log.debug(f"Starting AI extraction for series: {name} ({date}) using {type(self.provider).__name__}")
        
        try:
            # Delegate to the configured provider
            result = self.provider.series_extract(name, date, clean_data)
            
            self.log.debug(f"AI extraction completed successfully for series: {name}")
            return result
            
        except Exception as e:
            self.log.error(f"AI extraction failed for series {name}: {str(e)}")
            raise Exception(Messages.AI.service_error(str(e)))