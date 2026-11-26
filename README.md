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

### Dev container

The dev container joins the `stamps-network` Docker network, so anything started with
`stamps.sh` is reachable by service name (`db`, `stamps-backend`, `stamps-frontend`),
never via `localhost`.

It also mounts the **host** Docker socket (the `docker-outside-of-docker` feature), so
`stamps.sh` runs unchanged from inside the container:

```bash
./stamps.sh dev start stamps-backend
./stamps.sh test run
```

Consequences worth knowing:

- Containers started that way are **siblings** on the host, not children of the dev
  container. Published ports land on the host, so `localhost:8000` works from your
  machine's browser but not from inside the dev container.
- A bind mount declared in a compose file resolves against **host** paths. Keep the
  workspace at the same absolute path on host and container (the VS Code default).
- `docker` inside the container is root on the host. Fine on a personal machine, not
  on a shared one.

### Production Deployment

```bash
# Build and start production containers
docker-compose -f backend/docker-compose.prod.yml -f frontend/docker-compose.prod.yml up -d
```

### DataDesk (internal DB maintenance)

DataDesk is a staff-only Django app mounted at `/datadesk/`. It is **not** part of the
public API: nothing lives under `/api/v1/`, it has no DRF exposure and it is not in the
OpenAPI schema. It is off unless `DATADESK_ENABLED=True` in `backend/.env`.

Create the account it uses — staff, not necessarily a superuser:

```bash
docker compose -f backend/docker-compose.yml -f backend/docker-compose.dev.yml \
  exec stamps-backend python manage.py createsuperuser

# or a plain staff user
docker compose -f backend/docker-compose.yml -f backend/docker-compose.dev.yml \
  exec stamps-backend python manage.py shell -c \
  "from django.contrib.auth.models import User; User.objects.create_user('datadesk', password='<password>', is_staff=True)"
```

Log in at http://localhost:8000/datadesk/. Failed attempts are counted per username and
IP in `backend/.cache/` (shared by the gunicorn workers): the sixth failure inside five
minutes answers 429 with `Retry-After`.

Set `DATADESK_TLS=1` in the deployment environment when nginx terminates TLS in front of
Django. It only turns on `Secure` cookies and `SECURE_PROXY_SSL_HEADER`; the code path is
the same locally and on the server.

Stamp pictures are read from disk, not from the database: `Stamp.image` is empty and the
files live with the frontend, one `.webp` per FESOFI code under `<year>/<code>.webp`.
`DATADESK_STAMP_IMAGES` points at that tree. In development
`backend/docker-compose.dev.yml` mounts `../frontend/assets/stamps` read-only at
`/srv/stamp-images`. In production the mount is **not** part of this repository: the
deployment has a single compose file with the three containers (db, backend and
frontend) and only it knows where the pictures live, so it mounts the folder read-only
and sets `DATADESK_STAMP_IMAGES` to that path. A path that does not exist — or does not
exist yet — is not an error: the grid falls back to `no_stamp.webp` and the "without
image" queue counts everything. The listing is cached for a minute, so dropping a new
file on the server shows up without a restart or a rebuild.

Restricting the app by IP is done at the proxy, not in Django:

```nginx
location /datadesk/ {
    allow 203.0.113.10;
    deny all;
    proxy_pass http://stamps-backend:8000;
}
```

#### The keyboard

DataDesk is meant to be driven without the mouse, and each screen says under its
grid what it understands:

| Key | Where | What it does |
| --- | --- | --- |
| `/` | workbench, lookup table | focuses the search box |
| `j` / `k` | workbench, lookup table | moves the selection down / up |
| `Enter` | workbench | opens the selected series |
| `N` | workbench | starts a new series |
| `Shift+Enter` | workspace | commits the pending changes / creates the series |
| `Ctrl+Enter` | workspace | commits the change set |
| `Ctrl+D` | new series | duplicates the row under the cursor |
| `Ctrl+Z` / `Ctrl+Shift+Z` | workspace | undo / redo |
| `Esc` | everywhere | closes a dialog, blurs a field, leaves the workspace |

#### Before a large commit

A change set of more than twenty edits offers **Back up first** in the review
panel; it runs the existing command with a timestamped name and never blocks the
commit if the dump fails. From a shell, the same thing:

