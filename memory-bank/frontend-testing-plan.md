# Frontend Unit Testing Plan

## Current State
- **Zero tests** exist for the frontend
- `pytest.ini` is backend-only (`DJANGO_SETTINGS_MODULE`, `testpaths = backend`)
- `pytest-asyncio`, `pytest-mock`, `pytest-cov` are already in `requirements.dev.txt`
- 3 service files are **Flet-free** — no `import flet` → testable in standard pytest
- 5 core files have **zero Flet dependency** (utils, logger, severity, urls, log_setup)

## File Structure (goal)

```
frontend/
├── tests/
│   ├── __init__.py
│   ├── conftest.py                  # shared fixtures, module-level setup
│   ├── test_utils.py                # Step 1: pure functions
│   ├── test_base_service.py         # Step 2: service layer
│   ├── test_auth_service.py
│   ├── test_issue_service.py
│   ├── test_translations.py         # Step 3: translations
│   ├── test_column_def.py           # Step 3: formatters
│   ├── test_colors.py               # Step 4: colors
│   └── test_base_ui.py              # Step 4: base UI
└── pytest.ini                       # frontend-specific pytest config
```

## Incremental Steps

### Step 1 — Pure functions, zero mocking

| File | What to test |
|------|-------------|
| `core/utils.py` | `is_valid_email()` — valid/invalid formats, `is_strong_password()` — strength rules |

**Action items:**
1. Create `frontend/tests/__init__.py`
2. Create `frontend/tests/conftest.py` (empty fixture setup)
3. Create `frontend/tests/test_utils.py`
4. Update root `pytest.ini` to add `frontend` to `testpaths` and handle asyncio
5. Run tests to validate infrastructure

**Effort:** ~30 min • **No mocking needed** • **Provides immediate proof of test infrastructure**

---

### Step 2 — Service layer (mocked HTTP)

| File | What to test |
|------|-------------|
| `services/base_service.py` | `_make_request()` for all 4 HTTP methods, timeout handling, error handling |
| `services/auth_service.py` | `login()` builds correct URL/headers, `signup()` adds API key header |
| `services/issue_service.py` | `get_issues()` builds query params, `delete_issue()` calls correct URL, `get_issue_stamps()` adds issue_id param, `get_years()` calls correct endpoint |

**Test pattern:** Mock `requests.get/post/put/delete` at the `asyncio.to_thread` wrapper level, or mock at `BaseService._make_request` level for service-specific tests.

**Effort:** ~2h • **Uses `pytest-mock` + `pytest-asyncio`** • **No Flet needed**

---

### Step 3 — Translation system + formatters

| File | What to test |
|------|-------------|
| `core/translations.py` | `_get_nested_value()` with dot keys, `translate()` with fallback/interpolation, `_()` function, `set_language()`/`get_language()` |
| `components/table/column_def.py` | `fmt_currency()` en/es formats, `fmt_number()` en/es formats, `fmt_date()` with valid/invalid dates, `COLUMNS` list structure |

**Note:** Both files `import flet as ft` at module level — `ft` must be **installed** (already in requirements.base.txt) but doesn't need a running Flet app. `translations.py` also calls `Translations.load_translations()` at import time which reads JSON files from disk — this works in test if cwd is `frontend/`.

**Effort:** ~1.5h • **Flet must be pip-installed but no runtime needed** • **Uses pytest fixtures for test data**

---

### Step 4 — Colors + BaseUI (light Flet mocking)

| File | What to test |
|------|-------------|
| `components/colors.py` | `lighten_color()` hex manipulation, constant types/values |
| `core/base_ui.py` | `_set_background()` with/without image file, `_save_user()`/`_delete_user()` with mocked `ft.SharedPreferences` |

**Effort:** ~1h • **Requires basic Flet mocking** • `BaseUI._save_user` needs `ft.SharedPreferences` patched

---

### Step 5 — Component unit tests (advanced)

| Class | Strategy |
|-------|----------|
| `ColumnDef` + `COLUMNS` | Already covered in Step 3 |
| `IssueRow` | Test data cell rendering: verify cells match COLUMNS order/formatters |
| `TableHeader` | Test sort indicators, column render count matches COLUMNS |
| `TablePagination` | Test page text formatting, button enable/disable states |
| `IssueTableApp` | Test state management (page, sort, filter), data flow (requires Flet runtime) |
| `AppHeader` | Test left_area content |
| `YearRangeSelector` | Test year parsing, Canvas interaction simulation |

**Challenge:** Flet components extend `ft.Container`/`ft.View` and use `self.page`, `self.update()`. These require either:
- A running Flet test harness (no official Flet test plugin exists for 0.84.0)
- Heavy mocking of `ft.Container`, `ft.Control`, `self.page`

**Recommendation:** Defer Step 5 until Steps 1-4 are solid. Focus unit tests on **logic extraction** rather than DOM-like assertions.

## Running Tests

```bash
# From repo root — run all tests (backend + frontend)
pytest

# From frontend/ — run only frontend tests
cd frontend && pytest

# With coverage
cd frontend && pytest --cov=. --cov-report=term-missing
```

## Config Notes

Root `pytest.ini` needs `frontend` added to `testpaths`:
```ini
testpaths = backend frontend
```

Or create a separate `frontend/pytest.ini`:
```ini
[pytest]
testpaths = tests
pythonpath = ..
asyncio_mode = auto
```

## Dependencies Already Available

All test dependencies are in `frontend/requirements.dev.txt`:
- `pytest==9.0.1`
- `pytest-asyncio==1.3.0`
- `pytest-mock==3.15.1`
- `pytest-cov==7.0.0`
