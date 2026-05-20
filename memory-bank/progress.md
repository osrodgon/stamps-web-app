# Progress Tracker

## Completed Tasks

### Frontend Docstring Updates (2025-05-11)
- [x] Analyzed colors.py for readability improvements
- [x] Added type hints to colors.py (Option 1: Add Type Hints & Docstrings)
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
  - test_base_ui.py: 18 tests (_set_background, _save_user, _delete_user)
- [ ] Implement Step 5: component tests (IssueRow, TableHeader, TablePagination, etc.)
- [ ] Implement unit tests for main.py (planned)

### Code Improvements
- [ ] Fix LSP type errors in frontend code (pre-existing)
- [ ] Add type hints to remaining untyped functions

### Documentation
- [ ] Update opencode_rules.md to reflect Flet (not NiceGUI)
- [ ] Document test patterns in memory-bank

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
│       ├── issue_detail_card.py  # IssueDetailCard class (expanded detail view)
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
components/table/issue_detail_card.py
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