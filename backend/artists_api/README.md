# Artists API Documentation

Welcome to the API documentation for the Artists resource. This document provides detailed information about the RESTful endpoints for managing the artists used to describe stamps.

The Artists API is a simple lookup table that allows for creating, viewing, updating, and deleting artist entries.

## Resource URL

The base URL for all version 1 endpoints for this resource is:

`/stamps_server/api/v1/artists/`

## Authentication

All endpoints are protected and require authentication via an API key or a password hash provided in the request headers. Please refer to the main `readme_api.md` for detailed authentication instructions.

---

## Model Description

The `Artist` model represents an artist that can be associated with a stamp.

| Field | Type | Description |
| :--- | :--- | :--- |
| `id` | Integer | The unique identifier for the artist. |
| `name` | String | The name of the artist (e.g., "John Smith", "Jane Doe"). |

---

## API Endpoints

### `GET /artists/`

Retrieves a list of all available artists.

*   **Summary:** List All Artists
*   **Success Response (200 OK):**
    A JSON array of artist objects.
    ```json
    [
      {
        "id": 1,
        "name": "John Smith"
      },
      {
        "id": 2,
        "name": "Jane Doe"
      }
    ]
    ```
*   **Error Responses:**
    *   **403 Forbidden:** If the API key is invalid or missing.

### `POST /artists/`

Creates a new artist.

*   **Summary:** Create an Artist
*   **Request Body:**
    A JSON object representing the new artist.
    ```json
    {
      "name": "Bob Johnson"
    }
    ```
*   **Success Response (201 Created):**
    The full, newly created artist object.
    ```json
    {
      "id": 3,
      "name": "Bob Johnson"
    }
    ```
*   **Error Responses:**
    *   **400 Bad Request:** If the request body is invalid (e.g., missing `name` field, or the name already exists).
    *   **403 Forbidden:** If the API key is invalid or missing.

### `GET /artists/{id}/`

Retrieves a single, specific artist by its unique ID.

*   **Summary:** Retrieve an Artist by ID
*   **URL Parameter:** `id` (integer, required) - The unique ID of the artist.
*   **Success Response (200 OK):**
    The requested artist object.
    ```json
    {
        "id": 1,
        "name": "John Smith"
    }
    ```
*   **Error Responses:**
    *   **403 Forbidden:** If the API key is invalid or missing.
    *   **404 Not Found:** If no artist with the given ID exists.

### `PUT /artists/{id}/`

Updates an existing artist. This method supports partial updates, so you only need to provide the fields you want to change.

*   **Summary:** Update an Artist
*   **URL Parameter:** `id` (integer, required) - The unique ID of the artist to update.
*   **Request Body:**
    A JSON object containing the fields to be updated.
    ```json
    {
      "name": "John A. Smith"
    }
    ```
*   **Success Response (200 OK):**
    The full, updated artist object.
    ```json
    {
        "id": 1,
        "name": "John A. Smith"
    }
    ```
*   **Error Responses:**
    *   **400 Bad Request:** If the request body contains invalid data (e.g., a duplicate `name`).
    *   **403 Forbidden:** If the API key is invalid or missing.
    *   **404 Not Found:** If no artist with the given ID exists.

### `DELETE /artists/{id}/`

Permanently deletes an artist.

*   **Summary:** Delete an Artist
*   **URL Parameter:** `id` (integer, required) - The ID of the artist to delete.
*   **Success Response (200 OK):**
    A confirmation message indicating successful deletion.
    ```json
    {
        "message": "Artist with id 1 has been deleted successfully."
    }
    ```
*   **Error Responses:**
    *   **403 Forbidden:** If the API key is invalid or missing.
    *   **404 Not Found:** If no artist with the given ID exists.