# Paper Types API Documentation

Welcome to the API documentation for the Paper Types resource. This document provides detailed information about the RESTful endpoints for managing the types of paper used for stamps.

The Paper Types API is a simple lookup table that allows for creating, viewing, updating, and deleting paper type entries (e.g., "Wove", "Laid", "Granite").

## Resource URL

The base URL for all version 1 endpoints for this resource is:

`/stamps_server/api/v1/paper_types/`

## Authentication

All endpoints are protected and require authentication via an API key or a password hash provided in the request headers. Please refer to the main `readme_api.md` for detailed authentication instructions.

---

## Model Description

The `PaperType` model represents a type of paper that a stamp can be printed on.

| Field | Type | Description |
| :--- | :--- | :--- |
| `id` | Integer | The unique identifier for the paper type. |
| `name` | String | The name of the paper type (e.g., "Wove"). |

---

## API Endpoints

### `GET /paper_types/`

Retrieves a list of all available paper types.

*   **Summary:** List All Paper Types
*   **Success Response (200 OK):**
    A JSON array of paper type objects.
    ```json
    [
      {
        "id": 1,
        "name": "Wove"
      },
      {
        "id": 2,
        "name": "Laid"
      }
    ]
    ```
*   **Error Responses:**
    *   **403 Forbidden:** If the API key is invalid or missing.

### `POST /paper_types/`

Creates a new paper type.

*   **Summary:** Create a Paper Type
*   **Request Body:**
    A JSON object representing the new paper type.
    ```json
    {
      "name": "Granite"
    }
    ```
*   **Success Response (201 Created):**
    The full, newly created paper type object.
    ```json
    {
      "id": 3,
      "name": "Granite"
    }
    ```
*   **Error Responses:**
    *   **400 Bad Request:** If the request body is invalid (e.g., missing `name` field, or the name already exists).
    *   **403 Forbidden:** If the API key is invalid or missing.

### `GET /paper_types/{id}/`

Retrieves a single, specific paper type by its unique ID.

*   **Summary:** Retrieve a Paper Type by ID
*   **URL Parameter:** `id` (integer, required) - The unique ID of the paper type.
*   **Success Response (200 OK):**
    The requested paper type object.
    ```json
    {
        "id": 1,
        "name": "Wove"
    }
    ```
*   **Error Responses:**
    *   **403 Forbidden:** If the API key is invalid or missing.
    *   **404 Not Found:** If no paper type with the given ID exists.

### `PUT /paper_types/{id}/`

Updates an existing paper type. This method supports partial updates, so you only need to provide the fields you want to change.

*   **Summary:** Update a Paper Type
*   **URL Parameter:** `id` (integer, required) - The unique ID of the paper type to update.
*   **Request Body:**
    A JSON object containing the fields to be updated.
    ```json
    {
      "name": "Chalk-surfaced"
    }
    ```
*   **Success Response (200 OK):**
    The full, updated paper type object.
    ```json
    {
        "id": 4,
        "name": "Chalk-surfaced"
    }
    ```
*   **Error Responses:**
    *   **400 Bad Request:** If the request body contains invalid data (e.g., a duplicate `name`).
    *   **403 Forbidden:** If the API key is invalid or missing.
    *   **404 Not Found:** If no paper type with the given ID exists.

### `DELETE /paper_types/{id}/`

Permanently deletes a paper type.

*   **Summary:** Delete a Paper Type
*   **URL Parameter:** `id` (integer, required) - The ID of the paper type to delete.
*   **Success Response (200 OK):**
    A confirmation message indicating successful deletion.
    ```json
    {
        "message": "Paper type with id 1 has been deleted successfully."
    }
    ```
*   **Error Responses:**
    *   **403 Forbidden:** If the API key is invalid or missing.
    *   **404 Not Found:** If no paper type with the given ID exists.