# Progress Tracker

## Completed Tasks

### Frontend Unit Testing Complete (2025-05-22)
- [x] Implemented Tier 7: IssueDetailCard — 35 tests
- [x] Implemented Tier 8: StandardPage 10 tests, NotFoundPage 6 tests
- [x] Implemented Tier 9: StampsManagerPage static methods + 5 handler stubs — 15 tests
- [x] Implemented Tier 10: main.py — 24 tests (ROUTE_HANDLERS, configure_page, route_change, view_pop)
- [x] Total: 618 tests (all passing)
- [x] Deferred: login_card, signup_card, login_page, signup_page, collections_page (Flet descriptor system)

### Frontend Docstring Updates (2025-05-11)
- [x] Analyzed colors.py for readability improvements
- [x] Added type hints to colors.py
- [x] Added type hints to all 20 color constants
- [x] Added docstrings to undocumented colors (RED, DARK_BLUE_GREY, etc.)
- [x] Added `__all__` export list to colors.py
- [x] Analyzed all frontend files for docstring needs
- [x] Added docstrings to 11 files across all priority levels
- [x] Fixed incorrect docstring in alert_button.py (PrimaryButton → AlertButton)

### File Analysis
- [x] Analyzed main.py for unit testing options
- [x] Created test plan for main.py
- [x] Reviewed backend test patterns as reference
- [x] Reviewed frontend_nicegui test structure as reference

### Memory Bank Setup (2025-05-11)
- [x] Created memory-bank/index.md (entry point)
- [x] Created memory-bank/activeContext.md (current work)
- [x] Created memory-bank/progress.md (completed tasks)

## Pending Tasks

### Testing
- [x] Implement Step 1: pure function tests for core/utils.py (29 tests, all passing)
- [x] Create frontend/tests/ directory with __init__.py, conftest.py
- [x] Create frontend/pytest.ini with isolated config
- [x] Implement Step 2: service layer tests (41 tests, all passing)
  - test_base_service.py: 14 tests (HTTP methods, error handling, constants)
  - test_auth_service.py: 9 tests (login, signup, API key headers)
  - test_issue_service.py: 18 tests (get_issues filters, delete, stamps, years)
- [x] Implement Step 3: translations + formatters tests (88 tests, all passing)
  - test_translations.py: 33 tests (nested value, translate, _(), set/get_language, JSON load)
  - test_column_def.py: 55 tests (fmt_currency, fmt_number, fmt_date, ColumnDef, COLUMNS)
- [x] Implement Step 4: colors + BaseUI tests (61 tests, all passing)
  - test_colors.py: 43 tests (lighten_color edge cases, hex validation, 30 color constants)
  - test_base_ui.py: 20 tests (_set_background, _save_user, _delete_user)
- [x] Implement Step 5: component tests (84 tests, all passing)
  - test_app_header.py: 13 tests (three-area layout, add/clear, default state)
  - test_year_range_selector.py: 14 tests (coordinate conversion, set_range, properties, track width)
  - test_table_pagination.py: 18 tests (_format_range en/es, _total_pages, nav buttons, update_state)
  - test_table_header.py: 10 tests (column count, sortable detection, toggle sort, indicators)
  - test_issue_row.py: 10 tests (cell count, zebra striping, name color, expand, set_stamps, loading)
  - test_issue_table_app.py: 19 tests (_parse_filter, state, filter/sort/page callbacks, _rebuild_rows)
- [x] Implement log_setup tests (17 tests, all passing)
  - test_log_setup.py: 17 tests (dictConfig, directory creation, path resolution, handlers, formatters, loggers)
- [x] Implement Tier 3 button tests (30 tests, all passing)
  - test_buttons.py: AlertButton (5), DefaultButton (5), PrimaryButton (5),
    TextButton (5), LinkButton (5), IconButton (5)
- [x] Implement Tier 4 form component tests (34 tests, all passing)
  - test_text_field.py: FieldStyle (7), DEFAULT preset (3), APP_HEADER preset (9),
    TextField (15)
- [x] Implement Tier 5 layout component tests (14 tests, all passing)
  - test_layout.py: HorizontalLine (7), VerticalLine (7)
