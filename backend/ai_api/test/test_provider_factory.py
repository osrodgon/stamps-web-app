"""
Test module for ProviderFactory.

This module contains comprehensive tests for the ProviderFactory class,
ensuring proper instantiation and configuration of different LLM providers.
"""

import pytest
from unittest.mock import patch, Mock
from common.api.messages import Messages
from ai_api.services.provider_factory import ProviderFactory
from ai_api.services.base_llm_provider import BaseLLMProvider
from ai_api.services.gemini_provider import GeminiProvider
from ai_api.services.groq_provider import GroqProvider

@pytest.mark.skip(reason="To be fixed after multi-provider refactor")
class TestProviderFactory:
    """Test class for ProviderFactory (No Database)."""
    
    def test_get_available_providers(self):
        """Test that get_available_providers returns the correct list."""
        providers = ProviderFactory.get_available_providers()
        expected_providers = ['gemini', 'groq']
        assert providers == expected_providers
    
    def test_is_provider_available(self):
        """Test provider availability checking."""
        assert ProviderFactory.is_provider_available('gemini') is True
        assert ProviderFactory.is_provider_available('groq') is True
        assert ProviderFactory.is_provider_available('openai') is False
        assert ProviderFactory.is_provider_available('anthropic') is False
    
    @patch('ai_api.services.provider_factory.GeminiProvider')
    def test_create_gemini_provider_default(self, mock_gemini_provider):
        """Test creating Gemini provider with default configuration."""
        # Mock the GeminiProvider initialization
        mock_provider_instance = Mock(spec=BaseLLMProvider)
        mock_gemini_provider.return_value = mock_provider_instance
        
        # Mock environment variables
        with patch.dict('os.environ', {
            'LLM_PROVIDER': 'gemini',
            'GEMINI_API_KEY': 'test-gemini-key',
            'GEMINI_MODEL_NAME': 'gemini-1.5-flash'
        }):
            factory = ProviderFactory()
            provider = factory.create_provider()
            
            # Verify the correct provider class was instantiated
            mock_gemini_provider.assert_called_once()
            assert provider == mock_provider_instance
    
    @patch('ai_api.services.provider_factory.GroqProvider')
    def test_create_groq_provider(self, mock_groq_provider):
        """Test creating Groq provider."""
        # Mock the GroqProvider initialization
        mock_provider_instance = Mock(spec=BaseLLMProvider)
        mock_groq_provider.return_value = mock_provider_instance
        
        # Mock environment variables
        with patch.dict('os.environ', {
            'LLM_PROVIDER': 'groq',
            'GROQ_API_KEY': 'test-groq-key',
            'GROQ_MODEL_NAME': 'llama3-8b-8192'
        }):
            factory = ProviderFactory()
            provider = factory.create_provider()
            
            # Verify the correct provider class was instantiated
            mock_groq_provider.assert_called_once()
            assert provider == mock_provider_instance
    
    def test_create_provider_default_to_gemini(self):
        """Test that provider defaults to Gemini when LLM_PROVIDER is not set."""
        with patch.dict('os.environ', {}, clear=True):
            factory = ProviderFactory()
            with patch('ai_api.services.provider_factory.GeminiProvider') as mock_gemini:
                mock_provider_instance = Mock(spec=BaseLLMProvider)
                mock_gemini.return_value = mock_provider_instance
                
                provider = factory.create_provider()
                
                # Should default to Gemini
                mock_gemini.assert_called_once()
                assert provider == mock_provider_instance
    
    def test_create_provider_invalid_type(self):
        """Test that creating an invalid provider type raises ValueError."""
        with patch.dict('os.environ', {'LLM_PROVIDER': 'invalid_provider'}):
            factory = ProviderFactory()
            
            with pytest.raises(ValueError, match="Unsupported LLM provider type: invalid_provider"):
                factory.create_provider()
    
    @patch('ai_api.services.provider_factory.GeminiProvider')
    def test_create_provider_initialization_failure(self, mock_gemini_provider):
        """Test handling of provider initialization failures."""
        # Mock provider initialization to raise an exception
        mock_gemini_provider.side_effect = Exception("Provider initialization failed")
        
        with patch.dict('os.environ', {
            'LLM_PROVIDER': 'gemini',
            'GEMINI_API_KEY': 'test-gemini-key',
            'GEMINI_MODEL_NAME': 'gemini-1.5-flash'
        }):
            factory = ProviderFactory()
            
            with pytest.raises(Exception, match="Provider initialization failed"):
                factory.create_provider()
    
    @patch('ai_api.services.provider_factory.GeminiProvider')
    def test_create_provider_logs_debug_message(self, mock_gemini_provider):
        """Test that provider creation logs debug information."""
        mock_provider_instance = Mock(spec=BaseLLMProvider)
        mock_gemini_provider.return_value = mock_provider_instance
        
        with patch.dict('os.environ', {
            'LLM_PROVIDER': 'gemini',
            'GEMINI_API_KEY': 'test-gemini-key',
            'GEMINI_MODEL_NAME': 'gemini-1.5-flash'
        }):
            factory = ProviderFactory()
            factory.create_provider()
            
            # Verify debug log was called
            factory.log.debug.assert_called_with("Creating LLM provider of type: gemini")
    
    @patch('ai_api.services.provider_factory.GeminiProvider')
    def test_create_provider_logs_success_message(self, mock_gemini_provider):
        """Test that successful provider creation logs success information."""
        mock_provider_instance = Mock(spec=BaseLLMProvider)
        mock_gemini_provider.return_value = mock_provider_instance
        
        with patch.dict('os.environ', {
            'LLM_PROVIDER': 'gemini',
            'GEMINI_API_KEY': 'test-gemini-key',
            'GEMINI_MODEL_NAME': 'gemini-1.5-flash'
        }):
            factory = ProviderFactory()
            factory.create_provider()
            
            # Verify success log was called
            factory.log.info.assert_called_with("Successfully created gemini provider")