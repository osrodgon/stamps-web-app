"""
Tests for BaseLLMProvider.

This module tests the abstract base class for LLM providers, including
utility methods for prompt formatting, JSON cleaning, and batch processing.
"""
import pytest
import json
from unittest.mock import Mock, patch

from ai_api.services.base_llm_provider import BaseLLMProvider


# Concrete implementation for testing abstract class (named with underscore prefix to avoid pytest collection)
class _TestableProvider(BaseLLMProvider):
    """Concrete implementation of BaseLLMProvider for testing purposes."""
    
    def series_extract(self, name: str, date: str, clean_data: str) -> dict:
        """Implementation for testing."""
        return {"result": "test"}
    
    def _single_extract(self, clean_data: str) -> dict:
        """Implementation for testing."""
        return {"result": "single"}
    
    def _extract_header(self, serie_info: dict) -> dict:
        """Implementation for testing."""
        return {"header": "data"}
    
    def _extract_batch(self, serie_info: dict, stamp_batch: list, batch_number: int, total_batches: int) -> dict:
        """Implementation for testing."""
        return {"stamps": stamp_batch}
    
    def __init__(self):
        """Initialize with all template attributes."""
        super().__init__()
        # Initialize template attributes that may be checked
        self.header_prompt_template = None
        self.batch_prompt_template = None


class TestBaseLLMProviderInit:
    """Test BaseLLMProvider initialization."""
    
    def test_init(self):
        """Test successful initialization of BaseLLMProvider."""
        provider = _TestableProvider()
        
        assert provider.prompt_template is None
        assert provider.log is not None


class TestFormatPrompt:
    """Test _format_prompt method."""
    
    def test_format_prompt_success(self):
        """Test successful prompt formatting."""
        provider = _TestableProvider()
        provider.prompt_template = "Template: {{ input_data }}"
        
        result = provider._format_prompt("test data")
        
        assert result == "Template: test data"
    
    def test_format_prompt_with_complex_data(self):
        """Test prompt formatting with complex data."""
        provider = _TestableProvider()
        provider.prompt_template = "Process this: {{ input_data }}"
        
        data = "{'issue': 'Olimpiadas', 'year': '1992'}"
        result = provider._format_prompt(data)
        
        assert "Olimpiadas" in result
        assert "1992" in result
    
    def test_format_prompt_no_template_raises_error(self):
        """Test that missing prompt template raises ValueError."""
        provider = _TestableProvider()
        # prompt_template is None by default
        
        with pytest.raises(ValueError, match="Prompt template not set"):
            provider._format_prompt("test data")
    
    def test_format_prompt_empty_data_raises_error(self):
        """Test that empty input data raises ValueError."""
        provider = _TestableProvider()
        provider.prompt_template = "Template: {{ input_data }}"
        
        with pytest.raises(ValueError, match="Input data cannot be empty"):
            provider._format_prompt("")
    
    def test_format_prompt_whitespace_only_raises_error(self):
        """Test that whitespace-only input data raises ValueError."""
        provider = _TestableProvider()
        provider.prompt_template = "Template: {{ input_data }}"
        
        with pytest.raises(ValueError, match="Input data cannot be empty"):
            provider._format_prompt("   ")


class TestCleanJsonResponse:
    """Test _clean_json_response method."""
    
    def test_clean_json_with_markdown_json_block(self):
        """Test cleaning JSON wrapped in markdown code block with json label."""
        provider = _TestableProvider()
        
        response_text = '```json\n{"key": "value", "number": 123}\n```'
        result = provider._clean_json_response(response_text)
        
        expected = '{"key": "value", "number": 123}'
        assert result == expected
    
    def test_clean_json_with_markdown_no_label(self):
        """Test cleaning JSON wrapped in markdown code block without label."""
        provider = _TestableProvider()
        
        response_text = '```\n{"key": "value"}\n```'
        result = provider._clean_json_response(response_text)
        
        expected = '{"key": "value"}'
        assert result == expected
    
    def test_clean_json_standalone(self):
        """Test cleaning standalone JSON without markdown."""
        provider = _TestableProvider()
        
        response_text = '{"key": "value"}'
        result = provider._clean_json_response(response_text)
        
        expected = '{"key": "value"}'
        assert result == expected
    
    def test_clean_json_with_surrounding_text(self):
        """Test extracting JSON from text with surrounding content."""
        provider = _TestableProvider()
        
        response_text = 'Here is the result: {"key": "value"} and some text after.'
        result = provider._clean_json_response(response_text)
        
        expected = '{"key": "value"}'
        assert result == expected
    
    def test_clean_json_nested(self):
        """Test cleaning nested JSON structure."""
        provider = _TestableProvider()
        
        response_text = '{"outer": {"inner": "value"}, "array": [1, 2, 3]}'
        result = provider._clean_json_response(response_text)
        
        expected = '{"outer": {"inner": "value"}, "array": [1, 2, 3]}'
        assert result == expected
    
    def test_clean_json_no_json_object(self):
        """Test handling text with no JSON object."""
        provider = _TestableProvider()
        
        response_text = 'This is just plain text with no JSON.'
        result = provider._clean_json_response(response_text)
        
        # Should return stripped original text
        assert result == response_text.strip()


