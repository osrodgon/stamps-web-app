"""
Tests for ProviderFactory.

This module tests the factory pattern implementation for creating LLM providers.
Tests verify proper provider selection based on environment configuration,
error handling for unsupported providers, and utility methods.
"""
import pytest
from unittest.mock import Mock, patch

from ai_api.services.provider_factory import ProviderFactory
from ai_api.services.base_llm_provider import BaseLLMProvider
from ai_api.services.gemini_provider import GeminiProvider
from ai_api.services.groq_provider import GroqProvider


class TestProviderFactory:
    """Test class for ProviderFactory."""
    
    def test_init(self):
        """Test ProviderFactory initialization."""
        factory = ProviderFactory()
        assert factory is not None
    
    def test_create_gemini_provider(self, mocker):
        """Test creating Gemini provider when LLM_PROVIDER is set to gemini."""
        # Mock environment and settings
        mocker.patch.dict('os.environ', {'LLM_PROVIDER': 'gemini'})
        mocker.patch('ai_api.services.gemini_provider.GEMINI_API_KEY', 'test-api-key')
        mocker.patch('ai_api.services.gemini_provider.GEMINI_MODEL_NAME', 'test-model')
        
        # Mock the genai.Client to avoid actual API calls
        mock_client = Mock()
        mocker.patch('ai_api.services.gemini_provider.genai.Client', return_value=mock_client)
        
        factory = ProviderFactory()
        provider = factory.create_provider()
        
        assert isinstance(provider, GeminiProvider)
    
    def test_create_groq_provider(self, mocker):
        """Test creating Groq provider when LLM_PROVIDER is set to groq."""
        # Mock environment
        mocker.patch.dict('os.environ', {
            'LLM_PROVIDER': 'groq',
            'GROQ_API_KEY': 'test-api-key',
            'GROQ_MODEL_NAME': 'test-model'
        })
        
        # Mock the Groq client to avoid actual API calls
        mock_client = Mock()
        mocker.patch('ai_api.services.groq_provider.Groq', return_value=mock_client)
        
        factory = ProviderFactory()
        provider = factory.create_provider()
        
        assert isinstance(provider, GroqProvider)
    
    def test_default_provider_is_gemini(self, mocker):
        """Test that Gemini is the default provider when LLM_PROVIDER is not set."""
        # Mock environment without LLM_PROVIDER
        mocker.patch.dict('os.environ', {}, clear=True)
        mocker.patch('ai_api.services.gemini_provider.GEMINI_API_KEY', 'test-api-key')
        mocker.patch('ai_api.services.gemini_provider.GEMINI_MODEL_NAME', 'test-model')
        
        # Mock the genai.Client
        mock_client = Mock()
        mocker.patch('ai_api.services.gemini_provider.genai.Client', return_value=mock_client)
        
        factory = ProviderFactory()
        provider = factory.create_provider()
        
        assert isinstance(provider, GeminiProvider)
    
    def test_unsupported_provider_raises_error(self, mocker):
        """Test that unsupported provider type raises ValueError."""
        mocker.patch.dict('os.environ', {'LLM_PROVIDER': 'unsupported'})
        
        factory = ProviderFactory()
        
        with pytest.raises(ValueError, match="Unsupported LLM provider type"):
            factory.create_provider()
    
    def test_provider_initialization_failure_raises_error(self, mocker):
        """Test that provider initialization failure raises Exception."""
        mocker.patch.dict('os.environ', {'LLM_PROVIDER': 'gemini'})
        mocker.patch('ai_api.services.gemini_provider.GEMINI_API_KEY', None)
        
        factory = ProviderFactory()
        
        with pytest.raises(Exception, match="Provider initialization failed"):
            factory.create_provider()
    
    def test_get_available_providers(self):
        """Test getting list of available provider types."""
        providers = ProviderFactory.get_available_providers()
        
        assert 'gemini' in providers
        assert 'groq' in providers
        assert len(providers) == 2
    
    def test_is_provider_available_gemini(self):
        """Test checking if Gemini provider is available."""
        assert ProviderFactory.is_provider_available('gemini') is True
        assert ProviderFactory.is_provider_available('GEMINI') is True  # Case insensitive
        assert ProviderFactory.is_provider_available('Gemini') is True
    
    def test_is_provider_available_groq(self):
        """Test checking if Groq provider is available."""
        assert ProviderFactory.is_provider_available('groq') is True
        assert ProviderFactory.is_provider_available('GROQ') is True  # Case insensitive
    
    def test_is_provider_available_unsupported(self):
        """Test checking if unsupported provider is available."""
        assert ProviderFactory.is_provider_available('openai') is False
        assert ProviderFactory.is_provider_available('anthropic') is False
        assert ProviderFactory.is_provider_available('') is False
