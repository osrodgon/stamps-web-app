# Colors API Documentation

Welcome to the API documentation for the Colors resource. This document provides detailed information about the RESTful endpoints for managing the colors used to describe stamps.

The Colors API is a simple lookup table that allows for creating, viewing,updating, and deleting color entries.

## Resource URL

The base URL for all version 1 endpoints for this resource is:

`/stamps_server/api/v1/colors/`

## Authentication

All endpoints are protected and require authentication via an API key or a password hash provided in the request headers. Please refer to the main `readme_api.md` for detailed authentication instructions.

---

## Model Description

The `Color` model represents a color that can be associated with a stamp.

| Field | Type | Description |
| :--- | :--- | :--- |
| `id` | Integer | The unique identifier for the color. |
| `name` | String | The name of the color (e.g., "Red", "Blue", "Multicolor"). |

---

## API Endpoints

### `GET /colors/`

Retrieves a list of all available colors.

*   **Summary:** List All Colors
*   **Success Response (200 OK):**
    A JSON array of color objects.
    ```json
    [
      {
        "id": 1,
        "name": "Red"
      },
      {
        "id": 2,
        "name": "Blue"
      }
    ]
    ```
*   **Error Responses:**
    *   **403 Forbidden:** If the API key is invalid or missing.

### `POST /colors/`

Creates a new color.

*   **Summary:** Create a Color
*   **Request Body:**
    A JSON object representing the new color.
    ```json
    {
      "name": "Green"
    }
    ```
*   **Success Response (201 Created):**
    The full, newly created color object.
    ```json
    {
      "id": 3,
      "name": "Green"
    }
    ```
*   **Error Responses:**
    *   **400 Bad Request:** If the request body is invalid (e.g., missing `name` field, or the name already exists).
    *   **403 Forbidden:** If the API key is invalid or missing.

### `GET /colors/{id}/`

Retrieves a single, specific color by its unique ID.

*   **Summary:** Retrieve a Color by ID
*   **URL Parameter:** `id` (integer, required) - The unique ID of the color.
*   **Success Response (200 OK):**
    The requested color object.
    ```json
    {
        "id": 1,
        "name": "Red"
    }
    ```
*   **Error Responses:**
    *   **403 Forbidden:** If the API key is invalid or missing.
    *   **404 Not Found:** If no color with the given ID exists.

### `PUT /colors/{id}/`

Updates an existing color. This method supports partial updates, so you only need to provide the fields you want to change.

*   **Summary:** Update a Color
*   **URL Parameter:** `id` (integer, required) - The unique ID of the color to update.
*   **Request Body:**
    A JSON object containing the fields to be updated.
    ```json
    {
      "name": "Dark Red"
    }
    ```
*   **Success Response (200 OK):**
    The full, updated color object.
    ```json
    {
        "id": 1,
        "name": "Dark Red"
    }
    ```
*   **Error Responses:**
    *   **400 Bad Request:** If the request body contains invalid data (e.g., a duplicate `name`).
    *   **403 Forbidden:** If the API key is invalid or missing.
    *   **404 Not Found:** If no color with the given ID exists.

### `DELETE /colors/{id}/`

Permanently deletes a color.

*   **Summary:** Delete a Color
*   **URL Parameter:** `id` (integer, required) - The ID of the color to delete.
*   **Success Response (200 OK):**
    A confirmation message indicating successful deletion.
    ```json
    {
        "message": "Color with id 1 has been deleted successfully."
    }
    ```
*   **Error Responses:**
    *   **403 Forbidden:** If the API key is invalid or missing.
    *   **404 Not Found:** If no color with the given ID exists.