# OpenCode Rules - Stamps Web App

## Top 5 Must-Follow Rules
1. Be concise - no explanations unless asked
2. Type hints on ALL function signatures
3. Business logic in services.py, NOT views
4. Update memory-bank/ after EVERY task
5. Follow file structure: backend/{module}_api/api/views/, serializers/

## Classes are mandatory (2026-11-26)
- **Backend and frontend code lives in classes.** A module is a folder of classes,
  not a bag of loose functions. A helper is a class with a method:
  `CurrentUser(request).get()`, **not** `current_user(request)`.
- **A standalone function is the exception** and needs a reason a class cannot
  serve: a pytest fixture (`@pytest.fixture` requires a function), a framework
  callback that must be a function, a module-level constant, or code that has to run
  before a class can exist. "It is shorter" is not a reason.
- Applies to tests too: helpers are static methods of a small class, and test
  functions live inside a class. Fixtures are the only module-level functions.
- Views, serializers, services, models, pages and components were already classes;
  this rule is about the small helpers that were slipping through as functions.

## Tech Stack
- Backend: Django 6.0 + DRF 3.16.1, PostgreSQL
- Frontend: Flet 0.84.0, Python-native UI framework
- Testing: pytest, pytest-asyncio
- Docs: drf-spectacular
- Auth: JWT + API Key

## Backend Standards
- Use timezone.now (not datetime.now)
- URL pattern: /api/v1/{resource}/
- Max line: 88 chars (Black)
- Service layer for API calls
- Django: models.py → services.py → views.py
- verbose_name + db_index on FKs

## Reuse before writing (2026-11-26)
- **Look for what already exists before adding a class.** The frontend's
  `components/` folder is a library: cards, tables, dialogs, buttons, layout pieces
  and the `BaseUI` / `StandardPage` / `BaseService` bases are there to be extended,
  not copied. Two components that look alike are one component with a parameter.
- **Extend the existing abstract/base classes** instead of re-implementing their
  behaviour: pages on `StandardPage`, services on `BaseService`, components on
  `ft.Container`, dialogs on the existing builders, views on the module's view base,
  and the shared mixins (`GenericSerializer`, `Logger`).
- **One implementation per concern.** If two classes parse the same header, format
  the same money or build the same URL, put it in one class both use (backend
  example: `common/core/authorization.py`, shared by the permission and
  `CurrentUser`). Duplicating it is how the two copies start to disagree.
- Reuse is not "the same file": a component reused in three screens is still one
  component; a helper copied into two services is a bug waiting to happen.

## Frontend Standards (Flet)
- Use ft.Container(), ft.Column(), ft.Row()
- Extend ft.Control or ft.View for custom components
- Async def for event handlers
- Use SharedPreferences for client-side storage
- Color constants in components/colors.py

## Frontend Conventions (Flet + Python)
- **Type hints**: ALL function signatures MUST have type hints (Rule #2)
- **Return types**: ALL functions MUST have return type annotations
- **Classes**: PascalCase (e.g., `LoginCard`, `AlertButton`)
- **Methods/vars**: snake_case (e.g., `_on_hover`, `clear_errors`)
- **Private methods**: prefix with underscore (e.g., `_handle_login_click`)
- **Constants**: UPPER_CASE (e.g., `GREY_700`, `RED_HOVER`)
- **No unused code**: Remove unused methods, attributes, and imports
- **Docstrings**: Required on all classes and public methods
- **Event handlers**: Use `_private_method` pattern, assign to `on_click=self._handle_event`

## File Structure
backend/{module}_api/    frontend/pages/ | components/ | services/
├── models.py             ├── {page}_page.py
├── urls.py               ├── {category}/
├── api/                  │   └── {component}.py
│   ├── views/           └── services/
│   ├── serializers/         └── {service}.py
│   └── urls.py
└── test/

## Naming
- Files: snake_case (service_name.py)
- Classes: PascalCase (StampManagerPage)
- Methods/vars: snake_case (get_stamps)
- Constants: UPPER_CASE

## API Design
- REST conventions: GET/POST/PUT/DELETE
- Proper HTTP status codes (200, 201, 400, 401, 403, 404, 500)
- Standardized response format: {success, message, errors, data}
- Versioning: /api/v1/
- drf-spectacular for OpenAPI docs

## Security
- JWT + API Key authentication
- Role-based access control
- Never expose secrets in frontend
- Validate all input on backend
- CSRF protection enabled
- Environment variables for sensitive config

## Internationalization
- JSON files in assets/locales/
- Languages: English (en), Spanish (es)
- Use _() function for translations
- Descriptive keys: filter_series_year, username, sign_in
- Group related keys: filter_series_year_tooltip_*

## Testing
- Backend: pytest with fixtures
- Test location: {module}_api/test/
- Frontend: pytest with pytest-asyncio, pytest-mock
- Test location: frontend/tests/
- Coverage: maintain reports

## Performance
- Database indexing on frequently queried fields
- Pagination for large datasets
- Lazy loading for frontend components
- Caching for static data (countries, years)
- Query optimization

## Memory Bank Protocol
End of EVERY task:
- Update activeContext.md (current work)
- Update progress.md (completed/pending)

## Reference Examples
- Well-structured backend: config_api/, stamps_api/
- Test base: common/test/abstract_api_unit_test.py
- API patterns: common/api/messages.py

## Git Workflow
- Feature branches
- Conventional commits
- PR workflow with review
- Squash before merge