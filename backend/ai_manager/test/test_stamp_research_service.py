import pytest
from unittest.mock import Mock, patch, mock_open
import json

from ai_manager.services.stamp_research_service import StampResearchService
from common.api.messages import Messages

class TestStampResearchService:
    """Test class for StampResearchService (No Database)."""
    
    def test_init_success(self, mocker):
        """Test successful initialization of StampResearchService."""
        # Mock environment variables
        mocker.patch.dict('os.environ', {
            'GEMINI_API_KEY': 'test-api-key',
            'GEMINI_MODEL_NAME': 'gemini-1.5-flash'
        })
        
        # Mock model initialization
        mock_model = Mock()
        mocker.patch('ai_manager.services.stamp_research_service.genai.Client.models', mock_model)
        
        # Mock prompt loading
        mock_prompt = "Test prompt template"
        mocker.patch('ai_manager.services.stamp_research_service.SERIES_RESEARCH_PROMPT_TEMPLATE', mock_prompt)
        
        service = StampResearchService()
        
        # Verify initialization
        assert service.client.models == mock_model
        assert service.prompt_template == mock_prompt
    
    def test_init_missing_api_key(self, mocker):
        """Test initialization fails when API key is missing."""
        mocker.patch('ai_manager.services.stamp_research_service.GEMINI_API_KEY', None)
        
        with pytest.raises(ValueError, match=Messages.AI.missing_api_key()):
            StampResearchService()
    
    def test_init_missing_model_name(self, mocker):
        """Test initialization fails when model name is missing."""
        mocker.patch('ai_manager.services.stamp_research_service.GEMINI_MODEL_NAME', None)
        
        with pytest.raises(ValueError, match=Messages.AI.missing_model_name()):
            StampResearchService()
    
    def test_format_prompt(self):
        """Test prompt formatting with provided parameters."""
        service = StampResearchService()
        service.prompt_template = "Template: {{ issue_name }}, {{ issue_date }}, {{ edifil_start_number }}"
        
        result = service._format_prompt("Test Series", "2023-01-01", "1234")
        
        expected = "Template: Test Series, 2023-01-01, 1234"
        assert result == expected
    
    def test_format_prompt_optional_field_none(self):
        """Test prompt formatting when optional field is None."""
        service = StampResearchService()
        service.prompt_template = "Template: {{ issue_name }}, {{ issue_date }}, {{ edifil_start_number }}"
        
        result = service._format_prompt("Test Series", "2023-01-01", None)
        
        expected = "Template: Test Series, 2023-01-01, n/a"
        assert result == expected
    
    def test_clean_json_response_with_markdown(self):
        """Test JSON response cleaning when wrapped in markdown."""
        service = StampResearchService()
        
        response_text = "```json\n{\"key\": \"value\"}\n```"
        result = service._clean_json_response(response_text)
        
        expected = "{\"key\": \"value\"}"
        assert result == expected
    
    def test_clean_json_response_standalone(self):
        """Test JSON response cleaning when standalone."""
        service = StampResearchService()
        
        response_text = "{\"key\": \"value\"}"
        result = service._clean_json_response(response_text)
        
        expected = "{\"key\": \"value\"}"
        assert result == expected
    
    def test_research_series_success(self, mocker):
        """Test successful research series call."""
        service = StampResearchService()
        
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
        
        result = service.research_series("Test Series", "2023-01-01", "1234")
        
        assert result["confidence_score"] == 95
        assert result["description"] == "Test description"
        service.client.models.generate_content.assert_called_once()
    
    def test_research_series_validation_error(self, mocker):
        """Test research series fails with validation error."""
        service = StampResearchService()
        
        with pytest.raises(ValueError, match="issue_name is required and cannot be empty"):
            service.research_series("", "2023-01-01", "1234")
    
    def test_research_series_service_error(self, mocker):
        """Test research series fails with service error."""
        service = StampResearchService()
        
        # Mock model to raise exception
        service.client.models.generate_content = Mock(side_effect=Exception(Messages.AI.error()))
        
        with pytest.raises(Exception, match=Messages.AI.error()):
            service.research_series("Test Series", "2023-01-01", "1234")
