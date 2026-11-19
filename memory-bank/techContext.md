# Stamps Web App - Technical Context

## Architecture Overview

### Frontend Architecture (NiceGUI)
- **Framework**: NiceGUI 3.3.0 - Python-based web framework for building modern web applications
- **Architecture Pattern**: Component-based with service layer separation
- **State Management**: Session-based using `app.storage.user` for user-specific data
- **Internationalization**: JSON-based translation system with support for English and Spanish
- **Testing**: NiceGUI testing plugin for component and integration testing

### Backend Architecture (Django/DRF)
- **Framework**: Django 6.0 with Django REST Framework 3.16.1
- **Database**: PostgreSQL with Django ORM for data persistence
- **Authentication**: JWT tokens + API Key authentication for secure access
- **Documentation**: drf-spectacular for OpenAPI specification generation
- **Testing**: pytest with Django test framework for comprehensive testing

## Key Technical Decisions

### Component Architecture
- **Base Classes**: 
  - `BaseUI`: Base class for all UI components
  - `BasePage`: Base class for all pages
  - `BaseService`: Base class for all services
- **Composition over Inheritance**: Prefer composition for better flexibility and maintainability
- **Dependency Injection**: Services are injected into components for better testability

### NiceGUI Specific Nuances
- **Component Lifecycle**: Understanding of NiceGUI's reactive system and component lifecycle
- **Event Handling**: Proper handling of user interactions and form submissions
- **State Management**: Using `app.storage.user` for session-based state persistence
- **Error Handling**: Implementing proper error boundaries and user feedback
- **Performance**: Lazy loading of components and efficient data fetching patterns

### Django Best Practices
- **REST API Design**: Following REST conventions with proper HTTP methods and status codes
- **Serializer Patterns**: Using DRF serializers for data validation and serialization
- **Permission System**: Custom permissions for role-based access control
- **Database Design**: Proper model relationships and indexing strategies
- **Security**: CSRF protection, input validation, and secure session management

## File Organization Patterns

### Frontend Structure
```
frontend/
├── pages/           # Page-specific components and logic
├── components/      # Reusable UI components organized by category
├── services/        # API communication and business logic
├── base/           # Base classes and common utilities
├── core/           # Core functionality (translations, URLs, logging)
└── assets/         # Static assets including translations
```

### Backend Structure
```
backend/
├── {module}_api/   # Feature-specific Django apps
│   ├── models.py   # Database models
│   ├── api/        # API views, serializers, URLs
│   └── test/       # Unit and integration tests
├── common/         # Shared utilities and base classes
└── _backend/       # Django project configuration
```

## Development Environment

### Docker Configuration
- **Development**: Separate Docker Compose files for dev, prod, and test environments
- **Multi-stage Builds**: Optimized Dockerfiles for different deployment scenarios
- **Database**: PostgreSQL for production, SQLite for testing
- **Dev container = docker-outside-of-docker**: the devcontainer uses the **host**
  daemon (feature `docker-outside-of-docker`, which mounts `/var/run/docker.sock`
  as `/var/run/docker-host.sock`), so `stamps.sh` runs unchanged from inside it.
  Chosen over docker-in-docker: it shares the host image cache and the existing
  `stamps-network`, which is what `runArgs`/`initializeCommand` already rely on.
  Consequences: containers are **siblings** on the host (reach them by service
  name on `stamps-network`, never `localhost`; published ports land on the host),
  and bind mounts in compose files resolve against **host** paths.
  `devcontainer-lock.json` pins the feature digest — regenerate it on feature bumps.
  `stamps.sh`'s socket guard follows `DOCKER_HOST` (falling back to
  `/var/run/docker.sock`) and only re-execs through `sg docker` when the socket
  exists but is not writable. A nested engine is **not** installed: it cannot use
  overlayfs (the container root is already overlay), so it needs `vfs` and fails to
  pull images. If `docker` misbehaves after a rebuild, check `docker context ls` /
  `echo $DOCKER_HOST` before touching anything else.

### Testing Strategy
- **Backend**: pytest with Django test framework, fixtures for test data
- **Frontend**: NiceGUI testing plugin for component testing
- **Integration**: End-to-end tests for critical user workflows
- **Coverage**: Maintaining test coverage reports for quality assurance

## Security Considerations

### Authentication Flow
- JWT tokens for user authentication
- API Key authentication for service-to-service communication
- Secure session storage using `app.storage.user`
- Proper CSRF protection implementation

### Data Security
- Environment variables for sensitive configuration
- Database permissions and access control
- Input validation and sanitization on backend
- Secure API endpoints with proper permissions

## Performance Optimization

### Frontend Optimizations
- Lazy loading of components to reduce initial bundle size
- Efficient data fetching patterns with proper caching
- Image optimization for stamp collection photos
- State management to minimize unnecessary re-renders

### Backend Optimizations
- Database indexing for frequently queried fields
- Caching strategies for static data (countries, years, etc.)
- Pagination for large collections and stamp lists
- Query optimization and bulk operations where appropriate

## Internationalization Strategy

### Translation System
- JSON files in `assets/locales/` directory
- Support for English (en) and Spanish (es)
- Using `_()` function for translation calls
- Context-aware translation keys for better maintainability

### Implementation Details
- Translation keys follow descriptive naming patterns
- Grouping related translations for better organization
- Handling pluralization and gender appropriately
- Consistent translation key structure across the application

## API Design Patterns

### REST API Standards
- Consistent URL patterns: `/api/v1/{resource}/`
- Standard HTTP status codes for different scenarios
- Comprehensive API documentation with drf-spectacular
- Proper versioning strategy for future API changes

### Error Handling
- Standardized error response format
- Meaningful error messages for debugging
- Proper logging for error tracking and monitoring
- Graceful degradation for non-critical failures

## Development Workflow

### Git Workflow
- Feature branches for new development
- Pull request workflow with code review
- Conventional commit standards for better history
- Squash commits before merging to main branch

### Code Quality
- PEP 8 compliance with Black formatter (88 character limit)
- Type hints for better code documentation
- Comprehensive test coverage requirements
- Security vulnerability scanning and monitoring

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
