# Active Context

## Current Task
- **Task**: Frontend unit testing plan saved to memory-bank
- **Priority**: medium
- **Status**: completed

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
