# IssueTable Implementation Plan (Flet 0.84.0 Compatible)

> **Archived design doc.** Moved out of `progress.md` (Nov 2026) — the whole
> component hierarchy described here is implemented and shipped; each step is
> recorded in `progress.md` under "Frontend Unit Testing" and
> "IssueDetailCard". Kept for the response-format and component-hierarchy
> reference only. Section 7 ("Details Expansion — Stamps Data") is obsolete: the
> stamp fields are already resolved in `issue_detail_card.py`.

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
- [x] Step 10: Inline multi-select color selector with chips in `StampForm` (replacing modal dialog color picker)

---
