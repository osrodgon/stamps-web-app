# Stamps Web App

A modern, full-stack web application for managing and cataloging stamp collections. This project provides a comprehensive solution for philatelists to organize their collections, track individual stamps, and manage detailed information about issues, print types, and more.

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.13+ (for local development)

### Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd stamps-web-app
   ```

2. **Set up environment variables**
   ```bash
   cp backend/.env.example backend/.env
   cp frontend/.env.example frontend/.env
   # Edit the .env files with your configuration
   ```

3. **Start the development environment**
   ```bash
   # Start both backend and frontend in development mode
   docker-compose -f backend/docker-compose.dev.yml -f frontend/docker-compose.dev.yml up
   
   # Or start them separately
   docker-compose -f backend/docker-compose.dev.yml up -d
   docker-compose -f frontend/docker-compose.dev.yml up -d
   ```

4. **Access the application**
   - Frontend: http://localhost:8080
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/stamps-backend/api/v1/swagger/

### Production Deployment

```bash
# Build and start production containers
docker-compose -f backend/docker-compose.prod.yml -f frontend/docker-compose.prod.yml up -d
```

## 📋 Project Structure

```
stamps-web-app/
├── backend/                   # Django REST API backend
│   ├── _backend/              # Django project configuration
│   ├── stamps_api/            # Master stamp catalog management
│   ├── issues_api/            # Stamp issue management
│   ├── collections_api/       # User collection management
│   ├── collection_items_api/  # Individual stamp items in collections
│   ├── config_api/            # System configuration
│   ├── users_api/             # User management and authentication
│   ├── years_api/             # Year reference data
│   ├── colors_api/            # Color reference data
│   ├── countries_api/         # Country reference data
│   ├── stamp_types_api/       # Stamp type reference data
│   ├── print_types_api/       # Print type reference data
│   ├── locations_api/         # Storage location management
│   ├── condition_types_api/   # Condition type reference data
│   ├── health_api/            # System health checks
│   ├── common/                # Shared utilities and middleware
│   ├── resources/             # Static resources and data files
│   └── manage.py              # Django management script
├── frontend/                   # NiceGUI frontend application
│   ├── main.py                # Application entry point
│   ├── pages/                 # Page components
│   ├── components/            # Reusable UI components
│   ├── services/              # API service layer
│   ├── assets/                # Static assets (images, styles)
│   ├── core/                  # Core utilities and configuration
│   └── settings.py            # Application settings
├── logs/                      # Application logs
└── README.md                  # This file
```

## 🏗️ Architecture

### Backend (Django REST Framework)

The backend is built with Django and Django REST Framework, providing a robust API for managing stamp collections. Key features include:

- **RESTful API design** with comprehensive documentation
- **Authentication and authorization** using JWT tokens and API keys
- **Database management** with PostgreSQL support
- **Reference data management** for stamps, issues, colors, countries, etc.
- **Collection management** for user-specific stamp collections
- **Health monitoring** endpoints for system status

### Frontend (NiceGUI)

The frontend uses NiceGUI to create a modern, responsive web interface:

- **Modern UI/UX** with responsive design
- **Authentication flow** with login/logout functionality
- **Collection management** interface for users
- **Admin interface** for managing the master stamp catalog
- **Multi-language support** (Spanish and English)
- **Static file serving** for images and assets

## 📊 Data Model

The application manages several key entities:

### Core Entities

- **Issues**: Stamp issues with metadata (year, date, name, description, etc.)
- **Stamps**: Individual stamps within issues (face value, colors, market value, etc.)
- **Collections**: User-specific collections of stamps
- **Collection Items**: Individual stamps within user collections

### Reference Data

- **Years**: Year reference for issues
- **Countries**: Country reference for issues
- **Colors**: Color reference for stamps
- **Stamp Types**: Type classification for stamps
- **Print Types**: Printing method reference
- **Locations**: Storage location reference
- **Condition Types**: Condition reference for collection items

## 🔧 Configuration

### Environment Variables

#### Backend
```bash
# Database
POSTGRES_DB=stamps_db
POSTGRES_USER=stamps_user
POSTGRES_PASSWORD=your_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Django
SECRET_KEY=your_secret_key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=http://localhost:8000

# API
API_MASTER_KEY=your_master_api_key
```

#### Frontend
```bash
# Application
APP_NAME=Stamps App
LOG_LEVEL=DEBUG
DEFAULT_LANGUAGE=es

# Backend Connection
BACKEND_HOST=localhost
BACKEND_PORT=8000
API_MASTER_KEY=your_master_api_key

# Authentication
APP_STORAGE_SECRET=your_storage_secret
```

## 🧪 Testing

### Backend Tests
```bash
# Run backend tests
cd backend
python -m pytest

# Run with coverage
python -m pytest --cov=.
```

### Frontend Tests
```bash
# Run frontend tests
cd frontend
python -m pytest

# Run with coverage
python -m pytest --cov=.
```

## Testing everything
```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=.
```

The project is configured to use `pytest` for running unit and integration tests.

```bash
# Run all frontend tests
python -m pytest
```

## 📚 API Documentation

The API is documented using Swagger/OpenAPI. Access the documentation at:

- **Development**: http://localhost:8000/stamps-backend/api/v1/swagger/
- **Production**: http://your-domain.com/stamps-backend/api/v1/swagger/

### Key Endpoints

- **Authentication**: `/stamps-backend/api/v1/login/` - User login
- **Issues**: `/stamps-backend/api/v1/issues/` - Manage stamp issues
- **Stamps**: `/stamps-backend/api/v1/stamps/` - Manage individual stamps
- **Collections**: `/stamps-backend/api/v1/collections/` - Manage user collections
- **Collection Items**: `/stamps-backend/api/v1/collection_items/` - Manage collection items

## 🚀 Deployment

### Docker Compose

The project includes Docker Compose configurations for different environments:

- **Development**: `docker-compose.dev.yml` - With hot reload and development tools
- **Production**: `docker-compose.prod.yml` - Optimized for production deployment
- **Testing**: `docker-compose.test.yml` - For running tests

### Production Considerations

1. **Security**: Set strong secrets and disable debug mode
2. **Database**: Use a production PostgreSQL instance
3. **Static Files**: Configure proper static file serving
4. **SSL/TLS**: Enable HTTPS in production
5. **Monitoring**: Set up health checks and monitoring

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [Django](https://www.djangoproject.com/) and [Django REST Framework](https://www.django-rest-framework.org/)
- Frontend powered by [NiceGUI](https://nicegui.io/)
- Database management with [PostgreSQL](https://www.postgresql.org/)

## 🔗 Links

- [Backend Documentation](backend/README.md)
- [Frontend Documentation](frontend/README.md)
- [API Documentation](http://localhost:8000/stamps-backend/api/v1/swagger/)

---

**Note**: This is a philatelic collection management application designed for stamp collectors and enthusiasts.