- [ ] Implement Tier 6: auth components — deferred (ft.Container._values issue, needs integration test)
- [x] Implement Tier 7: table detail card — 35 tests (IssueDetailCard)
- [x] Implement Tier 8: page templates — 16 tests (StandardPage 10, NotFoundPage 6)
- [x] Implement Tier 9: full pages — 15 tests (StampsManagerPage static methods + stubs)
  - login_page, signup_page, collections_page deferred (ft.View _values descriptor issue)
- [x] Implement Tier 10: main.py — 24 tests (ROUTE_HANDLERS, configure_page, route_change, view_pop)

### Stamp Deletion (2025-05-22)
- [x] Added `delete_stamp()` to IssueService
- [x] Confirmation dialog in StampCard + callback wrapping in IssueDetailCard
- [x] 5 locale keys: `ui.delete`, `stamps.delete_confirm`, `stamps.delete_confirm_message`, `stamps.delete_success`, `stamps.delete_error`
- [x] Callback wiring through IssueRow → IssueTableApp → StampsManagerPage (API call commented out)
- [x] All 488 tests passing

### Database Backup/Restore Commands (2025-05-22)
- [x] Created `stamps_db_backup.py` — interactive/non-interactive backup with `--mode` (system/stamps/full)
- [x] Created `stamps_db_restore.py` — interactive restore with confirmation prompt
- [x] Added `backend/backups/` to `.gitignore`
- [x] 1008 backend tests + 491 frontend tests passing

### Issue Deletion (2025-05-22)
- [x] Confirmation dialog in `IssueDetailCard._handle_delete_issue` showing issue name + cascade warning
- [x] Locale keys provided by user (not managed by automation)
- [x] Live API call in `StampsManagerPage._handle_delete_issue` with success/error notifications and table reload
- [x] 3 new tests for issue delete dialog (dialog shown, confirm fires callback, cancel does not fire)
- [x] All 491 tests passing

### DatePicker Styling & Future Dates (2025-05-24)
- [x] Added `year_shape` to DatePickerTheme via post-construction assignment (skipped by __init__)
- [x] Added `shape` to DatePickerTheme for dialog corner radius (8px)
- [x] Changed DatePickerField default `last_date` from `today` to `today + 365 days`
- [x] 2 new tests (year_shape, shape); 560 total passing

### Client Timezone Detection (2025-05-26)
- [x] `index.html` JS detects `Intl.DateTimeFormat().resolvedOptions().timeZone` and passes as `?tz=` query param
- [x] `core/utils.py`: `init_client_timezone(page)` + `get_local_today()` — reads query param, returns today in client timezone
- [x] `settings.py`: added `DEFAULT_TIMEZONE` env var
- [x] `main.py`: calls `init_client_timezone(page)` on startup
- [x] Replaced `datetime.date.today()` and `datetime.datetime.now()` with `get_local_today()` in `date_picker.py` and `issue_form.py`
- [x] 3 new tests for `init_client_timezone`, 3 for `get_local_today`, updated 2 existing tests
- [x] All 566 tests passing

### Add Issue Form (2025-05-24)
- [x] Added URL definitions for `countries`, `artists`, `paper_types`, `printers`
- [x] Added 7 service methods: `create_issue`, `get_countries`, `get_artists`, `get_stamp_types`, `get_paper_types`, `get_print_types`, `get_printers`
- [x] Created `IssueForm` dialog component with specs grid (3 cols), date picker + "Today" button, reference data dropdowns, multiline description/notes, Create/Cancel buttons
- [x] Wired `_handle_add_issue` in StampsManagerPage → opens IssueForm → reloads table on success
- [x] 28 service tests + 16 IssueForm tests = 44 new tests
- [x] All 535 frontend tests passing
- [x] Noted Flet 0.84.0 quirks: `ft.Dropdown` sets `on_change` after construction; `ft.TextButton` uses `content` not `text`

### Code Improvements
- [ ] Fix LSP type errors in frontend code (pre-existing)
- [ ] Add type hints to remaining untyped functions

