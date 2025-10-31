# Config API Documentation

Welcome to the API documentation for the Config resource. This document provides detailed information about the RESTful endpoints for managing the application's configuration settings.

The Config API provides a simple key-value store for application-wide settings, allowing for dynamic configuration without code changes.

## Resource URL

The base URL for all version 1 endpoints for this resource is:

`/stamps_server/api/v1/config/`

## Authentication

All endpoints are protected and require authentication via an API key or a password hash provided in the request headers. Please refer to the main `readme_api.md` for detailed authentication instructions.

---

## Model Description

The `Config` model represents a single configuration setting.

| Field | Type | Description |
| :--- | :--- | :--- |
| `id` | Integer | The unique identifier for the configuration entry. |
| `user` | Foreign Key | A reference to the `UserConfig` who owns this configuration entry. |
| `property` | String | The name of the configuration property (the key). This must be unique. |
| `value` | String | The value associated with the property. |

---

## API Endpoints

### `GET /config/`

Retrieves a list of all configuration key-value pairs.

*   **Summary:** List All Configuration Entries
*   **Success Response (200 OK):**
    A JSON array of configuration objects.
    ```json
    [
      {
        "id": 1,
        "user": 2,
        "property": "site_name",
        "value": "Stamps Web App"
      },
      {
        "id": 2,
        "user": 1,
        "property": "maintenance_mode",
        "value": "false"
      }
    ]
    ```
*   **Error Responses:**
    *   **403 Forbidden:** If the API key is invalid or missing.

### `POST /config/`

Creates a new configuration key-value pair.

*   **Summary:** Create a Configuration Entry
*   **Request Body:**
    A JSON object representing the new configuration entry.
    ```json
    {
      "user": 1,
      "property": "theme",
      "value": "dark"
    }
    ```
*   **Success Response (201 Created):**
    The full, newly created configuration object.
    ```json
    {
      "id": 3,
      "user": 1,
      "property": "theme",
      "value": "dark"
    }
    ```
*   **Error Responses:**
    *   **400 Bad Request:** If the request body is invalid (e.g., missing fields, or the `property` already exists).
    *   **403 Forbidden:** If the API key is invalid or missing.

### `GET /config/{id}/`

Retrieves a single, specific configuration entry by its unique ID.

*   **Summary:** Retrieve a Configuration Entry by ID
*   **URL Parameter:** `id` (integer, required) - The unique ID of the configuration entry.
*   **Success Response (200 OK):**
    The requested configuration object.
    ```json
    {
        "id": 1,
        "property": "site_name",
        "value": "Stamps Web App"
    }
    ```
*   **Error Responses:**
    *   **403 Forbidden:** If the API key is invalid or missing.
    *   **404 Not Found:** If no configuration entry with the given ID exists.

### `PUT /config/{id}/`

Updates an existing configuration entry. This method supports partial updates.

*   **Summary:** Update a Configuration Entry
*   **URL Parameter:** `id` (integer, required) - The unique ID of the configuration entry to update.
*   **Request Body:**
    A JSON object containing the fields to be updated. You can update the `property`, the `value`, or both.
    ```json
    {
      "user": 1,
      "value": "light"
    }
    ```
*   **Success Response (200 OK):**
    The full, updated configuration object.
    ```json
    {
        "id": 3,
        "user": 1,
        "property": "theme",
        "value": "light"
    }
    ```
*   **Error Responses:**
    *   **400 Bad Request:** If the request body contains invalid data (e.g., a duplicate `property` name).
    *   **403 Forbidden:** If the API key is invalid or missing.
    *   **404 Not Found:** If no configuration entry with the given ID exists.

### `DELETE /config/{id}/`

Permanently deletes a configuration entry.

*   **Summary:** Delete a Configuration Entry
*   **URL Parameter:** `id` (integer, required) - The ID of the configuration entry to delete.
*   **Success Response (200 OK):**
    A confirmation message indicating successful deletion.
    ```json
    {
        "message": "Config with id 1 has been deleted successfully."
    }
    ```
*   **Error Responses:**
    *   **403 Forbidden:** If the API key is invalid or missing.
    *   **404 Not Found:** If no configuration entry with the given ID exists.