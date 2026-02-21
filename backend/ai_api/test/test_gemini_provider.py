"""
Tests for GeminiProvider.

This module tests the Google Gemini LLM provider implementation, including
initialization, series extraction, and batch processing logic.
"""
import pytest
import json
from unittest.mock import Mock, patch, MagicMock

from ai_api.services.gemini_provider import GeminiProvider
from common.api.messages import Messages


class TestGeminiProviderInit:
    """Test GeminiProvider initialization."""
    
    def test_init_success(self, mocker):
        """Test successful initialization of GeminiProvider."""
        # Mock settings
        mocker.patch('ai_api.services.gemini_provider.GEMINI_API_KEY', 'test-api-key')
        mocker.patch('ai_api.services.gemini_provider.GEMINI_MODEL_NAME', 'test-model')
        
        # Mock genai.Client
        mock_client = Mock()
        mocker.patch('ai_api.services.gemini_provider.genai.Client', return_value=mock_client)
        
        provider = GeminiProvider()
        
        assert provider.client is not None
        assert provider.prompt_template is not None
        assert provider.header_prompt_template is not None
        assert provider.batch_prompt_template is not None
    
    def test_init_missing_api_key_raises_error(self, mocker):
        """Test that missing API key raises ValueError."""
        mocker.patch('ai_api.services.gemini_provider.GEMINI_API_KEY', None)
        mocker.patch('ai_api.services.gemini_provider.GEMINI_MODEL_NAME', 'test-model')
        
        with pytest.raises(ValueError, match=Messages.AI.missing_api_key()):
            GeminiProvider()
    
    def test_init_missing_model_name_raises_error(self, mocker):
        """Test that missing model name raises ValueError."""
        mocker.patch('ai_api.services.gemini_provider.GEMINI_API_KEY', 'test-api-key')
        mocker.patch('ai_api.services.gemini_provider.GEMINI_MODEL_NAME', None)
        
        with pytest.raises(ValueError, match=Messages.AI.missing_model_name()):
            GeminiProvider()


class TestGeminiSeriesExtract:
    """Test series_extract method."""
    
    def test_series_extract_empty_data_raises_error(self, mocker):
        """Test that empty clean_data raises ValueError."""
        mocker.patch('ai_api.services.gemini_provider.GEMINI_API_KEY', 'test-api-key')
        mocker.patch('ai_api.services.gemini_provider.GEMINI_MODEL_NAME', 'test-model')
        mock_client = Mock()
        mocker.patch('ai_api.services.gemini_provider.genai.Client', return_value=mock_client)
        
        provider = GeminiProvider()
        
        with pytest.raises(ValueError, match=Messages.AI.missing_input_data()):
            provider.series_extract("Test Series", "1992", "")
    
    def test_series_extract_whitespace_data_raises_error(self, mocker):
        """Test that whitespace-only clean_data raises ValueError."""
        mocker.patch('ai_api.services.gemini_provider.GEMINI_API_KEY', 'test-api-key')
        mocker.patch('ai_api.services.gemini_provider.GEMINI_MODEL_NAME', 'test-model')
        mock_client = Mock()
        mocker.patch('ai_api.services.gemini_provider.genai.Client', return_value=mock_client)
        
        provider = GeminiProvider()
        
        with pytest.raises(ValueError, match=Messages.AI.missing_input_data()):
            provider.series_extract("Test Series", "1992", "   ")
    
    def test_series_extract_single_extraction(self, mocker):
        """Test single extraction for small series."""
        mocker.patch('ai_api.services.gemini_provider.GEMINI_API_KEY', 'test-api-key')
        mocker.patch('ai_api.services.gemini_provider.GEMINI_MODEL_NAME', 'test-model')
        
        # Mock LLM_BATCH_SIZE to be high (no batching)
        mocker.patch('ai_api.services.base_llm_provider.LLM_BATCH_SIZE', 1000)
        
        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = json.dumps({
            "issue_name": "Test Series",
            "description": "Test description",
            "stamps": []
        })
        mock_client.models.generate_content.return_value = mock_response
        mocker.patch('ai_api.services.gemini_provider.genai.Client', return_value=mock_client)
        
        provider = GeminiProvider()
        
        clean_data = json.dumps({"serie_info": {"name": "Test"}, "stamps": []})
        result = provider.series_extract("Test Series", "1992", clean_data)
        
        assert result["issue_name"] == "Test Series"
        mock_client.models.generate_content.assert_called_once()
    
    def test_series_extract_service_error(self, mocker):
        """Test that API error is properly handled."""
        mocker.patch('ai_api.services.gemini_provider.GEMINI_API_KEY', 'test-api-key')
        mocker.patch('ai_api.services.gemini_provider.GEMINI_MODEL_NAME', 'test-model')
        mocker.patch('ai_api.services.base_llm_provider.LLM_BATCH_SIZE', 1000)
        
        mock_client = Mock()
        mock_client.models.generate_content.side_effect = Exception("API Error")
        mocker.patch('ai_api.services.gemini_provider.genai.Client', return_value=mock_client)
        
        provider = GeminiProvider()
        
        clean_data = json.dumps({"serie_info": {"name": "Test"}, "stamps": []})
        
        with pytest.raises(Exception, match="Extraction service error"):
            provider.series_extract("Test Series", "1992", clean_data)


