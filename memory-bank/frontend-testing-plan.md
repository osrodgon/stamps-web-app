# Frontend Unit Testing Plan

## Current State
- **219 tests** exist for the frontend (Steps 1-4 complete)
- `frontend/pytest.ini` with isolated config (`testpaths = tests`, `pythonpath = .`, `asyncio_mode = auto`)
- `pytest-asyncio`, `pytest-mock`, `pytest-cov` are already in `requirements.dev.txt`
- 3 service files are **Flet-free** — no `import flet` → testable in standard pytest
- 5 core files have **zero Flet dependency** (utils, logger, severity, urls, log_setup)

## File Structure (goal)

```
frontend/
├── tests/
│   ├── __init__.py                      # ✅ Created
│   ├── conftest.py                      # ✅ Created
│   ├── pytest.ini                       # ✅ Created
│   ├── test_utils.py                    # ✅ Step 1: pure functions (29 tests)
│   ├── test_base_service.py             # ✅ Step 2: service layer (14 tests)
│   ├── test_auth_service.py             # ✅ Step 2: service layer (9 tests)
│   ├── test_issue_service.py            # ✅ Step 2: service layer (18 tests)
│   ├── test_translations.py             # ✅ Step 3: translations (33 tests)
│   ├── test_column_def.py               # ✅ Step 3: formatters (55 tests)
│   ├── test_colors.py                   # ✅ Step 4: colors (43 tests)
│   └── test_base_ui.py                  # ✅ Step 4: base UI (18 tests)
└── pytest.ini                           # ✅ frontend-specific pytest config
```

**Total: 219 tests, all passing**

## Incremental Steps

### Step 1 — Pure functions, zero mocking ✅ COMPLETE

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
**Result:** 29 tests, all passing

---

### Step 2 — Service layer (mocked HTTP) ✅ COMPLETE

| File | What to test |
|------|-------------|
| `services/base_service.py` | `_make_request()` for all 4 HTTP methods, timeout handling, error handling |
| `services/auth_service.py` | `login()` builds correct URL/headers, `signup()` adds API key header |
| `services/issue_service.py` | `get_issues()` builds query params, `delete_issue()` calls correct URL, `get_issue_stamps()` adds issue_id param, `get_years()` calls correct endpoint |

**Test pattern:** Mock `requests.get/post/put/delete` at the `asyncio.to_thread` wrapper level, or mock at `BaseService._make_request` level for service-specific tests.

**Effort:** ~2h • **Uses `pytest-mock` + `pytest-asyncio`** • **No Flet needed**
**Result:** 41 tests, all passing (14 base_service + 9 auth_service + 18 issue_service)

---

### Step 3 — Translation system + formatters ✅ COMPLETE

| File | What to test |
|------|-------------|
| `core/translations.py` | `_get_nested_value()` with dot keys, `translate()` with fallback/interpolation, `_()` function, `set_language()`/`get_language()` |
| `components/table/column_def.py` | `fmt_currency()` en/es formats, `fmt_number()` en/es formats, `fmt_date()` with valid/invalid dates, `COLUMNS` list structure |

**Note:** Both files `import flet as ft` at module level — `ft` must be **installed** (already in requirements.base.txt) but doesn't need a running Flet app. `translations.py` also calls `Translations.load_translations()` at import time which reads JSON files from disk — this works in test if cwd is `frontend/`.

**Effort:** ~1.5h • **Flet must be pip-installed but no runtime needed** • **Uses pytest fixtures for test data**
**Result:** 88 tests, all passing (33 translations + 55 column_def)
**Note:** `fmt_date` uses global `current_language` via `_()`, not `lang` param — tests call `set_language()` explicitly

---

### Step 4 — Colors + BaseUI (light Flet mocking) ✅ COMPLETE

| File | What to test |
|------|-------------|
| `components/colors.py` | `lighten_color()` hex manipulation, constant types/values |
| `core/base_ui.py` | `_set_background()` with/without image file, `_save_user()`/`_delete_user()` with mocked `ft.SharedPreferences` |

**Effort:** ~1h • **Requires basic Flet mocking** • `BaseUI._save_user` needs `ft.SharedPreferences` patched
**Result:** 61 tests, all passing (43 colors + 18 base_ui)
**Pattern:** mock `os.path.exists` + `ft.Container` for background, mock `ft.SharedPreferences` for user session

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

Root `pytest.ini` — backend-only, unchanged:
```ini
testpaths = backend
```

Frontend `pytest.ini` — created with isolated config:
```ini
[pytest]
testpaths = tests
pythonpath = .
asyncio_mode = auto
```

## Dependencies Already Installed

All test dependencies are installed and working:
- `pytest==9.0.1` ✅
- `pytest-asyncio==1.3.0` ✅
- `pytest-mock==3.15.1` ✅
- `pytest-cov==7.0.0` ✅
