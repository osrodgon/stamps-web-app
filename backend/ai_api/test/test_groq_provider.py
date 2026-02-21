"""
Tests for GroqProvider.

This module tests the Groq LLM provider implementation, including
initialization, series extraction, and batch processing logic.
"""
import pytest
import json
from unittest.mock import Mock, patch, MagicMock

from ai_api.services.groq_provider import GroqProvider
from common.api.messages import Messages


class TestGroqProviderInit:
    """Test GroqProvider initialization."""
    
    def test_init_success(self, mocker):
        """Test successful initialization of GroqProvider."""
        # Mock environment
        mocker.patch.dict('os.environ', {
            'GROQ_API_KEY': 'test-api-key',
            'GROQ_MODEL_NAME': 'test-model'
        })
        
        # Mock Groq client
        mock_client = Mock()
        mocker.patch('ai_api.services.groq_provider.Groq', return_value=mock_client)
        
        provider = GroqProvider()
        
        assert provider.client is not None
        assert provider.model_name == 'test-model'
        assert provider.prompt_template is not None
        assert provider.header_prompt_template is not None
        assert provider.batch_prompt_template is not None
    
    def test_init_missing_api_key_raises_error(self, mocker):
        """Test that missing API key raises ValueError."""
        mocker.patch.dict('os.environ', {'GROQ_API_KEY': ''})
        mocker.patch.dict('os.environ', {'GROQ_MODEL_NAME': 'test-model'})
        
        with pytest.raises(ValueError, match=Messages.AI.missing_api_key()):
            GroqProvider()
    
    def test_init_default_model_name(self, mocker):
        """Test that default model name is used when not specified."""
        # Set API key but not GROQ_MODEL_NAME - it should use default
        mocker.patch.dict('os.environ', {'GROQ_API_KEY': 'test-api-key'}, clear=True)
        
        mock_client = Mock()
        mocker.patch('ai_api.services.groq_provider.Groq', return_value=mock_client)
        
        provider = GroqProvider()
        
        # Default model name should be used when GROQ_MODEL_NAME is not set
        assert provider.model_name == 'llama3-8b-8192'


class TestGroqSeriesExtract:
    """Test series_extract method."""
    
    def test_series_extract_empty_data_raises_error(self, mocker):
        """Test that empty clean_data raises ValueError."""
        mocker.patch.dict('os.environ', {'GROQ_API_KEY': 'test-api-key'})
        mock_client = Mock()
        mocker.patch('ai_api.services.groq_provider.Groq', return_value=mock_client)
        
        provider = GroqProvider()
        
        with pytest.raises(ValueError, match=Messages.AI.missing_input_data()):
            provider.series_extract("Test Series", "1992", "")
    
    def test_series_extract_whitespace_data_raises_error(self, mocker):
        """Test that whitespace-only clean_data raises ValueError."""
        mocker.patch.dict('os.environ', {'GROQ_API_KEY': 'test-api-key'})
        mock_client = Mock()
        mocker.patch('ai_api.services.groq_provider.Groq', return_value=mock_client)
        
        provider = GroqProvider()
        
        with pytest.raises(ValueError, match=Messages.AI.missing_input_data()):
            provider.series_extract("Test Series", "1992", "   ")
    
    def test_series_extract_single_extraction(self, mocker):
        """Test single extraction for small series."""
        mocker.patch.dict('os.environ', {'GROQ_API_KEY': 'test-api-key'})
        mocker.patch('ai_api.services.base_llm_provider.LLM_BATCH_SIZE', 1000)
        
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = json.dumps({
            "issue_name": "Test Series",
            "description": "Test description",
            "stamps": []
        })
        mock_client.chat.completions.create.return_value = mock_response
        mocker.patch('ai_api.services.groq_provider.Groq', return_value=mock_client)
        
        provider = GroqProvider()
        
        clean_data = json.dumps({"serie_info": {"name": "Test"}, "stamps": []})
        result = provider.series_extract("Test Series", "1992", clean_data)
        
        assert result["issue_name"] == "Test Series"
        mock_client.chat.completions.create.assert_called_once()
    
    def test_series_extract_service_error(self, mocker):
        """Test that API error is properly handled."""
        mocker.patch.dict('os.environ', {'GROQ_API_KEY': 'test-api-key'})
        mocker.patch('ai_api.services.base_llm_provider.LLM_BATCH_SIZE', 1000)
        
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        mocker.patch('ai_api.services.groq_provider.Groq', return_value=mock_client)
        
        provider = GroqProvider()
        
        clean_data = json.dumps({"serie_info": {"name": "Test"}, "stamps": []})
        
        with pytest.raises(Exception, match="Extraction service error"):
            provider.series_extract("Test Series", "1992", clean_data)


