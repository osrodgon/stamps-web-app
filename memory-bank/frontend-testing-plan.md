# Frontend Unit Testing Plan

## Current State
- **320 tests** exist for the frontend (Steps 1-5 + log_setup complete)
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
│   ├── test_base_ui.py                  # ✅ Step 4: base UI (20 tests)
│   ├── test_app_header.py               # ✅ Step 5: component (13 tests)
│   ├── test_year_range_selector.py      # ✅ Step 5: component (14 tests)
│   ├── test_table_pagination.py         # ✅ Step 5: component (18 tests)
│   ├── test_table_header.py             # ✅ Step 5: component (10 tests)
│   ├── test_issue_row.py                # ✅ Step 5: component (10 tests)
│   ├── test_issue_table_app.py          # ✅ Step 5: component (19 tests)
│   └── test_log_setup.py                # ✅ log_setup (17 tests)
└── pytest.ini                           # ✅ frontend-specific pytest config
```

**Total: 320 tests, all passing**

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

### Step 5 — Component unit tests (advanced) ✅ COMPLETE

| Class | Tests | Result |
|-------|-------|--------|
| `AppHeader` | 13 tests | ✅ Three-area layout, add/clear, default state |
| `YearRangeSelector` | 14 tests | ✅ Coordinate conversion, set_range, properties, track width |
| `TablePagination` | 18 tests | ✅ _format_range en/es, _total_pages, nav buttons, update_state |
| `TableHeader` | 10 tests | ✅ Column count, sortable detection, toggle sort, indicators |
| `IssueRow` | 10 tests | ✅ Cell count, zebra striping, name color, expand, set_stamps, loading |
| `IssueTableApp` | 19 tests | ✅ _parse_filter, state, filter/sort/page callbacks, _rebuild_rows |

**Result:** 84 tests, all passing
**Key patterns:**
- Patch at `components.table.issue_table_app.IssueRow` (where used, not defined)
- Mock `_schedule_fetch` to avoid `page.run_task` dependency
- `IssueDetailCard` expects stamps as `{"data": [...]}` not plain list
- Nav buttons start enabled; `_update_nav_buttons()` must be called explicitly

---

## Remaining Untested Files (26 files, ~193 tests planned)

### Tier 1 — Pure utilities (skipped, already covered)
- `core/severity.py` — 100% covered by existing tests
- `core/urls.py` — 100% covered by existing tests
- `settings.py` — 95% covered (lines 30-31: dotenv import fallback)

### Tier 2 — Core infrastructure (partially done)
- `core/logger.py` — 100% covered by existing tests
- `core/log_setup.py` — ✅ 17 tests, 100% coverage
- Extend service tests — 12 tests (remaining)

### Tier 3 — Button components, minimal mocking (~30 tests)
| File | Est. tests |
|------|------------|
| `alert_button.py`, `default_button.py`, `primary_button.py`, `text_button.py`, `link_button.py`, `icon_button.py` | 5 each |

### Tier 4 — Form components, moderate mocking (~15 tests)
| File | Est. tests |
|------|------------|
| `components/form/text_field.py` | 15 |

### Tier 5 — Layout components, light mocking (~15 tests)
| File | Est. tests |
|------|------------|
| `brand.py`, `app_drawer.py`, `horizontal_line.py`, `vertical_line.py` | 5, 5, 3, 3 |

### Tier 6 — Auth components, moderate mocking (~20 tests)
| File | Est. tests |
|------|------------|
| `login_card.py`, `signup_card.py` | 10 each |

### Tier 7 — Table detail card, heavy mocking (~15 tests)
| File | Est. tests |
|------|------------|
| `issue_detail_card.py` | 15 |

### Tier 8 — Page templates, heavy mocking (~15 tests)
| File | Est. tests |
|------|------------|
| `standard_page.py`, `not_found_page.py` | 10, 5 |

### Tier 9 — Full pages, heaviest mocking (~30 tests)
| File | Est. tests |
|------|------------|
| `login_page.py`, `signup_page.py`, `collections_page.py`, `stamps_manager_page.py` | 10, 10, 5, 10 |

### Tier 10 — Entry point (~25 tests)
| File | Est. tests |
|------|------------|
| `main.py` | 25 |

**Current: 320 tests → Target: ~513 tests**

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
