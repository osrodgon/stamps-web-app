# Locations API Documentation

Welcome to the API documentation for the Locations resource. This document provides detailed information about the RESTful endpoints for managing the physical or logical locations where stamps are stored.

The Locations API is a simple lookup table that allows for creating, viewing, updating, and deleting location entries (e.g., "Main Album", "Stockbook A", "Trade Binder").

## Resource URL

The base URL for all version 1 endpoints for this resource is:

`/stamps_server/api/v1/locations/`

## Authentication

All endpoints are protected and require authentication via an API key or a password hash provided in the request headers. Please refer to the main `readme_api.md` for detailed authentication instructions.

---

## Model Description

The `Location` model represents a place where a stamp can be stored.

| Field | Type | Description |
| :--- | :--- | :--- |
| `id` | Integer | The unique identifier for the location. |
| `name` | String | The name of the location (e.g., "Main Album"). |

---

## API Endpoints

### `GET /locations/`

Retrieves a list of all available locations.

*   **Summary:** List All Locations
*   **Success Response (200 OK):**
    A JSON array of location objects.
    ```json
    [
      {
        "id": 1,
        "name": "Main Album"
      },
      {
        "id": 2,
        "name": "Stockbook A"
      }
    ]
    ```
*   **Error Responses:**
    *   **403 Forbidden:** If the API key is invalid or missing.

### `POST /locations/`

Creates a new location.

*   **Summary:** Create a Location
*   **Request Body:**
    A JSON object representing the new location.
    ```json
    {
      "name": "Trade Binder"
    }
    ```
*   **Success Response (201 Created):**
    The full, newly created location object.
    ```json
    {
      "id": 3,
      "name": "Trade Binder"
    }
    ```
*   **Error Responses:**
    *   **400 Bad Request:** If the request body is invalid (e.g., missing `name` field, or the name already exists).
    *   **403 Forbidden:** If the API key is invalid or missing.

### `GET /locations/{id}/`

Retrieves a single, specific location by its unique ID.

*   **Summary:** Retrieve a Location by ID
*   **URL Parameter:** `id` (integer, required) - The unique ID of the location.
*   **Success Response (200 OK):**
    The requested location object.
    ```json
    {
        "id": 1,
        "name": "Main Album"
    }
    ```
*   **Error Responses:**
    *   **403 Forbidden:** If the API key is invalid or missing.
    *   **404 Not Found:** If no location with the given ID exists.

### `PUT /locations/{id}/`

Updates an existing location. This method supports partial updates, so you only need to provide the fields you want to change.

*   **Summary:** Update a Location
*   **URL Parameter:** `id` (integer, required) - The unique ID of the location to update.
*   **Request Body:**
    A JSON object containing the fields to be updated.
    ```json
    {
      "name": "Primary Album"
    }
    ```
*   **Success Response (200 OK):**
    The full, updated location object.
    ```json
    {
        "id": 1,
        "name": "Primary Album"
    }
    ```
*   **Error Responses:**
    *   **400 Bad Request:** If the request body contains invalid data (e.g., a duplicate `name`).
    *   **403 Forbidden:** If the API key is invalid or missing.
    *   **404 Not Found:** If no location with the given ID exists.

### `DELETE /locations/{id}/`

Permanently deletes a location.

*   **Summary:** Delete a Location
*   **URL Parameter:** `id` (integer, required) - The ID of the location to delete.
*   **Success Response (200 OK):**
    A confirmation message indicating successful deletion.
    ```json
    {
        "message": "Location with id 1 has been deleted successfully."
    }
    ```
*   **Error Responses:**
    *   **403 Forbidden:** If the API key is invalid or missing.
    *   **404 Not Found:** If no location with the given ID exists.