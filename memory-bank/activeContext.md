# Active Context

## Current Task
- **Task**: Frontend unit testing — Steps 1-5 + log_setup + Tier 3-4 + Tier 5 lines complete (398 tests)
- **Priority**: medium
- **Status**: in_progress (Tier 7 next: issue_detail_card ~15 tests)

## Remaining Untested Files (15 files, ~95 tests planned)

### Tier 1 — Pure utilities (skipped, already covered)
- `core/severity.py` — 100% covered
- `core/urls.py` — 100% covered
- `settings.py` — 95% covered (dotenv fallback)

### Tier 2 — Core infrastructure (partially done)
- `core/logger.py` — 100% covered
- `core/log_setup.py` — ✅ 17 tests, 100% coverage
- Extend service tests (12)

### Tier 3 — Button components ✅ COMPLETE
- `alert_button.py`, `default_button.py`, `primary_button.py`, `text_button.py`, `link_button.py`, `icon_button.py` — ✅ 30 tests

### Tier 4 — Form components ✅ COMPLETE
- `components/form/text_field.py` — ✅ 34 tests

### Tier 5 — Layout components (partially done)
- `horizontal_line.py` — ✅ 7 tests
- `vertical_line.py` — ✅ 7 tests
- `brand.py` — deferred (heavy Flet mocking, needs integration test approach)
- `app_drawer.py` — deferred (heavy Flet mocking, needs integration test approach)

### Tier 6 — Auth components, deferred (heavy Flet mocking)
- `login_card.py` — deferred (ft.Container._values descriptor issue, needs integration test)
- `signup_card.py` — deferred (same _values issue, needs integration test)

### Tier 7 — Table detail card, heavy mocking (~15 tests)
- `issue_detail_card.py` (15)

### Tier 8 — Page templates, heavy mocking (~15 tests)
- `standard_page.py` (10), `not_found_page.py` (5)

### Tier 9 — Full pages, heaviest mocking (~30 tests)
- `login_page.py` (10), `signup_page.py` (10), `collections_page.py` (5), `stamps_manager_page.py` (10)

### Tier 10 — Entry point (~25 tests)
- `main.py` (25)

**Current: 398 tests → Target: ~493 tests** (Tier 6 deferred, -20 tests)

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
- [Today] Added on_add_stamp callback chain through 4 layers: IssueDetailCard → IssueRow → IssueTableApp → StampsManagerPage
- [Today] Add-stamp card renders as last stamp grid item: centered "+" icon on DARK_IMG_BG, "Add Stamp" label below, card with elevation=1
- [Today] Fixed ft.Card.on_click → ft.Container.on_click (Card lacks on_click in Flet 0.84.0), moved click handler to inner container
- [Today] All 398 tests pass after add-stamp implementation
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
- [Today] Implemented Step 5: component tests — 84 new tests (all passing)
  - Created test_app_header.py: three-area layout, add/clear methods, default state (13 tests)
  - Created test_year_range_selector.py: coordinate conversion (_year_to_x/_x_to_year), set_range, properties, track width (14 tests)
  - Created test_table_pagination.py: _format_range en/es, _total_pages, nav button states, update_state (18 tests)
  - Created test_table_header.py: column count, sortable/non-sortable detection, toggle sort, update_sort_indicators (10 tests)
  - Created test_issue_row.py: cell count, zebra striping, name column color, expand/collapse, set_stamps, set_loading (10 tests)
  - Created test_issue_table_app.py: _parse_filter (8 cases), initial state, filter/sort/page callbacks, _rebuild_rows (19 tests)
  - Key patterns: patch at `components.table.issue_table_app.IssueRow` (where used, not defined), mock `_schedule_fetch` to avoid page dependency, use `object.__setattr__` workaround for read-only `page` property
  - IssueDetailCard expects stamps as `{"data": [...]}` not plain list
  - Nav buttons start enabled; `_update_nav_buttons()` must be called explicitly to set disabled states
- [Today] Implemented log_setup tests — 17 new tests (all passing)
  - Created test_log_setup.py: dictConfig call, directory creation, path resolution, handlers (file/console), formatters (standard/colored), logger suppression (17 tests)
  - Pattern: mock `logging.config.dictConfig` + `Path.mkdir` + `Path.is_absolute`, verify config dict structure
  - Coverage: `core/log_setup.py` now at 100%
- [Today] Implemented Tier 3 button tests — 30 new tests (all passing)
  - Created test_buttons.py: AlertButton (5), DefaultButton (5), PrimaryButton (5),
    TextButton (5), LinkButton (5), IconButton (5)
  - Pattern: mock ft.Text/ft.ButtonStyle/ft.TextButton/ft.Container, verify colors,
    hover behavior, on_click/data assignment
  - Key finding: Flet hover events use `e.data = "true"` for hovered and `e.data = ""`
    (empty string) for not hovered — `"false"` is truthy in Python
- [Today] Implemented Tier 4 form component tests — 34 new tests (all passing)
  - Created test_text_field.py: FieldStyle (7), DEFAULT preset (3), APP_HEADER preset (9),
    TextField (15)
  - Pattern: mock ft.TextField, verify FieldStyle defaults and overrides, test style
    resolution order (field_style → explicit params → kwargs)
  - Key pattern: TextField extends ft.TextField, uses FieldStyle dataclass for presets,
    explicit params override field_style values
- [Today] Implemented Tier 5 layout component tests — 14 new tests (all passing)
  - Created test_layout.py: HorizontalLine (7), VerticalLine (7)
  - Pattern: direct instantiation (no mocking needed), verify height/width/bgcolor/border_radius
  - Note: Brand and AppDrawer deferred — heavy Flet mocking required, need integration test approach
- [Today] Attempted Tier 6 auth card tests — deferred (ft.Container._values descriptor issue)
  - login_card.py and signup_card.py cannot be unit tested due to Flet's descriptor system
  - These require integration test approach with real Flet page context
