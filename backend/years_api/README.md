# Years API Documentation

Welcome to the API documentation for the Years resource. This document provides detailed information about the RESTful endpoints for managing the years associated with stamp issues.

The Years API is a simple lookup table that allows for creating, viewing, updating, and deleting year entries.

## Resource URL

The base URL for all version 1 endpoints for this resource is:

`/stamps_server/api/v1/years/`

## Authentication

All endpoints are protected and require authentication via an API key or a password hash provided in the request headers. Please refer to the main `readme_api.md` for detailed authentication instructions.

---

## Model Description

The `Year` model represents a year that can be associated with a stamp issue.

| Field | Type | Description |
| :--- | :--- | :--- |
| `id` | Integer | The unique identifier for the year. |
| `year` | Integer | The specific year value (e.g., 2023). |

---

## API Endpoints

### `GET /years/`

Retrieves a list of all available years.

*   **Summary:** List All Years
*   **Success Response (200 OK):**
    A JSON array of year objects.
    ```json
    [
      {
        "id": 1,
        "year": 2023
      },
      {
        "id": 2,
        "year": 2024
      }
    ]
    ```
*   **Error Responses:**
    *   **403 Forbidden:** If the API key is invalid or missing.

### `POST /years/`

Creates a new year.

*   **Summary:** Create a Year
*   **Request Body:**
    A JSON object representing the new year.
    ```json
    {
      "year": 2025
    }
    ```
*   **Success Response (201 Created):**
    The full, newly created year object.
    ```json
    {
      "id": 3,
      "year": 2025
    }
    ```
*   **Error Responses:**
    *   **400 Bad Request:** If the request body is invalid (e.g., missing `year` field, or the year already exists).
    *   **403 Forbidden:** If the API key is invalid or missing.

### `GET /years/{id}/`

Retrieves a single, specific year by its unique ID.

*   **Summary:** Retrieve a Year by ID
*   **URL Parameter:** `id` (integer, required) - The unique ID of the year.
*   **Success Response (200 OK):**
    The requested year object.
    ```json
    {
        "id": 1,
        "year": 2023
    }
    ```
*   **Error Responses:**
    *   **403 Forbidden:** If the API key is invalid or missing.
    *   **404 Not Found:** If no year with the given ID exists.

### `PUT /years/{id}/`

Updates an existing year. This method supports partial updates, so you only need to provide the fields you want to change.

*   **Summary:** Update a Year
*   **URL Parameter:** `id` (integer, required) - The unique ID of the year to update.
*   **Request Body:**
    A JSON object containing the fields to be updated.
    ```json
    {
      "year": 2022
    }
    ```
*   **Success Response (200 OK):**
    The full, updated year object.
    ```json
    {
        "id": 1,
        "year": 2022
    }
    ```
*   **Error Responses:**
    *   **400 Bad Request:** If the request body contains invalid data (e.g., a duplicate `year`).
    *   **403 Forbidden:** If the API key is invalid or missing.
    *   **404 Not Found:** If no year with the given ID exists.

### `DELETE /years/{id}/`

Permanently deletes a year.

*   **Summary:** Delete a Year
*   **URL Parameter:** `id` (integer, required) - The ID of the year to delete.
*   **Success Response (200 OK):**
    A confirmation message indicating successful deletion.
    ```json
    {
        "message": "Year with id 1 has been deleted successfully."
    }
    ```
*   **Error Responses:**
    *   **403 Forbidden:** If the API key is invalid or missing.
    *   **404 Not Found:** If no year with the given ID exists.