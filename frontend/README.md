# Stamps Web App Frontend

This directory contains the NiceGUI frontend for the Stamps Web App. It provides a modern, responsive user interface for interacting with the backend API to manage stamp collections.

## Getting Started

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
2.  **Environment Variables**:
    Create a `.env` file from the `.env.example` template. This file configures the connection to the backend API.
    ```bash
    cp .env.example .env
    ```
3.  **Start Server**:
    ```bash
    python main.py
    ```

## Folder Structure

The frontend application is built with NiceGUI and follows a modular structure to keep the code organized and maintainable.

*   **`main.py`**: The main entry point for the NiceGUI application. It initializes the app and sets up global configurations.
*   **`pages/`**: Contains the different pages or views of the application (e.g., Login, Dashboard, Collection View). Each file in this directory typically represents a distinct URL route.
*   **`components/`**: Holds reusable UI components that are used across multiple pages, such as custom data tables, dialogs, or navigation bars.
*   **`services/`**: This layer is responsible for all communication with the backend REST API. It abstracts the HTTP requests (GET, POST, etc.) into clean, reusable functions.
*   **`core/`**: Contains core application logic, configuration loading, and shared utilities that don't fit into other categories.
*   **`assets/`**: Static assets like images, custom CSS stylesheets, and fonts are stored here.
*   **`settings.py`**: Defines and loads application settings, primarily from environment variables specified in the `.env` file.

## Testing

The project is configured to use `pytest` for running unit and integration tests.

```bash
# Run all frontend tests
python -m pytest
```

## Key Technologies

*   **NiceGUI**: The core framework used to build the web interface with Python.
*   **Quasar Framework**: The underlying Vue component framework that provides the UI elements for NiceGUI.
*   **httpx**: Used in the `services` layer for making asynchronous API calls to the Django backend.

---
*For backend documentation, please see the Backend README.*