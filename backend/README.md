# Stamps Web App Backend

This directory contains the Django backend for the Stamps Web App. It exposes a RESTful API for managing stamp collections, catalog data, and AI-powered data enrichment.

## Getting Started

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
2.  **Environment Variables**:
    Ensure you have a `.env` file configured with database credentials (`POSTGRES_DB`, `POSTGRES_USER`, etc.) and `GOOGLE_API_KEY` for AI features.
3.  **Run Migrations**:
    ```bash
    python manage.py migrate
    ```
4.  **Start Server**:
    ```bash
    python manage.py runserver
    ```

## Application Modules

The project is modularized into several Django apps. Please refer to the README files in each app folder for specific documentation.

*   [**Collections API**](collections_api/README.md) - Manages user collections.
*   [**Collection Items API**](collection_items_api/README.md) - Manages individual items within collections.
*   [**Colors API**](colors_api/README.md) - Master data for stamp colors.
*   [**Condition Types API**](condition_types_api/README.md) - Master data for stamp conditions.
*   [**Config API**](config_api/README.md) - System configuration endpoints.
*   [**Countries API**](countries_api/README.md) - Master data for countries.
*   [**Health API**](health_api/README.md) - System health check endpoints.
*   [**Issues API**](issues_api/README.md) - Master data for stamp issues (series).
*   [**Locations API**](locations_api/README.md) - Master data for storage locations.
*   [**Print Types API**](print_types_api/README.md) - Master data for printing methods.
*   [**Stamp Types API**](stamp_types_api/README.md) - Master data for types of stamps.
*   [**Stamps API**](stamps_api/README.md) - Master data for individual stamps.
*   [**Users API**](users_api/README.md) - User management.
*   [**Years API**](years_api/README.md) - Master data for years.

## Database Model

![Database Model](resources/stamps-db-model.png)

## API Documentation

Interactive API documentation is available when the server is running:
*   **Swagger UI**: `/api/v1/swagger/`
*   **ReDoc**: `/api/v1/redoc/`

## Testing

The project is configured to use `pytest` for running unit and integration tests.

```bash
# Run all backend tests
python -m pytest
```
