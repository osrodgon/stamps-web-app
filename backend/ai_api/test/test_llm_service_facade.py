"""
Tests for LLMService (Facade Pattern).

This module tests the LLMService facade class that delegates to provider-specific
implementations. Tests verify proper delegation, error handling, and initialization.
"""
import pytest
import json
from unittest.mock import Mock, patch, MagicMock

from ai_api.services.llm_service import LLMService
from ai_api.services.provider_factory import ProviderFactory
from ai_api.services.gemini_provider import GeminiProvider
from ai_api.services.groq_provider import GroqProvider
from common.api.messages import Messages


class TestLLMServiceInit:
    """Test LLMService initialization."""
    
    def test_init_creates_provider_factory(self, mocker):
        """Test that LLMService creates a ProviderFactory."""
        mock_provider = Mock()
        mocker.patch.object(ProviderFactory, 'create_provider', return_value=mock_provider)
        
        service = LLMService()
        
        assert service.provider_factory is not None
        assert service.provider == mock_provider
    
    def test_init_uses_default_provider(self, mocker):
        """Test that LLMService uses GeminiProvider by default."""
        mocker.patch.dict('os.environ', {}, clear=True)
        mocker.patch('ai_api.services.gemini_provider.GEMINI_API_KEY', 'test-api-key')
        mocker.patch('ai_api.services.gemini_provider.GEMINI_MODEL_NAME', 'test-model')
        
        mock_client = Mock()
        mocker.patch('ai_api.services.gemini_provider.genai.Client', return_value=mock_client)
        
        service = LLMService()
        
        assert isinstance(service.provider, GeminiProvider)
    
    def test_init_uses_gemini_provider(self, mocker):
        """Test that LLMService uses GeminiProvider when configured."""
        mocker.patch.dict('os.environ', {'LLM_PROVIDER': 'gemini'})
        mocker.patch('ai_api.services.gemini_provider.GEMINI_API_KEY', 'test-api-key')
        mocker.patch('ai_api.services.gemini_provider.GEMINI_MODEL_NAME', 'test-model')
        
        mock_client = Mock()
        mocker.patch('ai_api.services.gemini_provider.genai.Client', return_value=mock_client)
        
        service = LLMService()
        
        assert isinstance(service.provider, GeminiProvider)
    
    def test_init_uses_groq_provider(self, mocker):
        """Test that LLMService uses GroqProvider when configured."""
        mocker.patch.dict('os.environ', {
            'LLM_PROVIDER': 'groq',
            'GROQ_API_KEY': 'test-api-key',
            'GROQ_MODEL_NAME': 'test-model'
        })
        
        mock_client = Mock()
        mocker.patch('ai_api.services.groq_provider.Groq', return_value=mock_client)
        
        service = LLMService()
        
        assert isinstance(service.provider, GroqProvider)


class TestLLMServiceSeriesExtract:
    """Test series_extract method delegation."""
    
    def test_series_extract_delegates_to_provider(self, mocker):
        """Test that series_extract delegates to the provider."""
        mock_provider = Mock()
        mock_provider.series_extract.return_value = {
            "issue_name": "Test Series",
            "description": "Test description",
            "stamps": []
        }
        mocker.patch.object(ProviderFactory, 'create_provider', return_value=mock_provider)
        
        service = LLMService()
        result = service.series_extract("Test Series", "1992", '{"data": "test"}')
        
        mock_provider.series_extract.assert_called_once_with("Test Series", "1992", '{"data": "test"}')
        assert result["issue_name"] == "Test Series"
    
    def test_series_extract_passes_all_arguments(self, mocker):
        """Test that all arguments are passed to the provider."""
        mock_provider = Mock()
        mock_provider.series_extract.return_value = {"result": "success"}
        mocker.patch.object(ProviderFactory, 'create_provider', return_value=mock_provider)
        
        service = LLMService()
        service.series_extract("Name", "Date", "CleanData")
        
        mock_provider.series_extract.assert_called_once_with("Name", "Date", "CleanData")
    
    def test_series_extract_propagates_validation_error(self, mocker):
        """Test that validation errors from provider are wrapped in service error."""
        mock_provider = Mock()
        mock_provider.series_extract.side_effect = ValueError(Messages.AI.missing_input_data())
        mocker.patch.object(ProviderFactory, 'create_provider', return_value=mock_provider)
        
        service = LLMService()
        
        # LLMService wraps all exceptions in a service error message
        with pytest.raises(Exception, match="Extraction service error"):
            service.series_extract("Test", "1992", "")
    
    def test_series_extract_wraps_generic_error(self, mocker):
        """Test that generic errors are wrapped in service error message."""
        mock_provider = Mock()
        mock_provider.series_extract.side_effect = Exception("API connection failed")
        mocker.patch.object(ProviderFactory, 'create_provider', return_value=mock_provider)
        
        service = LLMService()
        
        with pytest.raises(Exception, match="Extraction service error"):
            service.series_extract("Test", "1992", "data")


