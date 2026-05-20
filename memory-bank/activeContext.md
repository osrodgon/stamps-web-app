# Active Context

## Current Task
- **Task**: Frontend unit testing — Steps 1-4 completed
- **Priority**: medium
- **Status**: in_progress (Step 5 next: component tests)

## Notes
- Frontend uses Flet 0.84.0 (not NiceGUI)
- IssueTable fully implemented and integrated into StampsManagerPage
- COLUMNS list in column_def.py is single source of truth for table columns
- All table components extend ft.Container (no UserControl in Flet 0.84.0)
- Service methods return raw requests.Response (AuthService pattern)
- Colors defined in colors.py with named constants (no raw hex in components)
- YearRangeSelector: custom Canvas-drawn two-thumb slider, debounced on_change,
  configurable track height, thumb radius, step, padding, and hover aura
- StampIssueService renamed to IssueService, added get_years() method
- IssueDetailCard: 4 modules (Header, Specs Grid, Valuation Bar, Stamp Table) + description/notes
- Stamps fetched async via IssueTableApp._fetch_stamps_for_row → row.set_stamps()
- 3 service files are Flet-free (base_service, auth_service, issue_service)
- 5 core files have zero Flet dependency (utils, logger, severity, urls, log_setup)
- Frontend unit testing plan saved to memory-bank/frontend-testing-plan.md
- Spanish locale fixes applied: éxitO, caracteres, Tipo de sello, Tirada total
- Duplicate ai_series_lookup keys removed from both en.json and es.json

## Session Log
- [Today] Analyzed IconButton for readability improvements
- [Today] Created IssueTable implementation plan
- [Today] Stored plan in memory-bank/progress.md
- [Today] Implemented StampIssueService, IssueRow, TableHeader, TablePagination, IssueTableApp
- [Today] Integrated IssueTable into StampsManagerPage
- [Today] Refactored to COLUMNS-driven architecture with column_def.py
- [Today] Fixed circular import, UserControl, Dropdown, layout issues
- [Today] Added TextField filter to AppHeader left area
- [Today] Added AppHeader left_area expand=True for filter layout
- [Today] Created YearRangeSelector with Canvas rendering (3px track, 6px thumbs, step=5)
- [Today] Added set_range(), set_year_filter(), debounced callbacks, async callback support
- [Today] Integrated YearRangeSelector into StampsManagerPage with API year range init
- [Today] Added SLIDER_INACTIVE color constant
- [Today] Added issue_table_app module-level docstring
- [Today] Created AGENTS.md with session start protocol
- [Today] Removed delete button from IssueRow and TableHeader
- [Today] Created IssueDetailCard with 4 modules + description/notes section
- [Today] Added async stamp fetch in IssueTableApp._on_expand → set_stamps()
- [Today] Added 7 new translation keys (year, mint, used, market_value_mnh, etc.)
- [Today] Fixed _kv_cell to properly set container.col property
- [Today] Added DARK_IMG_BG to colors.py, replaced #1a1a1a references
- [Today] Analyzed locale files: found typos, inconsistencies, dead keys
- [Today] Fixed Spanish typos (éxito, caracteres), capitalization (Tipo de sello), Tirada total
- [Today] Removed 17 duplicate keys from en.json and 16 from es.json (ai_series_lookup)
- [Today] Created frontend-testing-plan.md in memory-bank (5 incremental steps)
- [Today] Implemented Step 1: frontend test infrastructure + 29 utils tests (all passing)
  - Created frontend/tests/__init__.py, conftest.py, test_utils.py
  - Created frontend/pytest.ini with isolated config
  - Tests: is_valid_email (15 cases), is_strong_password (14 cases)
- [Today] Implemented Step 2: service layer tests — 41 new tests (all passing)
  - Created test_base_service.py: HTTP methods (GET/POST/PUT/DELETE), error handling, constants (14 tests)
  - Created test_auth_service.py: login/signup endpoint validation, API key headers (9 tests)
  - Created test_issue_service.py: get_issues filters, delete_issue, get_issue_stamps, get_years (18 tests)
  - Pattern: mock asyncio.to_thread for BaseService, mock _make_request for subclasses
- [Today] Implemented Step 3: translations + formatters — 88 new tests (all passing)
  - Created test_translations.py: _get_nested_value dot keys, translate fallback/interpolation, _() function, set_language/get_language, JSON load verification (33 tests)
  - Created test_column_def.py: fmt_currency en/es, fmt_number en/es, fmt_date valid/invalid/all months, ColumnDef dataclass, COLUMNS list structure (55 tests)
  - Note: fmt_date uses global current_language via _(), not lang param — tests set_language() explicitly
- [Today] Implemented Step 4: colors + BaseUI — 61 new tests (all passing)
  - Created test_colors.py: lighten_color edge cases, hex validation, 30 color constant values/types (43 tests)
  - Created test_base_ui.py: _set_background image/fallback, _save_user all fields, _delete_user all fields (18 tests)
  - Pattern: mock os.path.exists + ft.Container for background, mock ft.SharedPreferences for user session