### IssueForm Visual Alignment with IssueDetailCard (2025-06-12)
- [x] Added `hide_action_icons: bool = False` param to IssueHeaderSection — guards icon visibility in enter/exit_edit_mode
- [x] Rebuilt IssueForm to use IssueHeaderSection + IssueSpecsGrid in permanent edit mode (reuses same components as edit flow)
- [x] Kept Cancel/Create buttons at bottom of dialog
- [x] Removed all hand-rolled form builder methods (`_build_name_section`, `_build_specs_grid`, `_paired_cell`, etc.) — now driven by shared components
- [x] Rewrote `_on_create` to read from IssueHeaderSection properties + IssueSpecsGrid edit_state (same pattern as `_handle_save_edit`)
- [x] Updated 24 tests (mock shared components, test via mock properties instead of old field attributes)
- [x] All 624 tests passing

### IssueService + IssueForm Refactoring (2025-05-28)
- [x] Extracted `_fetch_ref` / `_create_ref` helpers in IssueService — 14 boilerplate methods → 1-liners
- [x] Split `_build_form()` into named methods (`_build_name_section`, `_build_date_row`, `_build_specs_grid`, `_build_notes_section`, `_build_actions`, `_assemble_card`)
- [x] Renamed `_mnh_field` → `_mint_field`, `_date_picker_icon` → `_date_picker`
- [x] Removed dead `_on_field_change` handler and `_field_cell` static method
- [x] Replaced `_make_dropdown` setattr pattern with `_build_dropdown` + explicit assignment
- [x] Moved DatePicker overlay append from `_build_form()` to `show()`
- [x] Added `super().__init__()` call in IssueForm
- [x] Documented `_on_success` as sync-only
- [x] Fixed stale docstrings in both files
- [x] All 585 tests passing

### Stamp Deletion (2025-05-22)
- [x] Step 1: Added `delete_stamp()` method to `IssueService` (issue_service.py)
- [x] Step 2: Confirmation dialog in `StampCard._handle_delete` + callback wrapping in `IssueDetailCard`
- [x] Step 3: Added 5 locale keys (en/es): `ui.delete`, `stamps.delete_confirm`, `stamps.delete_confirm_message`, `stamps.delete_success`, `stamps.delete_error`
- [x] Step 4: Wired `on_delete_stamp(stamp_id, issue_id)` callback through → `StampsManagerPage` with live API call, success/error notifications, and stamps refresh
- [x] All 488 tests passing

### DatePicker Timezone Fix — Complete (2025-05-30)
- [x] JS timezone detection in `index.html` — writes `Intl.DateTimeFormat().resolvedOptions().timeZone` to `localStorage` under `flutter.stamps_app._timezone` with `JSON.stringify()`
- [x] `init_client_timezone()` in `utils.py` — reads the stored timezone via `SharedPreferences.get(TIMEZONE)`
- [x] `get_local_today()` in `utils.py` — returns today in the client timezone using `zoneinfo.ZoneInfo`
- [x] `to_local_date()` in `utils.py` — converts Flutter's UTC-normalised datetime back to client local date
- [x] `DEFAULT_TIMEZONE` env var in `settings.py`
- [x] Wired `init_client_timezone()` into `main.py` startup
- [x] Replaced `datetime.date.today()` with `get_local_today()` in `date_picker.py` and `issue_form.py`
- [x] 12 new tests for all three timezone functions — 597 total passing

### Client-Side JWT Token Validation (2025-05-30)
- [x] Added `validate_jwt_token()` to `core/utils.py` — decodes JWT without signature verification, checks `exp` claim against UTC
- [x] Wired validation into `main.py` root route (redirect only when stored JWT is still valid, not just present)
- [x] Added `PyJWT==2.10.1` to `requirements.base.txt`
- [x] Added 7 locale keys (en/es) for issue creation feedback
- [x] Cleaned up unused imports in `login_view.py`
- [x] Note: validation runs on first page load only; follow-ups for API-level checks TBD

### Add Issues to Database (backend) — Complete
- [x] Backend endpoint to persist issues from frontend IssueForm
- [x] Wire up working tree changes on branch `212-feature-stamps-manager-add-issues`
- [x] Fixed duplicate issue creation bug in `issue_form.py` (duplicated `_on_create` logic causing two API calls)

