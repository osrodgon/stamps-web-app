# OpenCode Rules - Stamps Web App

## Top 5 Must-Follow Rules
1. Be concise - no explanations unless asked
2. Type hints on ALL function signatures
3. Business logic in services.py, NOT views
4. Update memory-bank/ after EVERY task
5. Follow file structure: backend/{module}_api/api/views/, serializers/

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