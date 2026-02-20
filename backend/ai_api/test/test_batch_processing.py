"""
Tests for LLM batch processing functionality.

This module tests the batch processing capabilities of LLM providers,
ensuring that large stamp series are correctly split into batches
and processed sequentially.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import json

from ai_api.services.base_llm_provider import BaseLLMProvider
from _backend.settings import LLM_BATCH_SIZE


class TestBaseLLMProviderBatchMethods:
    """Test class for BaseLLMProvider batch helper methods."""
    
    def test_should_batch_below_threshold(self):
        """Test that _should_batch returns False when below threshold."""
        provider = Mock(spec=BaseLLMProvider)
        
        # Below or equal to threshold should not batch
        result = BaseLLMProvider._should_batch(provider, LLM_BATCH_SIZE)
        assert result is False
        
        result = BaseLLMProvider._should_batch(provider, LLM_BATCH_SIZE - 1)
        assert result is False
    
    def test_should_batch_above_threshold(self):
        """Test that _should_batch returns True when above threshold."""
        provider = Mock(spec=BaseLLMProvider)
        
        # Above threshold should batch
        result = BaseLLMProvider._should_batch(provider, LLM_BATCH_SIZE + 1)
        assert result is True
        
        result = BaseLLMProvider._should_batch(provider, LLM_BATCH_SIZE * 3)
        assert result is True
    
    def test_split_into_batches_even_split(self):
        """Test _split_into_batches with even number of stamps."""
        provider = Mock(spec=BaseLLMProvider)
        
        stamps = [{"id": i} for i in range(10)]  # 10 stamps with batch_size=5
        batches = BaseLLMProvider._split_into_batches(provider, stamps)
        
        assert len(batches) == 2
        assert len(batches[0]) == 5
        assert len(batches[1]) == 5
    
    def test_split_into_batches_uneven_split(self):
        """Test _split_into_batches with uneven number of stamps."""
        provider = Mock(spec=BaseLLMProvider)
        
        stamps = [{"id": i} for i in range(7)]  # 7 stamps with batch_size=5
        batches = BaseLLMProvider._split_into_batches(provider, stamps)
        
        assert len(batches) == 2
        assert len(batches[0]) == 5
        assert len(batches[1]) == 2
    
    def test_split_into_batches_empty_list(self):
        """Test _split_into_batches with empty list."""
        provider = Mock(spec=BaseLLMProvider)
        
        batches = BaseLLMProvider._split_into_batches(provider, [])
        
        assert len(batches) == 0
    
    def test_split_into_batches_single_batch(self):
        """Test _split_into_batches with fewer stamps than batch size."""
        provider = Mock(spec=BaseLLMProvider)
        
        stamps = [{"id": i} for i in range(3)]  # 3 stamps with batch_size=5
        batches = BaseLLMProvider._split_into_batches(provider, stamps)
        
        assert len(batches) == 1
        assert len(batches[0]) == 3


class TestGeminiProviderBatchProcessing:
    """Test class for GeminiProvider batch processing."""
    
    @patch('ai_api.services.gemini_provider.GEMINI_API_KEY', 'test-api-key')
    @patch('ai_api.services.gemini_provider.GEMINI_MODEL_NAME', 'gemini-1.5-flash')
    @patch('ai_api.services.gemini_provider.genai.Client')
    def test_single_extraction_for_small_series(self, mock_client_class):
        """Test that small series use single extraction (no batching)."""
        from ai_api.services.gemini_provider import GeminiProvider
        
        # Mock the Gemini client
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # Mock response for single extraction
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "issue_name": "Test Series",
            "description": "Test description",
            "stamps": [
                {"edifil_code": "001", "motive": "Stamp 1"},
                {"edifil_code": "002", "motive": "Stamp 2"}
            ]
        })
        mock_client.models.generate_content.return_value = mock_response
        
        provider = GeminiProvider()
        
        # Create test data with few stamps (below threshold)
        clean_data = json.dumps({
            "serie_info": {"issue_name": "Test Series"},
            "stamps": [{"id": i} for i in range(3)]  # 3 stamps, below LLM_BATCH_SIZE
        })
        
        result = provider.series_extract("Test Series", "2023", clean_data)
        
        # Should call generate_content only once (single extraction)
        mock_client.models.generate_content.assert_called_once()
        assert result["issue_name"] == "Test Series"
    
    @patch('ai_api.services.gemini_provider.GEMINI_API_KEY', 'test-api-key')
    @patch('ai_api.services.gemini_provider.GEMINI_MODEL_NAME', 'gemini-1.5-flash')
    @patch('ai_api.services.gemini_provider.genai.Client')
    def test_batch_extraction_for_large_series(self, mock_client_class):
        """Test that large series use batch extraction."""
        from ai_api.services.gemini_provider import GeminiProvider
        
        # Mock the Gemini client
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # Mock responses for header + batch extractions
        # 8 stamps with batch_size=5 = 2 batches + 1 header = 3 calls
        header_response = MagicMock()
        header_response.text = json.dumps({
            "issue_name": "Large Series",
            "description": "Test description for large series"
        })
        
        batch1_response = MagicMock()
        batch1_response.text = json.dumps({
            "stamps": [{"edifil_code": f"00{i}", "motive": f"Stamp {i}"} for i in range(5)]
        })
        
        batch2_response = MagicMock()
        batch2_response.text = json.dumps({
            "stamps": [{"edifil_code": f"00{i}", "motive": f"Stamp {i}"} for i in range(5, 8)]
        })
        
        mock_client.models.generate_content.side_effect = [
            header_response,
            batch1_response,
            batch2_response
        ]
        
        provider = GeminiProvider()
        
        # Create test data with many stamps (above threshold)
        clean_data = json.dumps({
            "serie_info": {"issue_name": "Large Series"},
            "stamps": [{"id": i} for i in range(8)]  # 8 stamps, above LLM_BATCH_SIZE
        })
        
        result = provider.series_extract("Large Series", "2023", clean_data)
        
        # Should call generate_content 3 times (header + 2 batches)
        assert mock_client.models.generate_content.call_count == 3
        assert result["issue_name"] == "Large Series"
        assert len(result["stamps"]) == 8
    
    @patch('ai_api.services.gemini_provider.GEMINI_API_KEY', 'test-api-key')
    @patch('ai_api.services.gemini_provider.GEMINI_MODEL_NAME', 'gemini-1.5-flash')
    @patch('ai_api.services.gemini_provider.genai.Client')
    def test_batch_extraction_fails_on_error(self, mock_client_class):
        """Test that batch extraction fails entire process on error."""
        from ai_api.services.gemini_provider import GeminiProvider
        
        # Mock the Gemini client
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # Mock header success, but batch 1 fails
        header_response = MagicMock()
        header_response.text = json.dumps({"issue_name": "Series"})
        
        mock_client.models.generate_content.side_effect = [
            header_response,
            Exception("Batch processing failed")
        ]
        
        provider = GeminiProvider()
        
        # Create test data with many stamps
        clean_data = json.dumps({
            "serie_info": {"issue_name": "Series"},
            "stamps": [{"id": i} for i in range(8)]
        })
        
        # Should raise exception
        with pytest.raises(Exception):
            provider.series_extract("Series", "2023", clean_data)


class TestGroqProviderBatchProcessing:
    """Test class for GroqProvider batch processing."""
    
    @patch.dict('os.environ', {
        'GROQ_API_KEY': 'test-api-key',
        'GROQ_MODEL_NAME': 'llama3-8b-8192'
    })
    @patch('ai_api.services.groq_provider.Groq')
    def test_single_extraction_for_small_series(self, mock_groq_class):
        """Test that small series use single extraction (no batching)."""
        from ai_api.services.groq_provider import GroqProvider
        
        # Mock the Groq client
        mock_client = MagicMock()
        mock_groq_class.return_value = mock_client
        
        # Mock response for single extraction
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "issue_name": "Test Series",
            "description": "Test description",
            "stamps": [
                {"edifil_code": "001", "motive": "Stamp 1"},
                {"edifil_code": "002", "motive": "Stamp 2"}
            ]
        })
        mock_client.chat.completions.create.return_value = mock_response
        
        provider = GroqProvider()
        
        # Create test data with few stamps (below threshold)
        clean_data = json.dumps({
            "serie_info": {"issue_name": "Test Series"},
            "stamps": [{"id": i} for i in range(3)]  # 3 stamps, below LLM_BATCH_SIZE
        })
        
        result = provider.series_extract("Test Series", "2023", clean_data)
        
        # Should call create only once (single extraction)
        mock_client.chat.completions.create.assert_called_once()
        assert result["issue_name"] == "Test Series"
    
    @patch.dict('os.environ', {
        'GROQ_API_KEY': 'test-api-key',
        'GROQ_MODEL_NAME': 'llama3-8b-8192'
    })
    @patch('ai_api.services.groq_provider.Groq')
    def test_batch_extraction_for_large_series(self, mock_groq_class):
        """Test that large series use batch extraction."""
        from ai_api.services.groq_provider import GroqProvider
        
        # Mock the Groq client
        mock_client = MagicMock()
        mock_groq_class.return_value = mock_client
        
        # Mock responses for header + batch extractions
        header_response = MagicMock()
        header_response.choices = [MagicMock()]
        header_response.choices[0].message.content = json.dumps({
            "issue_name": "Large Series",
            "description": "Test description"
        })
        
        batch1_response = MagicMock()
        batch1_response.choices = [MagicMock()]
        batch1_response.choices[0].message.content = json.dumps({
            "stamps": [{"edifil_code": f"00{i}", "motive": f"Stamp {i}"} for i in range(5)]
        })
        
        batch2_response = MagicMock()
        batch2_response.choices = [MagicMock()]
        batch2_response.choices[0].message.content = json.dumps({
            "stamps": [{"edifil_code": f"00{i}", "motive": f"Stamp {i}"} for i in range(5, 8)]
        })
        
        mock_client.chat.completions.create.side_effect = [
            header_response,
            batch1_response,
            batch2_response
        ]
        
        provider = GroqProvider()
        
        # Create test data with many stamps (above threshold)
        clean_data = json.dumps({
            "serie_info": {"issue_name": "Large Series"},
            "stamps": [{"id": i} for i in range(8)]  # 8 stamps, above LLM_BATCH_SIZE
        })
        
        result = provider.series_extract("Large Series", "2023", clean_data)
        
        # Should call create 3 times (header + 2 batches)
        assert mock_client.chat.completions.create.call_count == 3
        assert result["issue_name"] == "Large Series"
        assert len(result["stamps"]) == 8


class TestPromptFormatting:
    """Test class for prompt formatting in batch processing."""
    
    def test_format_header_prompt(self):
        """Test formatting of header extraction prompt."""
        provider = Mock(spec=BaseLLMProvider)
        provider.header_prompt_template = "Series Info: {{ input_data }}"
        
        serie_info = {"issue_name": "Test", "year": "2023"}
        result = BaseLLMProvider._format_header_prompt(provider, serie_info)
        
        assert "Test" in result
        assert "2023" in result
        assert "{{ input_data }}" not in result
    
    def test_format_batch_prompt(self):
        """Test formatting of batch extraction prompt."""
        provider = Mock(spec=BaseLLMProvider)
        provider.batch_prompt_template = (
            "Context: {{ series_context }}\n"
            "Batch {{ batch_number }} of {{ total_batches }}\n"
            "Data: {{ input_data }}"
        )
        
        serie_info = {"issue_name": "Test"}
        stamp_batch = [{"edifil_code": "001"}, {"edifil_code": "002"}]
        
        result = BaseLLMProvider._format_batch_prompt(
            provider, serie_info, stamp_batch, 1, 3
        )
        
        assert "Batch 1 of 3" in result
        assert "{{ batch_number }}" not in result
        assert "{{ total_batches }}" not in result
        assert "{{ input_data }}" not in result
        assert "{{ series_context }}" not in result