class TestGeminiSingleExtract:
    """Test _single_extract method."""
    
    def test_single_extract_success(self, mocker):
        """Test successful single extraction."""
        mocker.patch('ai_api.services.gemini_provider.GEMINI_API_KEY', 'test-api-key')
        mocker.patch('ai_api.services.gemini_provider.GEMINI_MODEL_NAME', 'test-model')
        
        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = json.dumps({
            "issue_name": "Test Series",
            "stamps": [{"edifil_code": "1234"}]
        })
        mock_client.models.generate_content.return_value = mock_response
        mocker.patch('ai_api.services.gemini_provider.genai.Client', return_value=mock_client)
        
        provider = GeminiProvider()
        clean_data = json.dumps({"serie_info": {}, "stamps": []})
        
        result = provider._single_extract(clean_data)
        
        assert "issue_name" in result
        mock_client.models.generate_content.assert_called_once()
    
    def test_single_extract_empty_response_raises_error(self, mocker):
        """Test that empty response raises ValueError."""
        mocker.patch('ai_api.services.gemini_provider.GEMINI_API_KEY', 'test-api-key')
        mocker.patch('ai_api.services.gemini_provider.GEMINI_MODEL_NAME', 'test-model')
        
        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = None
        mock_client.models.generate_content.return_value = mock_response
        mocker.patch('ai_api.services.gemini_provider.genai.Client', return_value=mock_client)
        
        provider = GeminiProvider()
        clean_data = json.dumps({"serie_info": {}, "stamps": []})
        
        with pytest.raises(ValueError, match=Messages.AI.empty_response()):
            provider._single_extract(clean_data)


class TestGeminiBatchExtract:
    """Test batch extraction methods."""
    
    def test_batch_extract_triggers_for_large_series(self, mocker):
        """Test that batch processing is triggered for large series."""
        mocker.patch('ai_api.services.gemini_provider.GEMINI_API_KEY', 'test-api-key')
        mocker.patch('ai_api.services.gemini_provider.GEMINI_MODEL_NAME', 'test-model')
        
        # Set low batch size to trigger batching
        mocker.patch('ai_api.services.base_llm_provider.LLM_BATCH_SIZE', 2)
        
        mock_client = Mock()
        
        # Mock header response
        header_response = Mock()
        header_response.text = json.dumps({
            "issue_name": "Test Series",
            "description": "Test"
        })
        
        # Mock batch responses
        batch_response_1 = Mock()
        batch_response_1.text = json.dumps({
            "stamps": [{"edifil_code": "1"}, {"edifil_code": "2"}]
        })
        batch_response_2 = Mock()
        batch_response_2.text = json.dumps({
            "stamps": [{"edifil_code": "3"}]
        })
        
        mock_client.models.generate_content.side_effect = [
            header_response, batch_response_1, batch_response_2
        ]
        mocker.patch('ai_api.services.gemini_provider.genai.Client', return_value=mock_client)
        
        provider = GeminiProvider()
        
        # Create data with 3 stamps (exceeds batch size of 2)
        clean_data = json.dumps({
            "serie_info": {"name": "Test"},
            "stamps": [{"id": 1}, {"id": 2}, {"id": 3}]
        })
        
        result = provider.series_extract("Test Series", "1992", clean_data)
        
        # Should have called generate_content 3 times (1 header + 2 batches)
        assert mock_client.models.generate_content.call_count == 3
        assert len(result["stamps"]) == 3


class TestGeminiExtractHeader:
    """Test _extract_header method."""
    
    def test_extract_header_success(self, mocker):
        """Test successful header extraction."""
        mocker.patch('ai_api.services.gemini_provider.GEMINI_API_KEY', 'test-api-key')
        mocker.patch('ai_api.services.gemini_provider.GEMINI_MODEL_NAME', 'test-model')
        
        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = json.dumps({
            "issue_name": "Test Series",
            "description": "Test description",
            "issue_date": "1992-01-01"
        })
        mock_client.models.generate_content.return_value = mock_response
        mocker.patch('ai_api.services.gemini_provider.genai.Client', return_value=mock_client)
        
        provider = GeminiProvider()
        serie_info = {"name": "Test Series", "year": "1992"}
        
        result = provider._extract_header(serie_info)
        
        assert result["issue_name"] == "Test Series"
        mock_client.models.generate_content.assert_called_once()


class TestGeminiExtractBatch:
    """Test _extract_batch method."""
    
    def test_extract_batch_success(self, mocker):
        """Test successful batch extraction."""
        mocker.patch('ai_api.services.gemini_provider.GEMINI_API_KEY', 'test-api-key')
        mocker.patch('ai_api.services.gemini_provider.GEMINI_MODEL_NAME', 'test-model')
        
        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = json.dumps({
            "stamps": [
                {"edifil_code": "1234", "motive": "Test"},
                {"edifil_code": "1235", "motive": "Test 2"}
            ]
        })
        mock_client.models.generate_content.return_value = mock_response
        mocker.patch('ai_api.services.gemini_provider.genai.Client', return_value=mock_client)
        
        provider = GeminiProvider()
        serie_info = {"name": "Test Series"}
        stamp_batch = [{"id": 1}, {"id": 2}]
        
        result = provider._extract_batch(serie_info, stamp_batch, 1, 2)
        
        assert len(result["stamps"]) == 2
        mock_client.models.generate_content.assert_called_once()
