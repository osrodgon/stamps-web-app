# Stamps Web App - Active Context

## Current Work Status

**Task**: LLM Batch Processing for Large Stamp Series
**Status**: ✅ **COMPLETED**

### What We Just Accomplished

Implemented batch processing for LLM extraction to handle large stamp series that exceed the output token limit (8192 tokens).

### Changes Summary

| File | Change |
|------|--------|
| `backend/_backend/settings.py` | Added `LLM_BATCH_SIZE = 5` configuration |
| `backend/ai_api/services/prompts.py` | Added `SERIES_HEADER_EXTRACTION_PROMPT_TEMPLATE` and `SERIES_BATCH_EXTRACTION_PROMPT_TEMPLATE` |
| `backend/ai_api/services/base_llm_provider.py` | Added batch helper methods (`_should_batch`, `_split_into_batches`, `_format_header_prompt`, `_format_batch_prompt`) |
| `backend/ai_api/services/gemini_provider.py` | Implemented batch processing logic with `_batch_extract`, `_extract_header`, `_extract_batch` |
| `backend/ai_api/services/groq_provider.py` | Implemented same batch processing logic |
| `backend/ai_api/test/test_batch_processing.py` | Created comprehensive tests for batch processing |

### How Batch Processing Works

1. **Detection**: When `clean_data` contains more stamps than `LLM_BATCH_SIZE` (default: 5), batch processing is triggered
2. **Header Extraction**: First LLM call extracts series-level information (issue_name, description, market values, etc.)
3. **Batch Processing**: Stamps are split into batches of 5, each processed with a separate LLM call
4. **Merge**: All stamp results are merged with the header to form the final response

### Key Benefits

- **Avoids token limits**: Large series (e.g., 20+ stamps) no longer fail due to output truncation
- **Configurable**: `LLM_BATCH_SIZE` can be adjusted via environment variable
- **Provider-agnostic**: Works with both Gemini and Groq providers
- **Sequential processing**: Batches are processed one-by-one to avoid rate limiting
- **Fail-fast**: If any batch fails, the entire extraction fails (no partial results)

### Technical Details

- **Batch threshold**: Series with > 5 stamps trigger batch processing
- **Batch size**: 5 stamps per batch
- **Prompt templates**: Separate prompts for header extraction vs. batch extraction
- **Error handling**: Any batch failure propagates to caller

### Next Steps

- Monitor token usage in production to fine-tune `LLM_BATCH_SIZE` if needed
- Consider adding metrics/logging for batch processing performance