"""
LLM provider factory for AI-powered stamp series extraction.

There is one provider — opencode — so this factory is deliberately thin: it
exists so the rest of the module asks for "a provider" instead of naming a class,
and so adding a second one later means touching one dictionary. It does not read
`LLM_PROVIDER` any more: with a single entry, an environment variable that can
only hold one valid value is a way to break a deployment by leaving a stale value
behind.

Dependencies:
    - ai_api.services.base_llm_provider: the interface a provider implements
    - ai_api.services.opencode_provider: the implementation
    - common.log.logger: for consistent logging

Usage:
    from ai_api.services.provider_factory import ProviderFactory
    provider = ProviderFactory().create_provider()
    result = provider.series_extract("Olimpiadas", "1992", "cleaned_data")
"""

from common.log.logger import Logger
from ai_api.services.base_llm_provider import BaseLLMProvider
from ai_api.services.opencode_provider import OpenCodeProvider


class ProviderFactory(Logger):
    """
    Factory for the LLM provider used by the API.

    Attributes:
        PROVIDER_TYPES (dict): mapping of provider name to provider class.

    Usage:
        factory = ProviderFactory()
        provider = factory.create_provider()
    """

    PROVIDER_TYPES = {
        'opencode': OpenCodeProvider,
    }

    def __init__(self):
        """Set up the logger."""
        super().__init__()

    def create_provider(self) -> BaseLLMProvider:
        """
        Create and return the LLM provider.

        Returns:
            BaseLLMProvider: an instance of the configured provider.

        Raises:
            Exception: if the provider cannot be initialised (missing key or
                model), with the original reason in the message.

        Example:
            >>> factory = ProviderFactory()
            >>> provider = factory.create_provider()
            >>> result = provider.series_extract("Olimpiadas", "1992", "cleaned_data")
        """
        provider_type = 'opencode'
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
        Get the names of the providers this factory can build.

        Returns:
            list: provider names, currently `['opencode']`.
        """
        return list(cls.PROVIDER_TYPES.keys())

    @classmethod
    def is_provider_available(cls, provider_type: str) -> bool:
        """
        Check whether a provider name is known.

        Args:
            provider_type (str): name to check, case-insensitive.

        Returns:
            bool: True when the factory can build it.
        """
        return provider_type.lower() in cls.PROVIDER_TYPES