class TestParseJsonResponse:
    """Test _parse_json_response method."""
    
    def test_parse_json_success(self):
        """Test successful JSON parsing."""
        provider = _TestableProvider()
        
        response_text = '{"key": "value", "number": 123}'
        result = provider._parse_json_response(response_text)
        
        assert result == {"key": "value", "number": 123}
    
    def test_parse_json_nested(self):
        """Test parsing nested JSON."""
        provider = _TestableProvider()
        
        response_text = '{"outer": {"inner": "value"}}'
        result = provider._parse_json_response(response_text)
        
        assert result == {"outer": {"inner": "value"}}
    
    def test_parse_json_with_array(self):
        """Test parsing JSON with array."""
        provider = _TestableProvider()
        
        response_text = '{"items": [1, 2, 3]}'
        result = provider._parse_json_response(response_text)
        
        assert result == {"items": [1, 2, 3]}
    
    def test_parse_json_invalid_raises_error(self):
        """Test that invalid JSON raises ValueError."""
        provider = _TestableProvider()
        
        response_text = 'not valid json'
        
        with pytest.raises(ValueError, match="Invalid JSON response"):
            provider._parse_json_response(response_text)


class TestParseCleanData:
    """Test _parse_clean_data method."""
    
    def test_parse_clean_data_json(self):
        """Test parsing JSON format clean_data."""
        provider = _TestableProvider()
        
        clean_data = '{"serie_info": {"name": "Test"}, "stamps": [{"id": 1}]}'
        result = provider._parse_clean_data(clean_data)
        
        assert result["serie_info"]["name"] == "Test"
        assert len(result["stamps"]) == 1
    
    def test_parse_clean_data_python_literal(self):
        """Test parsing Python literal format clean_data."""
        provider = _TestableProvider()
        
        clean_data = "{'serie_info': {'name': 'Test'}, 'stamps': []}"
        result = provider._parse_clean_data(clean_data)
        
        assert result["serie_info"]["name"] == "Test"
        assert result["stamps"] == []
    
    def test_parse_clean_data_invalid_returns_empty(self):
        """Test that invalid data returns empty structure."""
        provider = _TestableProvider()
        
        clean_data = "not valid data at all"
        result = provider._parse_clean_data(clean_data)
        
        assert result == {"serie_info": {}, "stamps": []}


class TestBatchProcessing:
    """Test batch processing methods."""
    
    def test_should_batch_below_threshold(self, mocker):
        """Test _should_batch returns False when count is below threshold."""
        mocker.patch('ai_api.services.base_llm_provider.LLM_BATCH_SIZE', 100)
        
        provider = _TestableProvider()
        
        assert provider._should_batch(50) is False
        assert provider._should_batch(100) is False
    
    def test_should_batch_above_threshold(self, mocker):
        """Test _should_batch returns True when count exceeds threshold."""
        mocker.patch('ai_api.services.base_llm_provider.LLM_BATCH_SIZE', 100)
        
        provider = _TestableProvider()
        
        assert provider._should_batch(101) is True
        assert provider._should_batch(200) is True
    
    def test_split_into_batches_even(self, mocker):
        """Test splitting stamps into even batches."""
        mocker.patch('ai_api.services.base_llm_provider.LLM_BATCH_SIZE', 3)
        
        provider = _TestableProvider()
        
        stamps = [{"id": i} for i in range(9)]  # 9 stamps, batch size 3
        batches = provider._split_into_batches(stamps)
        
        assert len(batches) == 3
        assert len(batches[0]) == 3
        assert len(batches[1]) == 3
        assert len(batches[2]) == 3
    
    def test_split_into_batches_uneven(self, mocker):
        """Test splitting stamps into uneven batches."""
        mocker.patch('ai_api.services.base_llm_provider.LLM_BATCH_SIZE', 3)
        
        provider = _TestableProvider()
        
        stamps = [{"id": i} for i in range(7)]  # 7 stamps, batch size 3
        batches = provider._split_into_batches(stamps)
        
        assert len(batches) == 3
        assert len(batches[0]) == 3
        assert len(batches[1]) == 3
        assert len(batches[2]) == 1
    
    def test_split_into_batches_empty(self):
        """Test splitting empty list returns empty list."""
        provider = _TestableProvider()
        
        batches = provider._split_into_batches([])
        
        assert batches == []


class TestHeaderPrompt:
    """Test header prompt formatting methods."""
    
    def test_format_header_prompt_success(self):
        """Test successful header prompt formatting."""
        provider = _TestableProvider()
        provider.header_prompt_template = "Extract header: {{ input_data }}"
        
        serie_info = {"name": "Test Series", "year": "1992"}
        result = provider._format_header_prompt(serie_info)
        
        assert "Test Series" in result
        assert "1992" in result
    
    def test_format_header_prompt_no_template_raises_error(self):
        """Test that missing header prompt template raises ValueError."""
        provider = _TestableProvider()
        # header_prompt_template is None by default
        
        with pytest.raises(ValueError, match="Header prompt template not set"):
            provider._format_header_prompt({})


class TestBatchPrompt:
    """Test batch prompt formatting method."""
    
    def test_format_batch_prompt_success(self):
        """Test successful batch prompt formatting."""
        provider = _TestableProvider()
        provider.batch_prompt_template = "Context: {{ series_context }} Batch {{ batch_number }}/{{ total_batches }} Data: {{ input_data }}"
        
        serie_info = {"name": "Test"}
        stamp_batch = [{"id": 1}, {"id": 2}]
        
        result = provider._format_batch_prompt(serie_info, stamp_batch, 1, 3)
        
        assert "Test" in result
        assert "1" in result
        assert "3" in result
    
    def test_format_batch_prompt_no_template_raises_error(self):
        """Test that missing batch prompt template raises ValueError."""
        provider = _TestableProvider()
        # batch_prompt_template is None by default
        
        with pytest.raises(ValueError, match="Batch prompt template not set"):
            provider._format_batch_prompt({}, [], 1, 1)
