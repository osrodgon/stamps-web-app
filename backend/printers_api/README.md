# Printers API Documentation

Welcome to the API documentation for the Printers resource. This document provides detailed information about the RESTful endpoints for managing the printers used to describe stamps.

The Printers API is a simple lookup table that allows for creating, viewing, updating, and deleting printer entries.

## Resource URL

The base URL for all version 1 endpoints for this resource is:

`/stamps_server/api/v1/printers/`

## Authentication

All endpoints are protected and require authentication via an API key or a password hash provided in the request headers. Please refer to the main `readme_api.md` for detailed authentication instructions.

---

## Model Description

The `Printer` model represents a printer that can be associated with a stamp.

| Field | Type | Description |
| :--- | :--- | :--- |
| `id` | Integer | The unique identifier for the printer. |
| `name` | String | The name of the printer (e.g., "British American Bank Note Company", "Canadian Bank Note Company"). |

---

## API Endpoints

### `GET /printers/`

Retrieves a list of all available printers.

*   **Summary:** List All Printers
*   **Success Response (200 OK):**
    A JSON array of printer objects.
    ```json
    [
      {
        "id": 1,
        "name": "British American Bank Note Company"
      },
      {
        "id": 2,
        "name": "Canadian Bank Note Company"
      }
    ]
    ```
*   **Error Responses:**
    *   **403 Forbidden:** If the API key is invalid or missing.

### `POST /printers/`

Creates a new printer.

*   **Summary:** Create a Printer
*   **Request Body:**
    A JSON object representing the new printer.
    ```json
    {
      "name": "American Bank Note Company"
    }
    ```
*   **Success Response (201 Created):**
    The full, newly created printer object.
    ```json
    {
      "id": 3,
      "name": "American Bank Note Company"
    }
    ```
*   **Error Responses:**
    *   **400 Bad Request:** If the request body is invalid (e.g., missing `name` field, or the name already exists).
    *   **403 Forbidden:** If the API key is invalid or missing.

### `GET /printers/{id}/`

Retrieves a single, specific printer by its unique ID.

*   **Summary:** Retrieve a Printer by ID
*   **URL Parameter:** `id` (integer, required) - The unique ID of the printer.
*   **Success Response (200 OK):**
    The requested printer object.
    ```json
    {
        "id": 1,
        "name": "British American Bank Note Company"
    }
    ```
*   **Error Responses:**
    *   **403 Forbidden:** If the API key is invalid or missing.
    *   **404 Not Found:** If no printer with the given ID exists.

### `PUT /printers/{id}/`

Updates an existing printer. This method supports partial updates, so you only need to provide the fields you want to change.

*   **Summary:** Update a Printer
*   **URL Parameter:** `id` (integer, required) - The unique ID of the printer to update.
*   **Request Body:**
    A JSON object containing the fields to be updated.
    ```json
    {
      "name": "BABN Company"
    }
    ```
*   **Success Response (200 OK):**
    The full, updated printer object.
    ```json
    {
        "id": 1,
        "name": "BABN Company"
    }
    ```
*   **Error Responses:**
    *   **400 Bad Request:** If the request body contains invalid data (e.g., a duplicate `name`).
    *   **403 Forbidden:** If the API key is invalid or missing.
    *   **404 Not Found:** If no printer with the given ID exists.

### `DELETE /printers/{id}/`

Permanently deletes a printer.

*   **Summary:** Delete a Printer
*   **URL Parameter:** `id` (integer, required) - The ID of the printer to delete.
*   **Success Response (200 OK):**
    A confirmation message indicating successful deletion.
    ```json
    {
        "message": "Printer with id 1 has been deleted successfully."
    }
    ```
*   **Error Responses:**
    *   **403 Forbidden:** If the API key is invalid or missing.
    *   **404 Not Found:** If no printer with the given ID exists.