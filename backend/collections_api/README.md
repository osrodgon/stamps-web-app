# Collections API Documentation

Welcome to the API documentation for the Collections resource. This document provides detailed information about the RESTful endpoints for managing a user's personal stamp collections.

The Collections API allows users to create, view, update, and delete their stamp collections. Each collection is associated with a specific user.

## Resource URL

The base URL for all version 1 endpoints for this resource is:

`/stamps_server/api/v1/collections/`

## Authentication

All endpoints are protected and require authentication via an API key or a password hash provided in the request headers. Please refer to the main `readme_api.md` for detailed authentication instructions.

---

## Model Description

The `Collection` model represents a user's personal stamp collection.

| Field | Type | Description |
| :--- | :--- | :--- |
| `id` | Integer | The unique identifier for the collection. |
| `user` | Foreign Key | A reference to the `UserCollection` who owns this collection. |
| `name` | String | The name of the collection. |

---

## API Endpoints

### `GET /collections/`

Retrieves a list of all collections for the authenticated user.

*   **Summary:** List All Collections
*   **Success Response (200 OK):**
    A JSON array of collection objects. The `user` field is represented by the username string.
    ```json
    [
      {
        "id": 1,
        "user": "testuser",
        "name": "European Classics"
      },
      {
        "id": 2,
        "user": "testuser",
        "name": "North American Commemoratives"
      }
    ]
    ```
*   **Error Responses:**
    *   **403 Forbidden:** If the API key is invalid or missing.

### `POST /collections/`

Creates a new collection for the authenticated user.

*   **Summary:** Create a Collection
*   **Request Body:**
    A JSON object representing the new collection. The `user` field should be the integer ID of the user.
    ```json
    {
      "user": 1,
      "name": "American Commemoratives"
    }
    ```
*   **Success Response (201 Created):**
    The full, newly created collection object. The `user` field is represented by the username string.
    ```json
    {
      "id": 3,
      "user": "testuser",
      "name": "American Commemoratives"
    }
    ```
*   **Error Responses:**
    *   **400 Bad Request:** If the request body is invalid (e.g., missing required fields, invalid data types, or a collection with the same name already exists for the user).
    *   **403 Forbidden:** If the API key is invalid or missing.
    *   **404 Not Found:** If the user ID provided in the request body does not exist.

### `GET /collections/{id}/`

Retrieves a single collection by its ID.

*   **Summary:** Retrieve a Collection by ID
*   **URL Parameter:** `id` (integer, required) - The unique ID of the collection.
*   **Success Response (200 OK):**
    The requested collection object. The `user` field is represented by the username string.
    ```json
    {
      "id": 1,
      "user": "testuser",
      "name": "European Classics"
    }
    ```
*   **Error Responses:**
    *   **403 Forbidden:** If the API key is invalid or missing.
    *   **404 Not Found:** If no collection with the given ID exists.

### `PUT /collections/{id}/`

Updates an existing collection. This method supports partial updates, so you only need to provide the fields you want to change.

*   **Summary:** Update a Collection
*   **URL Parameter:** `id` (integer, required) - The unique ID of the collection to update.
*   **Request Body:**
    A JSON object containing the fields to be updated.
    ```json
    {
      "name": "Updated European Classics"
    }
    ```
*   **Success Response (200 OK):**
    The full, updated collection object.
    ```json
    {
      "id": 1,
      "user": "testuser",
      "name": "Updated European Classics"
    }
    ```
*   **Error Responses:**
    *   **400 Bad Request:** If the request body contains invalid data (e.g., trying to change the `user` or providing a duplicate `name`).
    *   **403 Forbidden:** If the API key is invalid or missing.
    *   **404 Not Found:** If no collection with the given ID exists.

### `DELETE /collections/{id}/`

Deletes a collection.

*   **Summary:** Delete a Collection
*   **URL Parameter:** `id` (integer, required) - The unique ID of the collection to delete.
*   **Success Response (200 OK):**
    A confirmation message indicating successful deletion.
    ```json
    {
        "message": "Collection with id 1 has been deleted successfully."
    }
    ```
*   **Error Responses:**
    *   **403 Forbidden:** If the API key is invalid or missing.
    *   **404 Not Found:** If no collection with the given ID exists.