### Add Stamps
- [x] Create backend endpoint to add stamps to an issue
- [ ] Build frontend stamp form dialog
- [ ] Wire up in StampsManagerPage

### Documentation
- [x] Update opencode_rules.md to reflect Flet (not NiceGUI)
- [x] Document test patterns in memory-bank

## Notes
- Frontend framework: Flet (not NiceGUI)
- Testing: pytest with pytest-asyncio
- All docstring updates completed for Priority 1-4 files
- IssueTable fully implemented with IssueDetailCard expansion

### YearRangeSelector Implementation (2025-05-12)
- [x] Created YearRangeSelector with Canvas-drawn two-thumb slider
- [x] Added configurable track_height, thumb_radius, step, padding params
- [x] Added hover aura, drag focus (thumb enlarges), tap-to-move support
- [x] Added async callback support in _notify_change (sync/async transparent)
- [x] Added set_range() public method for post-construction API initialization
- [x] Added sel_min_year / sel_max_year properties for external range reads
- [x] Added get_years() method to IssueService (GET /years/)
- [x] Integrated into StampsManagerPage header with round-to-nearest-5 init
- [x] Added debounced year range filter (300ms) → updates table via set_year_filter()
- [x] Added SLIDER_INACTIVE color constant to colors.py
- [x] Locale-aware number formatting in TablePagination range text
- [x] Renamed StampIssueService → IssueService
- [x] Docstring audit across all modified files

### IssueDetailCard Implementation (2025-05-14)
- [x] Created IssueDetailCard component (issue_detail_card.py) with 4 modules:
  - Module A: Identity & Header (series name 32px bold + emission date)
  - Module B: Technical Specification Matrix (ResponsiveRow 4→2 cols, GREY_50 bg)
  - Module C: Description & Notes (between specs and valuation)
  - Module D: Financial Valuation Summary (mint GREEN_700, used BLUE_700, total printed)
  - Module E: Stamp Inventory DataTable (name, edifil, fesofi, face_value, color, total_printed, market_value_mnh, market_value_used, image)
- [x] Added async stamp fetch in IssueTableApp._on_expand → _fetch_stamps_for_row
- [x] Added set_stamps() method on IssueRow to update details after async fetch
- [x] Added loading/empty states in stamp table section
- [x] Added 7 new translation keys: year, mint, used, market_value_mnh, technical_specifications, valuation, image
- [x] Fixed _kv_cell to properly set container.col property (not as kwargs)

### Add-Stamp Button (2025-05-21)
- [x] Added `on_add_stamp` callback param to IssueDetailCard, IssueRow, IssueTableApp
- [x] Added `_handle_add_stamp` handler in IssueDetailCard (fires callback with issue_id)
- [x] Added stub `_handle_add_stamp` in StampsManagerPage (logs only)
- [x] Add-stamp card renders as last grid item: centered IconButton (48px ADD icon) in fixed-height Column, hover GREY_700→GREEN_700, tooltip from locale key
- [x] Fixed ft.Card.on_click → ft.Container.on_click (Card lacks on_click in Flet 0.84.0)
- [x] Renamed locale key stamps.add → stamps.add_tooltip
- [x] All 398 tests passing after implementation

### Add-Issue Button (2025-05-21)
- [x] Added IconButton with ADD icon in AppHeader right_area
- [x] Added async stub handler _handle_add_issue in StampsManagerPage

### Docstring Batch 2 (2025-05-21)
- [x] Added docstrings to _handle_add_stamp in IssueDetailCard
- [x] Added full docstring to show_stamp_detail_dialog()
- [x] Documented all callback params in IssueRow.__init__ and IssueTableApp.__init__
- [x] Added docstrings to 6 handler stubs in StampsManagerPage
- [x] Updated class/init docstrings for add-issue button reference

