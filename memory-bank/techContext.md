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