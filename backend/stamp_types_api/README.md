# Stamp Types API Documentation

Welcome to the API documentation for the Stamp Types resource. This document provides detailed information about the RESTful endpoints for managing the types of stamps (e.g., "Definitive", "Commemorative").

The Stamp Types API is a simple lookup table that allows for creating, viewing, updating, and deleting stamp type entries.

## Resource URL

The base URL for all version 1 endpoints for this resource is:

`/stamps_server/api/v1/stamp_types/`

## Authentication

All endpoints are protected and require authentication via an API key or a password hash provided in the request headers. Please refer to the main `readme_api.md` for detailed authentication instructions.

---

## Model Description

The `StampType` model represents a category for a stamp or stamp issue.

| Field | Type | Description |
| :--- | :--- | :--- |
| `id` | Integer | The unique identifier for the stamp type. |
| `name` | String | The name of the stamp type (e.g., "Definitive"). |

---

## API Endpoints

### `GET /stamp_types/`

Retrieves a list of all available stamp types.

*   **Summary:** List All Stamp Types
*   **Success Response (200 OK):**
    A JSON array of stamp type objects.
    ```json
    [
      {
        "id": 1,
        "name": "Definitive"
      },
      {
        "id": 2,
        "name": "Commemorative"
      }
    ]
    ```
*   **Error Responses:**
    *   **403 Forbidden:** If the API key is invalid or missing.

### `POST /stamp_types/`

Creates a new stamp type.

*   **Summary:** Create a Stamp Type
*   **Request Body:**
    A JSON object representing the new stamp type.
    ```json
    {
      "name": "Airmail"
    }
    ```
*   **Success Response (201 Created):**
    The full, newly created stamp type object.
    ```json
    {
      "id": 3,
      "name": "Airmail"
    }
    ```
*   **Error Responses:**
    *   **400 Bad Request:** If the request body is invalid (e.g., missing `name` field, or the name already exists).
    *   **403 Forbidden:** If the API key is invalid or missing.

### `GET /stamp_types/{id}/`

Retrieves a single, specific stamp type by its unique ID.

*   **Summary:** Retrieve a Stamp Type by ID
*   **URL Parameter:** `id` (integer, required) - The unique ID of the stamp type.
*   **Success Response (200 OK):**
    The requested stamp type object.
    ```json
    {
        "id": 1,
        "name": "Definitive"
    }
    ```
*   **Error Responses:**
    *   **403 Forbidden:** If the API key is invalid or missing.
    *   **404 Not Found:** If no stamp type with the given ID exists.

### `PUT /stamp_types/{id}/`

Updates an existing stamp type. This method supports partial updates, so you only need to provide the fields you want to change.

*   **Summary:** Update a Stamp Type
*   **URL Parameter:** `id` (integer, required) - The unique ID of the stamp type to update.
*   **Request Body:**
    A JSON object containing the fields to be updated.
    ```json
    {
      "name": "Postage Due"
    }
    ```
*   **Success Response (200 OK):**
    The full, updated stamp type object.
    ```json
    {
        "id": 4,
        "name": "Postage Due"
    }
    ```
*   **Error Responses:**
    *   **400 Bad Request:** If the request body contains invalid data (e.g., a duplicate `name`).
    *   **403 Forbidden:** If the API key is invalid or missing.
    *   **404 Not Found:** If no stamp type with the given ID exists.

### `DELETE /stamp_types/{id}/`

Permanently deletes a stamp type.

*   **Summary:** Delete a Stamp Type
*   **URL Parameter:** `id` (integer, required) - The ID of the stamp type to delete.
*   **Success Response (200 OK):**
    A confirmation message indicating successful deletion.
    ```json
    {
        "message": "Stamp type with id 1 has been deleted successfully."
    }
    ```
*   **Error Responses:**
    *   **403 Forbidden:** If the API key is invalid or missing.
    *   **404 Not Found:** If no stamp type with the given ID exists.