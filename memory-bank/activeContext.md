# Stamps Web App - Active Context

## Current Work Status

**Task**: Separate error messages for AI extraction vs. save operations
**Status**: ✅ **COMPLETED**

### What We Just Accomplished

1. **Added New Translation Keys**: Added save-specific error messages to both locale files:
   - English (`en.json`): `save_error_network`, `save_error_validation`, `save_error_service`, `save_error_unknown`
   - Spanish (`es.json`): Same keys with Spanish translations

2. **Updated Error Handling in stamps_manager_page.py**: Modified `_handle_save_ai_issue` method to use the new save-specific error keys:
   - Changed from `error_network` to `save_error_network`
   - Changed from `error_validation` to `save_error_validation`
   - Changed from `error_service` to `save_error_service`
   - Changed from `error_unknown` to `save_error_unknown`

### Why This Change Was Needed

Previously, both AI extraction (`_handle_ai_extraction`) and save operations (`_handle_save_ai_issue`) used the same error messages. This was confusing for users because:
- Error messages about "AI service unavailable" when trying to save didn't make sense
- Error messages about "network error" during save should be different from extraction errors

Now users get contextually appropriate error messages depending on whether the error occurred during AI extraction or during the save operation.

### Recent Changes Summary

| File | Change |
|------|--------|
| `frontend/assets/locales/en.json` | Added save_error translation keys |
| `frontend/assets/locales/es.json` | Added save_error translation keys |
| `frontend/pages/admin/stamps_manager_page.py` | Updated `_handle_save_ai_issue` to use new keys |

### Key Technical Context

- **Architecture**: Django REST Framework backend with NiceGUI frontend
- **Authentication**: JWT tokens + API Key system
- **Frontend Pattern**: Component-based with service layer
- **Internationalization**: English/Spanish via JSON translation files

### Next Steps

- Run the application to verify the changes work correctly
- Consider if any other error messages need to be differentiated
