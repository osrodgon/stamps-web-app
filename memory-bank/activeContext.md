# Active Context

## Current Task
- None (all pending items deferred)

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

**Current: 535 tests → Target: ~493 tests** (Tier 6 deferred, -20 tests)

## Notes
- Frontend uses Flet 0.84.0 (not NiceGUI)
- Locale files are user-managed — never modify en.json or es.json
- DatePicker timezone fix complete — JS in index.html writes to localStorage, Python reads via SharedPreferences
- Add issues to database (backend) — complete on branch `212-feature-stamps-manager-add-issues`
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
- [Today] Added `validate_jwt_token()` to utils.py and wired into main.py root route — client-side JWT exp check on first page load
- [Today] Added PyJWT dependency, 7 issue creation locale keys (en/es), cleaned unused imports in login_view.py
- [Today] DatePicker timezone fix complete — JS in index.html writes to localStorage, Python reads via SharedPreferences
- [Today] 12 new timezone tests, 597 total passing
- [Today] Fixed 3 failing issue form tests (mock `json` → `payload` kwargs, `show_snack_bar` → `show_dialog`, network error expectation)
- [Today] Refactored IssueService: extracted `_fetch_ref` / `_create_ref` helpers, 14 boilerplate get/create methods → 1-liners
- [Today] Refactored IssueForm (`issue_form.py`):
  - Split `_build_form()` into 8 named methods
  - `_mnh_field` → `_mint_field`, `_date_picker_icon` → `_date_picker`
  - Removed dead `_on_field_change` handler + registrations
  - Removed dead `_field_cell` method
  - Replaced `_make_dropdown(items, attr)` setattr pattern with `_build_dropdown(items)` + explicit assignment
  - Moved DatePicker overlay append from `_build_form()` to `show()` (one call)
  - Added `super().__init__()` call
  - Documented `_on_success` as sync-only
- [Today] Fixed stale docstrings: IssueService class doc (missing 7 create methods), IssueForm attribute doc (`_page` → `page`), added docstrings to all builder/static methods
- [Today] All 585 tests passing