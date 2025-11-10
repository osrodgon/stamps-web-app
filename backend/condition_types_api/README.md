# Condition Types API Documentation

Welcome to the API documentation for the Condition Types resource. This document provides detailed information about the RESTful endpoints for managing the various condition types that can be assigned to stamps in a collection.

The Condition Types API is a simple lookup table that allows for creating, viewing, updating, and deleting entries representing different stamp conditions (e.g., Mint, Used, Damaged).

## Resource URL

The base URL for all version 1 endpoints for this resource is:

`/stamps_server/api/v1/condition_types/`

## Authentication

All endpoints are protected and require authentication via an API key or a password hash provided in the request headers. Please refer to the main `readme_api.md` for detailed authentication instructions.

---

## Model Description

The `ConditionType` model represents a specific condition that a stamp can have.

| Field | Type | Description |
| :--- | :--- | :--- |
| `id` | Integer | The unique identifier for the condition type. |
| `name` | String | The name of the condition type (e.g., "Mint Never Hinged", "Used (Fine)"). |

---

## API Endpoints

### `GET /condition_types/`

Retrieves a list of all available condition types.

*   **Summary:** List All Condition Types
*   **Success Response (200 OK):**
    A JSON array of condition type objects.
    ```json
    [
      {
        "id": 1,
        "name": "Mint Never Hinged (MNH)"
      },
      {
        "id": 2,
        "name": "Used (Fine)"
      }
    ]
    ```
*   **Error Responses:**
    *   **403 Forbidden:** If the API key is invalid or missing.

### `POST /condition_types/`

Creates a new condition type.

*   **Summary:** Create a Condition Type
*   **Request Body:**
    A JSON object representing the new condition type.
    ```json
    {
      "name": "Damaged"
    }
    ```
*   **Success Response (201 Created):**
    The full, newly created condition type object.
    ```json
    {
      "id": 3,
      "name": "Damaged"
    }
    ```
*   **Error Responses:**
    *   **400 Bad Request:** If the request body is invalid (e.g., missing `name` field, or the name already exists).
    *   **403 Forbidden:** If the API key is invalid or missing.

### `GET /condition_types/{id}/`

Retrieves a single, specific condition type by its unique ID.

*   **Summary:** Retrieve a Condition Type by ID
*   **URL Parameter:** `id` (integer, required) - The unique ID of the condition type.
*   **Success Response (200 OK):**
    The requested condition type object.
    ```json
    {
        "id": 1,
        "name": "Mint Never Hinged (MNH)"
    }
    ```
*   **Error Responses:**
    *   **403 Forbidden:** If the API key is invalid or missing.
    *   **404 Not Found:** If no condition type with the given ID exists.

### `PUT /condition_types/{id}/`

Updates an existing condition type. This method supports partial updates, so you only need to provide the fields you want to change.

*   **Summary:** Update a Condition Type
*   **URL Parameter:** `id` (integer, required) - The unique ID of the condition type to update.
*   **Request Body:**
    A JSON object containing the fields to be updated.
    ```json
    {
      "name": "Mint Hinged (MH)"
    }
    ```
*   **Success Response (200 OK):**
    The full, updated condition type object.
    ```json
    {
        "id": 1,
        "name": "Mint Hinged (MH)"
    }
    ```
*   **Error Responses:**
    *   **400 Bad Request:** If the request body contains invalid data (e.g., a duplicate `name`).
    *   **403 Forbidden:** If the API key is invalid or missing.
    *   **404 Not Found:** If no condition type with the given ID exists.

### `DELETE /condition_types/{id}/`

Permanently deletes a condition type.

*   **Summary:** Delete a Condition Type
*   **URL Parameter:** `id` (integer, required) - The ID of the condition type to delete.
*   **Success Response (200 OK):**
    A confirmation message indicating successful deletion.
    ```json
    {
        "message": "Condition type with id 1 has been deleted successfully."
    }
    ```
*   **Error Responses:**
    *   **403 Forbidden:** If the API key is invalid or missing.
    *   **404 Not Found:** If no condition type with the given ID exists.