class TestGroqSingleExtract:
    """Test _single_extract method."""
    
    def test_single_extract_success(self, mocker):
        """Test successful single extraction."""
        mocker.patch.dict('os.environ', {'GROQ_API_KEY': 'test-api-key'})
        
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = json.dumps({
            "issue_name": "Test Series",
            "stamps": [{"edifil_code": "1234"}]
        })
        mock_client.chat.completions.create.return_value = mock_response
        mocker.patch('ai_api.services.groq_provider.Groq', return_value=mock_client)
        
        provider = GroqProvider()
        clean_data = json.dumps({"serie_info": {}, "stamps": []})
        
        result = provider._single_extract(clean_data)
        
        assert "issue_name" in result
        mock_client.chat.completions.create.assert_called_once()
    
    def test_single_extract_empty_response_raises_error(self, mocker):
        """Test that empty response raises ValueError."""
        mocker.patch.dict('os.environ', {'GROQ_API_KEY': 'test-api-key'})
        
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = []
        mock_client.chat.completions.create.return_value = mock_response
        mocker.patch('ai_api.services.groq_provider.Groq', return_value=mock_client)
        
        provider = GroqProvider()
        clean_data = json.dumps({"serie_info": {}, "stamps": []})
        
        with pytest.raises(ValueError, match=Messages.AI.empty_response()):
            provider._single_extract(clean_data)


class TestGroqBatchExtract:
    """Test batch extraction methods."""
    
    def test_batch_extract_triggers_for_large_series(self, mocker):
        """Test that batch processing is triggered for large series."""
        mocker.patch.dict('os.environ', {'GROQ_API_KEY': 'test-api-key'})
        mocker.patch('ai_api.services.base_llm_provider.LLM_BATCH_SIZE', 2)
        
        mock_client = Mock()
        
        # Mock header response
        header_response = Mock()
        header_response.choices = [Mock()]
        header_response.choices[0].message = Mock()
        header_response.choices[0].message.content = json.dumps({
            "issue_name": "Test Series",
            "description": "Test"
        })
        
        # Mock batch responses
        batch_response_1 = Mock()
        batch_response_1.choices = [Mock()]
        batch_response_1.choices[0].message = Mock()
        batch_response_1.choices[0].message.content = json.dumps({
            "stamps": [{"edifil_code": "1"}, {"edifil_code": "2"}]
        })
        batch_response_2 = Mock()
        batch_response_2.choices = [Mock()]
        batch_response_2.choices[0].message = Mock()
        batch_response_2.choices[0].message.content = json.dumps({
            "stamps": [{"edifil_code": "3"}]
        })
        
        mock_client.chat.completions.create.side_effect = [
            header_response, batch_response_1, batch_response_2
        ]
        mocker.patch('ai_api.services.groq_provider.Groq', return_value=mock_client)
        
        provider = GroqProvider()
        
        # Create data with 3 stamps (exceeds batch size of 2)
        clean_data = json.dumps({
            "serie_info": {"name": "Test"},
            "stamps": [{"id": 1}, {"id": 2}, {"id": 3}]
        })
        
        result = provider.series_extract("Test Series", "1992", clean_data)
        
        # Should have called create 3 times (1 header + 2 batches)
        assert mock_client.chat.completions.create.call_count == 3
        assert len(result["stamps"]) == 3


class TestGroqExtractHeader:
    """Test _extract_header method."""
    
    def test_extract_header_success(self, mocker):
        """Test successful header extraction."""
        mocker.patch.dict('os.environ', {'GROQ_API_KEY': 'test-api-key'})
        
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = json.dumps({
            "issue_name": "Test Series",
            "description": "Test description",
            "issue_date": "1992-01-01"
        })
        mock_client.chat.completions.create.return_value = mock_response
        mocker.patch('ai_api.services.groq_provider.Groq', return_value=mock_client)
        
        provider = GroqProvider()
        serie_info = {"name": "Test Series", "year": "1992"}
        
        result = provider._extract_header(serie_info)
        
        assert result["issue_name"] == "Test Series"
        mock_client.chat.completions.create.assert_called_once()


class TestGroqExtractBatch:
    """Test _extract_batch method."""
    
    def test_extract_batch_success(self, mocker):
        """Test successful batch extraction."""
        mocker.patch.dict('os.environ', {'GROQ_API_KEY': 'test-api-key'})
        
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = json.dumps({
            "stamps": [
                {"edifil_code": "1234", "motive": "Test"},
                {"edifil_code": "1235", "motive": "Test 2"}
            ]
        })
        mock_client.chat.completions.create.return_value = mock_response
        mocker.patch('ai_api.services.groq_provider.Groq', return_value=mock_client)
        
        provider = GroqProvider()
        serie_info = {"name": "Test Series"}
        stamp_batch = [{"id": 1}, {"id": 2}]
        
        result = provider._extract_batch(serie_info, stamp_batch, 1, 2)
        
        assert len(result["stamps"]) == 2
        mock_client.chat.completions.create.assert_called_once()
