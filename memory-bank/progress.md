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
- [ ] Implement unit tests for main.py (planned)
- [ ] Create frontend/tests/ directory
- [ ] Create conftest.py with shared fixtures

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

---

# IssueTable Implementation Plan (Flet 0.84.0 Compatible)

## 1. Component Hierarchy

| Class | Base | Responsibility |
|-------|------|-----------------|
| `IssueTableApp` | `ft.Container` | Main container, state management, data fetching |
| `TableHeader` | `ft.Container` | Column titles, sort indicators |
| `IssueRow` | `ft.UserControl` | Single row with expansion, delete action |
| `TablePagination` | `ft.Container` | Footer with dropdown, navigation |
| `IssueTableSearch` | `ft.Container` | Global search input field with debounce |

## 2. Data via API (no local models)

All data comes from the backend API. The service layer handles response parsing.

**Expected API response format:**
```json
{
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
```

**Backend query params:** `sortBy`, `order`, `page`, `pageSize`, `name` (issue name filter)

**Service methods:**
- `get_issues(page, page_size, sort_by, order, name) -> requests.Response | None`
- `delete_issue(id) -> requests.Response | None`
- `get_issue_stamps(id) -> requests.Response | None`

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
        self._expanded_rows: set[int] = set()
        self._name_filter: str = ""
```

## 4. Visual Design

- **Header BG**: `#232F3E` (dark navy)
- **Zebra striping**: Alternate between `None` and `"#F8F9FA"` bgcolor
- **Row divider**: `ft.border.only(bottom=ft.BorderSide(1, "#EEEEEE"))`
- **Font**: 12px data, 11px headers (uppercase, bold)
- **Value column**: `text_align=ft.TextAlign.RIGHT`
- **Delete button**: Red circular with confirmation dialog

## 5. UI Components

### IssueTableSearch
- Container with `ft.TextField`
- Search icon prefix
- Debounce: wait 300ms after typing before API call
- Name search: sends `name` query param to backend (name__icontains filter)
- On change → call service → update `_name_filter` → reset to page 1

### TableHeader
- Dark background container (`#232F3E`)
- Row with Text columns: "Country", "Date ▼", "Issue Name", "Type", "Value"
- Date column has sort icon (arrow up/down based on `_sort_order`)
- `on_click` triggers sort in parent

### IssueRow
- `ft.UserControl` with `build()` method
- Fields: details button (chevron), country, date with calendar icon, issue name, type, value (right-aligned)
- **Details expansion**: Hidden `Container` toggled by chevron - displays list of related `Stamp` objects
- **Delete**: Red icon button → shows `ft.AlertDialog` confirmation first

### TablePagination
- Bottom-right aligned
- Dropdown: [5, 10, 15, 25] options
- Text: "1-10 of 65"
- Four IconButtons: first, prev, next, last (disabled when at bounds)

## 6. Functionality

| Feature | Implementation |
|---------|-----------------|
| Global search via API | Debounced TextField → service call with `name` param → update `_filtered_data` |
| Sorting | Click header → toggle `_sort_key` + `_sort_order` → call API → update |
| Pagination | `_displayed_data = _filtered_data[(page-1)*per_page : page*per_page]` |
| Row expansion | Toggle row ID in `_expanded_rows` set → call `self.update()` |
| Delete | Show AlertDialog → on_confirm → call API delete → refresh data |

## 7. Details Expansion - Stamps Data

**TODO**: Need to check the backend Stamp model to determine which fields to display in the expanded details section.

## 8. File Structure

```
frontend/
├── components/
│   └── table/
│       ├── __init__.py
│       ├── issue_table_app.py    # IssueTableApp class
│       ├── table_header.py       # TableHeader class
│       ├── issue_row.py          # IssueRow class
│       ├── table_pagination.py   # TablePagination class
│       └── issue_table_search.py # IssueTableSearch class
└── services/
    └── stamp_issue_service.py    # API methods
```

## 9. Deployment Order

- [x] Step 1: Add `StampIssueService` in `frontend/services/stamp_issue_service.py`
- [ ] Step 2: Build `IssueRow` (most complex, reusable)
- [ ] Step 3: Build `TableHeader` and `TablePagination`
- [ ] Step 4: Build `IssueTableSearch`
- [ ] Step 5: Build `IssueTableApp` - assemble pieces, add state
- [ ] Step 6: Add events: sort, pagination, expand, delete, search
- [ ] Step 7: Add `__init__.py` exports