```bash
docker compose -f backend/docker-compose.yml -f backend/docker-compose.dev.yml \
  exec stamps-backend python manage.py stamps_db_backup datadesk-2026-11-19 --mode=stamps
```

The file lands in `backend/backups/` as `<name>__stamps.json` and comes back with
`stamps_db_restore`.

#### What a revert cannot undo

The activity screen undoes a whole commit in one transaction, including recreating
a deleted series and its stamps with their original ids and colours. What it
cannot give back is the `CollectionItem` rows that the cascade deleted with them:
the catalogue comes back, who owned those stamps does not. The confirmation says
so before the button is pressed.

#### Turning it off

`DATADESK_ENABLED=False` (the default) unmounts the URL pattern: `/datadesk/`
answers 404 and nothing else in the app changes. The audit trail lives in the
`datadesk_datadeskchange` table and stays where it is; keep it, it is the history
of what the maintenance did.

The interface is translated in English and Spanish. Catalogs live in
`backend/datadesk/locale/`; after editing a `.po`, rebuild the `.mo` files without
needing `gettext` installed. The compiled `.mo` files are versioned on purpose
(`.gitignore` has an exception for them): CI runs no `gettext` and the test suite
checks that they match their sources. To recompile them:

```bash
docker compose -f backend/docker-compose.yml -f backend/docker-compose.dev.yml \
  exec stamps-backend python manage.py datadesk_make_messages

# in CI: fail when a .po changed and its .mo was not rebuilt
... python manage.py datadesk_make_messages --check
```

The frontend translations (`frontend/assets/locales/*.json`) belong to the public
app and are never touched by DataDesk.

### AI API (series research)

`POST /stamps-backend/api/v1/issues/extraction/` researches one series: it finds it in
the **Fesofi** catalogue, reads its facts from the catalogue API (codes, face value,
print run, colour, perforation), prices its stamps in **filatelia.online** and in an
allowed-site search (opening the TodoColeccion listing when the snippet has no
condition), and has the LLM write the text from those facts. The LLM is a normaliser,
never a source.

Every price travels with the page that supports it (`observations`), and the value of
a stamp is a **trimmed mean** per condition with a minimum of three prices, in euros
only. What no source supports is `null` and appears in `gaps`; `partial: true` means
the request ran out of its budget and asking again is cheap.

It needs `OPENCODE_API_KEY` and `OPENCODE_MODEL` (paid Console models: the free ones
only work from inside opencode), plus `SERPER_API_KEY` for the price search. Every
outbound call goes through one allowlist and cache (`AI_SOURCE_*`), and one request is
capped by `AI_BUDGET_SECONDS`.

The endpoint prices one series. To fill the database:

```bash
docker compose -f backend/docker-compose.yml -f backend/docker-compose.dev.yml \
  exec stamps-backend python manage.py ai_prices_backfill --limit 10 --dry-run
```

It stores `SourceObservation` rows attached to the real stamp, deduplicated by
`raw_hash`, so running it twice does not duplicate the evidence. Module documentation:
`backend/ai_api/README.md`; the decisions and what each source answered:
`memory-bank/ai-api-plan.md` and `memory-bank/ai-sources-spike.md`.

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
|   ├── ai_api/                # AI series research (catalogue + prices)
|   ├── artists_api/           # Artists references (engravers)
|   ├── printers_api/          # Printers references (publishers)
|   ├── paper_types_api/       # Paper type reference data
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
- **Artists**: Artists (engravers) reference
- **Printers**: Printers (publishers) reference
- **Paper Types**: Paper type reference for stamps
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

# Gemini API Key
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL_NAME=your_gemini_model_name


# Groq API Key
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL_NAME=your_groq_model_name

# SERPER API Key
SERPER_API_KEY=your_serper_api_key
SERPER_URL=your_serper_url

# LLM Provider Selection
LLM_PROVIDER=llm_provider_to_use

# LLM Batch Size
LLM_BATCH_SIZE=batch_size
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

The API is documented using Swagger/OpenAPI. Access the documentation at (the application must be deployed in your local environment):

- **Development**: http://localhost:8000/stamps-backend/api/v1/swagger/

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

---

**Note**: This is a philatelic collection management application designed for stamp collectors and enthusiasts.