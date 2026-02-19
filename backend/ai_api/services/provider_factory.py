"""
LLM Provider Factory for AI-powered stamp series extraction.

This module provides a factory pattern implementation for creating and managing
different LLM providers (Google Gemini, Groq, etc.) based on configuration.

The factory pattern allows for dynamic provider selection while maintaining
a consistent interface across all providers, making it easy to switch between
different LLM services without changing the calling code.

Dependencies:
    - typing: For type hints and Union types
    - common.api.messages: For standardized error messages
    - common.log.logger: For consistent application logging
    - ai_api.services.base_llm_provider: For the base provider interface
    - ai_api.services.gemini_provider: For Google Gemini provider
    - ai_api.services.groq_provider: For Groq provider

Integration:
    - Used by LLMService to instantiate the appropriate provider
    - Part of the ai_api.services module
    - Works with environment-based configuration

Usage:
    from ai_api.services.provider_factory import ProviderFactory
    provider = ProviderFactory.create_provider()
    result = provider.series_extract("Olimpiadas", "1992", "cleaned_data")
"""

from typing import Union
from common.api.messages import Messages
from common.log.logger import Logger
from ai_api.services.base_llm_provider import BaseLLMProvider
from ai_api.services.gemini_provider import GeminiProvider
from ai_api.services.groq_provider import GroqProvider


class ProviderFactory(Logger):
    """
    Factory class for creating LLM providers.
    
    This factory handles the instantiation of different LLM providers based on
    environment configuration. It provides a centralized way to manage provider
    selection and ensures consistent initialization across all providers.
    
    Supported providers:
    - Google Gemini (default)
    - Groq
    
    Attributes:
        PROVIDER_TYPES (dict): Mapping of provider type names to provider classes
        
    Usage:
        factory = ProviderFactory()
        provider = factory.create_provider()
    """
    
    PROVIDER_TYPES = {
        'gemini': GeminiProvider,
        'groq': GroqProvider,
    }
    
    def __init__(self):
        """
        Initialize the ProviderFactory.
        
        Sets up the logger for the factory.
        """
        super().__init__()
    
    def create_provider(self) -> BaseLLMProvider:
        """
        Create and return an LLM provider instance based on configuration.
        
        This method reads the LLM_PROVIDER environment variable to determine
        which provider to instantiate. If not specified, it defaults to Gemini.
        
        Returns:
            BaseLLMProvider: An instance of the configured LLM provider
            
        Raises:
            ValueError: If the specified provider type is not supported
            Exception: If provider initialization fails
            
        Example:
            >>> factory = ProviderFactory()
            >>> provider = factory.create_provider()
            >>> result = provider.series_extract("Olimpiadas", "1992", "cleaned_data")
            
        Note:
            The provider type is determined by the LLM_PROVIDER environment variable.
            Supported values: 'gemini', 'groq'
            Default: 'gemini' if not specified
        """
        import os
        
        provider_type = os.getenv('LLM_PROVIDER', 'gemini').lower()
        
        self.log.debug(f"Creating LLM provider of type: {provider_type}")
        
        if provider_type not in self.PROVIDER_TYPES:
            error_msg = f"Unsupported LLM provider type: {provider_type}. Supported types: {list(self.PROVIDER_TYPES.keys())}"
            self.log.error(error_msg)
            raise ValueError(error_msg)
        
        provider_class = self.PROVIDER_TYPES[provider_type]
        
        try:
            provider = provider_class()
            self.log.info(f"Successfully created {provider_type} provider")
            return provider
        except Exception as e:
            self.log.error(f"Failed to create {provider_type} provider: {str(e)}")
            raise Exception(f"Provider initialization failed: {str(e)}")
    
    @classmethod
    def get_available_providers(cls) -> list:
        """
        Get a list of available provider types.
        
        Returns:
            list: List of available provider type names
            
        Example:
            >>> providers = ProviderFactory.get_available_providers()
            >>> print(providers)  # ['gemini', 'groq']
        """
        return list(cls.PROVIDER_TYPES.keys())
    
    @classmethod
    def is_provider_available(cls, provider_type: str) -> bool:
        """
        Check if a specific provider type is available.
        
        Args:
            provider_type (str): The provider type to check
            
        Returns:
            bool: True if the provider type is available, False otherwise
            
        Example:
            >>> is_available = ProviderFactory.is_provider_available('groq')
            >>> print(is_available)  # True or False
        """
        return provider_type.lower() in cls.PROVIDER_TYPES