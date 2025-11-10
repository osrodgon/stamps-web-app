# Stamps API Documentation

Welcome to the API documentation for the Stamps resource. This document provides detailed information about the RESTful endpoints for managing the individual stamps in the master catalog.

The Stamps API allows you to create, view, update, and delete individual stamp entries. Each stamp is part of a larger `Issue`.

## Resource URL

The base URL for all version 1 endpoints for this resource is:

`/stamps_server/api/v1/stamps/`

## Authentication

All endpoints are protected and require authentication via an API key or a password hash provided in the request headers. Please refer to the main `readme_api.md` for detailed authentication instructions.

---

## Model Description

The `Stamp` model represents an individual stamp within an `Issue`.

| Field | Type | Description |
| :--- | :--- | :--- |
| `id` | Integer | The unique identifier for the stamp. |
| `issue` | Foreign Key | The issue this stamp belongs to (links to `issues_api.Issue`). |
| `edifil_code` | String | The Edifil catalog code for the stamp. |
| `face_value` | String | The denominative face value of the stamp (e.g., "10c", "1.00€"). |
| `name` | String | The name or description of the individual stamp. |
| `others_code` | String | Catalog codes from other systems (e.g., Scott, Michel). |
| `image` | String | Path or URL to an image of the stamp. |
| `colors` | Many-to-Many | A list of colors associated with the stamp (links to `colors_api.Color`). |
| `market_value` | Decimal | The estimated market value of the individual stamp. |

---

## API Endpoints

### `GET /stamps/`

Retrieves a list of all stamps in the catalog.

*   **Summary:** List All Stamps
*   **Success Response (200 OK):**
    A JSON array of stamp objects. Foreign key and many-to-many relationships are represented by their IDs.
    ```json
    [
      {
        "id": 1,
        "issue": 1,
        "edifil_code": "4001",
        "face_value": "1.00",
        "name": "Sagrada Familia",
        "others_code": "SG-123",
        "image": "/images/sagrada.jpg",
        "colors": [10],
        "market_value": "1.20"
      }
    ]
    ```
*   **Error Responses:**
    *   **403 Forbidden:** If the API key is invalid or missing.

### `POST /stamps/`

Creates a new stamp entry in the catalog.

*   **Summary:** Create a Stamp
*   **Request Body:**
    A JSON object representing the new stamp. Foreign keys and many-to-many fields should be provided as integer IDs or a list of IDs.
    ```json
    {
      "issue": 1,
      "edifil_code": "4002",
      "face_value": "1.50",
      "name": "Alhambra",
      "colors": [1, 5],
      "market_value": "1.80"
    }
    ```
*   **Success Response (201 Created):**
    The full, newly created stamp object.
    ```json
    {
      "id": 2,
      "issue": 1,
      "edifil_code": "4002",
      "face_value": "1.50",
      "name": "Alhambra",
      "others_code": null,
      "image": null,
      "colors": [1, 5],
      "market_value": "1.80"
    }
    ```
*   **Error Responses:**
    *   **400 Bad Request:** If the request body is invalid (e.g., missing required fields, invalid data types, or non-existent foreign key IDs).
    *   **403 Forbidden:** If the API key is invalid or missing.

### `GET /stamps/{id}/`

Retrieves a single, specific stamp by its unique ID.

*   **Summary:** Retrieve a Stamp by ID
*   **URL Parameter:** `id` (integer, required) - The unique ID of the stamp.
*   **Success Response (200 OK):**
    The requested stamp object.
    ```json
    {
      "id": 1,
      "issue": 1,
      "edifil_code": "4001",
      "face_value": "1.00",
      "name": "Sagrada Familia",
      "others_code": "SG-123",
      "image": "/images/sagrada.jpg",
      "colors": [10],
      "market_value": "1.20"
    }
    ```
*   **Error Responses:**
    *   **403 Forbidden:** If the API key is invalid or missing.
    *   **404 Not Found:** If no stamp with the given ID exists.

### `PUT /stamps/{id}/`

Updates an existing stamp. This method supports partial updates, so you only need to provide the fields you want to change.

*   **Summary:** Update a Stamp
*   **URL Parameter:** `id` (integer, required) - The unique ID of the stamp to update.
*   **Request Body:**
    A JSON object containing the fields to be updated.
    ```json
    {
      "market_value": "1.30",
      "colors": [1, 10]
    }
    ```
*   **Success Response (200 OK):**
    The full, updated stamp object.
    ```json
    {
      "id": 1,
      "issue": 1,
      "edifil_code": "4001",
      "face_value": "1.00",
      "name": "Sagrada Familia",
      "others_code": "SG-123",
      "image": "/images/sagrada.jpg",
      "colors": [1, 10],
      "market_value": "1.30"
    }
    ```
*   **Error Responses:**
    *   **400 Bad Request:** If the request body contains invalid data (e.g., invalid foreign key IDs).
    *   **403 Forbidden:** If the API key is invalid or missing.
    *   **404 Not Found:** If no stamp with the given ID exists.

### `DELETE /stamps/{id}/`

Permanently deletes a stamp from the catalog.

*   **Summary:** Delete a Stamp
*   **URL Parameter:** `id` (integer, required) - The ID of the stamp to delete.
*   **Success Response (200 OK):**
    A confirmation message indicating successful deletion.
    ```json
    {
        "message": "Stamp with id 1 has been deleted successfully."
    }
    ```
*   **Error Responses:**
    *   **403 Forbidden:** If the API key is invalid or missing.
    *   **404 Not Found:** If no stamp with the given ID exists.