### IssueDetailCard Read/Edit Toggle (2025-05-30)
- [x] Added `update_issue()` to IssueService (PUT issues/{id}/)
- [x] Local edit mode toggle in IssueDetailCard for stamp_type field only
- [x] Edit icon swaps to save/cancel icons, stamp_type cell replaced with AutoCompleteField
- [x] Passes IssueService through IssueRow → IssueTableApp → IssueDetailCard
- [x] On save: resolves stamp_type (select or create ref), calls PUT, updates local data, fires `on_edit_issue` callback
- [x] Upgraded `_handle_edit_issue` in StampsManagerPage from stub to `self._table.load(reset_page=True)`
- [x] All 614 tests passing

---

# IssueTable Implementation Plan (Flet 0.84.0 Compatible)

## 1. Component Hierarchy

| Class | Base | Responsibility |
|-------|------|-----------------|
| `IssueTableApp` | `ft.Container` | Main container, state management, data fetching |
| `TableHeader` | `ft.Container` | Column titles, sort indicators |
| `IssueRow` | `ft.Container` | Single row with expansion (IssueDetailCard) |
| `TablePagination` | `ft.Container` | Footer with dropdown, navigation |

## 2. Data via API (no local models)

All data comes from the backend API. The service layer handles response parsing.

**Expected API response format:**
```json
{
  "data": {
    "issues": [
      {
        "id": 1,
        "country": "France",
        "year": "2023",
        "date": "2023-06-15",
        "name": "Marianne Series",
        "perforation": "Zebra",
        "stamp_type": "Definitive",
        "print_type": "Lithography",
        "total_printed": 500000,
        "market_value_mnh": "1.20",
        "market_value_used": "0.80"
      }
    ],
    "pagination": {
      "sort_by": "name",
      "order": "asc",
      "page": 1,
      "page_size": 15,
      "total": 65,
      "has_more": true
    }
  }
}
```

**Backend query params:** `sortBy`, `order`, `page`, `pageSize`, `name` (issue name filter)

**Service methods:**
- `get_issues(page, page_size, sort_by, order, name) -> requests.Response | None`
- `delete_issue(id) -> requests.Response | None`
- `get_issue_stamps(id) -> requests.Response | None`
- `get_years() -> requests.Response | None`

All return raw response objects — caller handles parsing and status checks (same pattern as AuthService).

## 3. State Management

```python
class IssueTableApp(ft.Container):
    def __init__(self, ...):
        self._data: list[dict] = []
        self._total: int = 0
        self._current_page: int = 1
        self._rows_per_page: int = 15
        self._sort_key: str = "date"
        self._sort_order: str = "asc"
        self._lang: str = "en"
```

## 4. Visual Design