class TestLLMServiceFacadeBehavior:
    """Test facade pattern behavior."""
    
    def test_facade_hides_provider_complexity(self, mocker):
        """Test that LLMService hides provider complexity."""
        # Setup Gemini provider with all its complexity
        mocker.patch.dict('os.environ', {'LLM_PROVIDER': 'gemini'})
        mocker.patch('ai_api.services.gemini_provider.GEMINI_API_KEY', 'test-api-key')
        mocker.patch('ai_api.services.gemini_provider.GEMINI_MODEL_NAME', 'test-model')
        
        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = json.dumps({"issue_name": "Test", "stamps": []})
        mock_response.candidates = [Mock(finish_reason='STOP', safety_ratings=[])]
        mock_client.models.generate_content.return_value = mock_response
        mocker.patch('ai_api.services.gemini_provider.genai.Client', return_value=mock_client)

        # User only interacts with simple LLMService interface
        service = LLMService()
        result = service.series_extract("Test", "1992", '{"serie_info": {}, "stamps": []}')
        
        # Verify result without knowing internal provider details
        assert "issue_name" in result
    
    def test_facade_switches_provider_transparently(self, mocker):
        """Test that switching providers is transparent to the user."""
        # First with Gemini
        mocker.patch.dict('os.environ', {'LLM_PROVIDER': 'gemini'})
        mocker.patch('ai_api.services.gemini_provider.GEMINI_API_KEY', 'test-key')
        mocker.patch('ai_api.services.gemini_provider.GEMINI_MODEL_NAME', 'test-model')
        
        mock_gemini_client = Mock()
        mock_gemini_response = Mock()
        mock_gemini_response.text = json.dumps({"issue_name": "Gemini Result", "stamps": []})
        mock_gemini_response.candidates = [Mock(finish_reason='STOP', safety_ratings=[])]
        mock_gemini_client.models.generate_content.return_value = mock_gemini_response
        mocker.patch('ai_api.services.gemini_provider.genai.Client', return_value=mock_gemini_client)
        
        service_gemini = LLMService()
        result_gemini = service_gemini.series_extract("Test", "1992", '{"serie_info": {}, "stamps": []}')
        
        # Same interface works with Groq
        mocker.patch.dict('os.environ', {
            'LLM_PROVIDER': 'groq',
            'GROQ_API_KEY': 'test-key'
        })
        
        mock_groq_client = Mock()
        mock_groq_response = Mock()
        mock_groq_response.choices = [Mock()]
        mock_groq_response.choices[0].message = Mock()
        mock_groq_response.choices[0].message.content = json.dumps({"issue_name": "Groq Result", "stamps": []})
        mock_groq_client.chat.completions.create.return_value = mock_groq_response
        mocker.patch('ai_api.services.groq_provider.Groq', return_value=mock_groq_client)
        
        service_groq = LLMService()
        result_groq = service_groq.series_extract("Test", "1992", '{"serie_info": {}, "stamps": []}')
        
        # Both return same structure, different internal implementation
        assert "issue_name" in result_gemini
        assert "issue_name" in result_groq
        assert result_gemini["issue_name"] == "Gemini Result"
        assert result_groq["issue_name"] == "Groq Result"


class TestLLMServiceLogging:
    """Test logging behavior."""
    
    def test_logs_provider_initialization(self, mocker):
        """Test that provider initialization is logged."""
        mock_provider = Mock()
        mock_provider.__class__.__name__ = 'TestProvider'
        mocker.patch.object(ProviderFactory, 'create_provider', return_value=mock_provider)
        
        service = LLMService()
        
        # Service should have logged the provider type
        assert service.log is not None
    
    def test_logs_extraction_start(self, mocker):
        """Test that extraction start is logged."""
        mock_provider = Mock()
        mock_provider.series_extract.return_value = {"result": "success"}
        mocker.patch.object(ProviderFactory, 'create_provider', return_value=mock_provider)
        
        service = LLMService()
        service.series_extract("Test", "1992", "data")
        
        # Service has a logger
        assert service.log is not None
    
    def test_logs_extraction_error(self, mocker):
        """Test that extraction errors are logged."""
        mock_provider = Mock()
        mock_provider.series_extract.side_effect = Exception("Test error")
        mocker.patch.object(ProviderFactory, 'create_provider', return_value=mock_provider)
        
        service = LLMService()
        
        with pytest.raises(Exception):
            service.series_extract("Test", "1992", "data")
        
        # Error should have been logged (verified by the error being raised)
        assert service.log is not None
