# Frontend Testing Patterns

## Quick Reference

| Aspect | Convention |
|---|---|
| Runner | pytest + pytest-asyncio |
| Config | `frontend/pytest.ini` — `asyncio_mode = auto`, `testpaths = tests`, `pythonpath = .` |
| Mock lib | `unittest.mock` — `MagicMock`, `AsyncMock`, `patch`, `PropertyMock` |
| No Flet headless | All tests are pure unit tests with mocked Flet objects |
| Fixtures | Defined per-class (not in conftest), except 4 string fixtures in conftest.py |
| Async | `AsyncMock` for async methods; `@pytest.mark.asyncio` optional (auto mode) |
| Type hints | Required on ALL test signatures |

---

## Mocking Strategies

### A. Patch Flet constructors — for components that call Flet constructors but don't extend Flet

```python
@patch("components.buttons.alert_button.ft.Text")
@patch("components.buttons.alert_button.ft.ButtonStyle")
def test_init(self, mock_style, mock_text):
    btn = AlertButton(text="Delete")
    assert btn.bgcolor[ft.ControlState.DEFAULT] == RED
```

Patch path must target the **module's own import namespace**, not `flet.*`.

### B. No mocking — for components that extend Flet classes (`ft.Container`, `ft.View`)

```python
def test_initial_areas_empty(self):
    header = AppHeader()
    assert header.left_area.controls == []
    assert header.center_area.controls == []
```

Real Flet objects are created. Tests access real attributes (`height`, `bgcolor`, `content`).

### C. Patch Flet APIs — for `ft.SharedPreferences`, `ft.AlertDialog`, etc.

```python
async def test_saves_jwt_token(self, ui):
    mock_prefs = MagicMock()
    mock_prefs.set = AsyncMock()
    with patch("core.base_ui.ft.SharedPreferences", return_value=mock_prefs):
        await ui._save_user("test-token", ...)
        mock_prefs.set.assert_any_call(USER_JWT_TOKEN, "test-token")
```

### D. Patch subcomponents — for composite controls

```python
def test_stores_issue(self, sample_issue):
    with patch("components.table.issue_detail.issue_detail_card.StampCard"):
        card = IssueDetailCard(issue=sample_issue, ...)
    assert card._issue == sample_issue
```

---

## Service Mocking Pattern

Services extend `BaseService` and delegate HTTP to `_make_request`. Mock at that level:

```python
@pytest.fixture
def service(self) -> IssueService:
    return IssueService()

@pytest.fixture
def mock_response(self) -> MagicMock:
    response = MagicMock(spec=requests.Response)
    response.status_code = 200
    return response

async def test_get_issues(self, service, mock_response):
    with patch.object(service, "_make_request", new_callable=AsyncMock, return_value=mock_response) as mock_req:
        result = await service.get_issues()
        assert result is mock_response
        call_kwargs = mock_req.call_args[1]
        assert call_kwargs["request_type"] == service.GET
```

Key points:
- `_make_request` is replaced with `AsyncMock` returning `MagicMock(spec=requests.Response)`
- Set `response.json.return_value` when the service method parses JSON
- Error paths: return `None` (network error) or non-2xx `status_code`

---

## Page / Route Handler Testing

### Function-based handlers (`main.py`)

```python
@pytest.fixture
def page_mock(self) -> MagicMock:
    page = MagicMock()
    page.push_route = AsyncMock()
    page.route = URLs.Frontend.login
    page.views = []
    return page

@pytest.fixture
def event_mock(self, page_mock) -> MagicMock:
    event = MagicMock()
    event.page = page_mock
    return event

async def test_redirects_anonymous_user(self, event_mock):
    with patch.object(ft, "SharedPreferences") as mock_prefs:
        prefs_instance = MagicMock()
        prefs_instance.get = AsyncMock(return_value=None)
        mock_prefs.return_value = prefs_instance
        await route_change(event_mock)
    event_mock.page.push_route.assert_called_once_with(URLs.Frontend.login)
```

### Class-based pages (`ft.View` subclasses)

Instantiate directly with a mock `page`:

```python
mock_page = MagicMock()
with patch.object(type(card), "page", new_callable=PropertyMock, return_value=mock_page):
    card._handle_delete_issue(MagicMock())
```

---

## Test Data Fixtures

Defined inside test classes (not conftest) — one fixture per class:

```python
class TestIssueServiceGetIssues:
    @pytest.fixture
    def service(self) -> IssueService:
        return IssueService()

class TestIssueDetailCard:
    @pytest.fixture
    def sample_issue(self) -> dict:
        return {"id": 42, "name": "Marianne Series", ...}
```

Use `autouse` fixtures for global state reset (e.g., language):

```python
@pytest.fixture(autouse=True)
def _reset_language() -> None:
    set_language("en")
```

---

## File Layout

```
frontend/tests/
├── __init__.py              # empty, marks package
├── conftest.py              # 4 shared string fixtures only
├── test_<module>.py         # mirrors source file under frontend/
```

Each test file uses classes to group by feature/method:

```python
class TestSetBackground:
class TestSaveUser:
class TestDeleteUser:
```

---

## Common Gotchas

- **Patch path uses the importing module's namespace**, not the defining module's: `patch("core.base_ui.ft.SharedPreferences")` not `patch("flet.SharedPreferences")`
- **`ft.Container` lacks `on_click`** in Flet 0.84.0 — use a nested `ft.GestureDetector` or `ft.InkWell`
- **`PropertyMock` for `self.page`** — Flet controls expose `page` as a property; tests must patch it with `PropertyMock` when the code reads `self.page`
- **Locale auto-loads on import** — `Translations.load_translations()` runs at module import time; tests implicitly rely on locale JSON files being present at `frontend/assets/locales/`