- **Header BG**: `HEADER_BG` (#232F3E, dark navy)
- **Zebra striping**: Even rows `BG_LIGHT` (#f5f5f5), odd rows white
- **Hover**: `ROW_HOVER` (#E8E8E8) highlight
- **Row divider**: `ROW_BORDER` (#EEEEEE)
- **Font**: 12px data (Roboto), 12px headers (Roboto-Bold, white, uppercase)
- **Value column**: `text_align=ft.TextAlign.RIGHT`
- **Number formatting**: Locale-aware (en: 1,234.56 / es: 1.234,56)
- **No text wrap**: `no_wrap=True`, `overflow=ELLIPSIS` on data cells

## 5. UI Components

### ColumnDef (`column_def.py`)
- `ColumnDef` dataclass — `translation_key`, `api_key`, `width`, `text_align`, `sortable`, `fmt`
- `COLUMNS` list — single source of truth (8 columns currently)
- Locale-aware formatters: `fmt_currency()`, `fmt_number()`

### TableHeader
- Dark background container (`HEADER_BG`)
- Builds cells by iterating `COLUMNS`
- Any `sortable=True` column gets sort arrow + click handler
- Sort icon rebuilt from scratch on each sort change

### IssueRow
- `ft.Container` with nested controls
- Builds cells by iterating `COLUMNS` with formatters
- Chevron toggle expands details panel with IssueDetailCard
- Hover highlight via `_on_hover`
- `set_stamps()` method updates card with async stamp data

### TablePagination
- Bottom-right aligned
- Dropdown: [10, 15, 20, 50, 100, All] options
- Text: "1-15 of 65"
- Four IconButtons: first, prev, next, last
- `update_state(page, page_size, total)` method for external sync

## 6. Functionality

| Feature | Implementation |
|---------|-----------------|
| Sorting | Click sortable column header → toggle `_sort_key` + `_sort_order` → call API → rebuild rows |
| Pagination | Server-side via `page`/`pageSize` params → update state → rebuild rows |
| Row expansion | Chevron toggles IssueDetailCard with specs, description, valuation, stamp table (async) |

## 7. Details Expansion - Stamps Data

**TODO**: Need to check the backend Stamp model to determine which fields to display in the expanded details section.

## 8. File Structure

```
frontend/
├── components/
│   ├── form/
│   │   ├── text_field.py          # FieldStyle, TextField class
│   │   └── year_range_selector.py # YearRangeSelector class
│   └── table/
│       ├── column_def.py         # ColumnDef dataclass, COLUMNS list, formatters
│       ├── issue_detail/
│       │   ├── issue_detail_card.py  # IssueDetailCard class
│       │   ├── stamp_card.py         # StampCard class
│       │   └── stamp_detail_dialog.py # show_stamp_detail_dialog function
│       ├── issue_table_app.py    # IssueTableApp class
│       ├── issue_row.py          # IssueRow class
│       ├── table_header.py       # TableHeader class
│       └── table_pagination.py   # TablePagination class
└── services/
    └── issue_service.py          # IssueService class
```

## 9. Deployment Order

- [x] Step 1: Add `IssueService` in `frontend/services/issue_service.py`
- [x] Step 2: Build `IssueRow` (most complex, reusable)
- [x] Step 3: Build `TableHeader` and `TablePagination`
- [x] Step 4: Build `IssueTableApp` - assemble pieces, add state
- [x] Step 5: Add events: sort, pagination, expand (delete still TODO)
- [x] Step 6: Add `__init__.py` exports (skipped — not used elsewhere)
- [x] Step 7: Integrate into StampsManagerPage content_area
- [x] Step 8: Refactor to COLUMNS-driven architecture with column_def.py
- [x] Step 9: Locale-aware number formatting (en/es)

---

## Logger Coverage Reference

Classes inherit Logger through `BaseUI(Logger)`, `StandardPage(ft.View, BaseUI)`, or `BaseService(Logger)`.

**Files whose classes DO have Logger in MRO:**
```
core/logger.py                          # Logger definition
core/base_ui.py                         # BaseUI(Logger)
components/templates/standard_page.py   # StandardPage(ft.View, BaseUI)
components/layout/app_header.py         # AppHeader(ft.Container, Logger)
components/auth/login_card.py           # LoginCard(ft.Container, BaseUI)
components/auth/signup_card.py          # SignupCard(ft.Container, BaseUI)
services/base_service.py                # BaseService(Logger)
services/auth_service.py                # AuthService(BaseService)
services/issue_service.py               # IssueService(BaseService)
pages/auth/login_page.py                # LoginPage(ft.View, BaseUI)
pages/auth/signup_page.py               # SignupPage(ft.View, BaseUI)
pages/not_found_page.py                 # NotFoundPage(ft.View, BaseUI)
pages/admin/stamps_manager_page.py      # StampsManagerPage(StandardPage)
pages/collection/collections_page.py    # CollectionsPage(StandardPage)
```

**Files whose classes do NOT have Logger in MRO:**
```
components/buttons/alert_button.py
components/buttons/default_button.py
components/buttons/icon_button.py
components/buttons/link_button.py
components/buttons/primary_button.py
components/buttons/text_button.py
components/colors.py
components/form/text_field.py
components/form/year_range_selector.py
components/layout/app_drawer.py
components/layout/brand.py
components/layout/horizontal_line.py
components/layout/vertical_line.py
components/table/column_def.py
components/table/issue_detail/issue_detail_card.py
components/table/issue_detail/stamp_card.py
components/table/issue_detail/stamp_detail_dialog.py
components/table/issue_row.py
components/table/issue_table_app.py
components/table/table_header.py
components/table/table_pagination.py
core/log_setup.py
core/severity.py
core/translations.py
core/urls.py
core/utils.py
main.py
settings.py
```