import pytest
from unittest.mock import Mock, patch, mock_open
import json

from ai_api.services.llm_service import LLMService
from common.api.messages import Messages

@pytest.mark.skip(reason="To be fixed after multi-provider refactor")
class TestLLMService:
    """Test class for LLMService (No Database)."""
    
    def test_init_success(self, mocker):
        """Test successful initialization of LLMService."""
        # Mock environment variables
        mocker.patch.dict('os.environ', {
            'GEMINI_API_KEY': 'test-api-key',
            'GEMINI_MODEL_NAME': 'gemini-1.5-flash',
            'LLM_PROVIDER': 'gemini'
        })
        
        # Mock model initialization
        mock_model = Mock()
        mocker.patch('ai_api.services.llm_service.genai.Client.models', mock_model)
        
        # Mock prompt loading
        mock_prompt = "Test prompt template"
        mocker.patch('ai_api.services.llm_service.SERIES_EXTRACTION_PROMPT_TEMPLATE', mock_prompt)
        
        service = LLMService()
        
        # Verify initialization
        assert service.client.models == mock_model
        assert service.prompt_template == mock_prompt
    
    def test_init_missing_api_key(self, mocker):
        """Test initialization fails when API key is missing."""
        mocker.patch('ai_api.services.llm_service.GEMINI_API_KEY', None)
        
        with pytest.raises(ValueError, match=Messages.AI.missing_api_key()):
            LLMService()
    
    def test_init_missing_model_name(self, mocker):
        """Test initialization fails when model name is missing."""
        mocker.patch('ai_api.services.llm_service.GEMINI_MODEL_NAME', None)
        
        with pytest.raises(ValueError, match=Messages.AI.missing_model_name()):
            LLMService()
    
    def test_format_prompt(self):
        """Test prompt formatting with provided parameters."""
        service = LLMService()
        service.prompt_template = "Template: {{ input_data }}"
        
        result = service._format_prompt("{'issue': 'Hello world}")
        
        expected = "Template: {'issue': 'Hello world}"
        assert result == expected
    
    def test_clean_json_response_with_markdown(self):
        """Test JSON response cleaning when wrapped in markdown."""
        service = LLMService()
        
        response_text = "```json\n{\"key\": \"value\"}\n```"
        result = service._clean_json_response(response_text)
        
        expected = "{\"key\": \"value\"}"
        assert result == expected
    
    def test_clean_json_response_standalone(self):
        """Test JSON response cleaning when standalone."""
        service = LLMService()
        
        response_text = "{\"key\": \"value\"}"
        result = service._clean_json_response(response_text)
        
        expected = "{\"key\": \"value\"}"
        assert result == expected
    
    def test_series_extraction_success(self, mocker):
        """Test successful series extraction call."""
        service = LLMService()
        
        # Mock model response
        mock_response = Mock()
        mock_response.text = json.dumps({
            "confidence_score": 95,
            "confidence_score_reasons": ["Test reason"],
            "description": "Test description",
            "issue_date": "2023-01-01",
            "artist": "Test Artist",
            "printer": "Test Printer",
            "print_type": "Test Type",
            "perforation": "Test Perforation",
            "paper_type": "Test Paper",
            "stamp_type": "Test Type",
            "notes": "Test Notes",
            "total_printed": 1000,
            "market_value_mnh": 10.5,
            "market_value_used": 5.5,
            "stamps": []
        })
        
        service.client.models.generate_content = Mock(return_value=mock_response)
        
        result = service.series_extract("Test Series", "2023-01-01", "1234")
        
        assert result["confidence_score"] == 95
        assert result["description"] == "Test description"
        service.client.models.generate_content.assert_called_once()
    
    def test_series_extraction_validation_error(self, mocker):
        """Test series extraction fails with validation error."""
        service = LLMService()
        
        with pytest.raises(ValueError, match=Messages.AI.missing_input_data()):
            service.series_extract("Series name", "2023-01-01", "")
    
    def test_series_extraction_service_error(self, mocker):
        """Test series extraction fails with service error."""
        service = LLMService()
        
        # Mock model to raise exception
        service.client.models.generate_content = Mock(side_effect=Exception(Messages.AI.error()))
        
        with pytest.raises(Exception, match=Messages.AI.error()):
            service.series_extract("Test Series", "2023-01-01", "1234")
