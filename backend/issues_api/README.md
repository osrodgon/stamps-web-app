# Issues API Documentation

Welcome to the API documentation for the Issues resource. This document provides detailed information about the RESTful endpoints for managing stamp issues.

The Issues API allows you to create, view, update, and delete stamp issues, which are typically series or sets of stamps released at a particular time. This resource has foreign key relationships to several lookup tables like `years`, `countries`, `stamp_types`, and `paper_types`.

## Resource URL

The base URL for all version 1 endpoints for this resource is:

`/stamps_server/api/v1/issues/`

## Authentication

All endpoints are protected and require authentication via an API key or a password hash provided in the request headers. Please refer to the main `readme_api.md` for detailed authentication instructions.

---

## Model Description

The `Issue` model represents a specific issue of stamps.

| Field | Type | Description |
| :--- | :--- | :--- |
| `id` | Integer | The unique identifier for the issue. |
| `year` | Foreign Key | The year of the issue (links to `years_api.Year`). |
| `date` | Date | Release date of the issue. |
| `name` | String | Name or description of the issue. |
| `total_printed` | Integer | Total number of stamps printed for this issue. |
| `market_value` | Decimal | Estimated market value of the issue as a set. |
| `stamp_type` | Foreign Key | Type of stamp in this issue (links to `stamp_types_api.StampType`). |
| `paper_type` | Foreign Key | Type of paper used (links to `paper_types_api.PaperType`). |
| `description` | Text | Detailed description of the issue. |
| `country` | Foreign Key | Country of origin for the issue (links to `countries_api.Country`). |
| `note` | Text | Any additional notes for the issue. |
| `perforation` | String | Perforation details (e.g., "13", "11.5x12"). |

---

## API Endpoints

### `GET /issues/`

Retrieves a list of all stamp issues.

*   **Summary:** List All Stamp Issues
*   **Success Response (200 OK):**
    A JSON array of stamp issue objects. Foreign key relationships are represented by their IDs.
    ```json
    [
      {
        "id": 1,
        "year": 1,
        "date": "2023-01-15",
        "name": "Historic Monuments",
        "total_printed": 10000,
        "market_value": "5.50",
        "stamp_type": 1,
        "paper_type": 1,
        "description": "A series on famous historical landmarks.",
        "country": 1,
        "note": "First issue of the year.",
        "perforation": "13"
      }
    ]
    ```
*   **Error Responses:**
    *   **403 Forbidden:** If the API key is invalid or missing.

### `POST /issues/`

Creates a new stamp issue.

*   **Summary:** Create a Stamp Issue
*   **Request Body:**
    A JSON object representing the new stamp issue. Foreign keys should be provided as integer IDs.
    ```json
    {
      "year": 2,
      "date": "2024-02-20",
      "name": "Flora and Fauna",
      "total_printed": 15000,
      "market_value": "7.00",
      "stamp_type": 2,
      "paper_type": 1,
      "description": "A series on local wildlife.",
      "country": 2,
      "note": "Commemorative issue.",
      "perforation": "14"
    }
    ```
*   **Success Response (201 Created):**
    The full, newly created issue object.
    ```json
    {
      "id": 2,
      "year": 2,
      "date": "2024-02-20",
      "name": "Flora and Fauna",
      "total_printed": 15000,
      "market_value": "7.00",
      "stamp_type": 2,
      "paper_type": 1,
      "description": "A series on local wildlife.",
      "country": 2,
      "note": "Commemorative issue.",
      "perforation": "14"
    }
    ```
*   **Error Responses:**
    *   **400 Bad Request:** If the request body is invalid (e.g., missing required fields, invalid data types, or non-existent foreign key IDs).
    *   **403 Forbidden:** If the API key is invalid or missing.

### `GET /issues/{id}/`

Retrieves a single, specific stamp issue by its unique ID.

*   **Summary:** Retrieve a Stamp Issue by ID
*   **URL Parameter:** `id` (integer, required) - The unique ID of the stamp issue.
*   **Success Response (200 OK):**
    The requested stamp issue object.
    ```json
    {
      "id": 1,
      "year": 1,
      "date": "2023-01-15",
      "name": "Historic Monuments",
      "total_printed": 10000,
      "market_value": "5.50",
      "stamp_type": 1,
      "paper_type": 1,
      "description": "A series on famous historical landmarks.",
      "country": 1,
      "note": "First issue of the year.",
      "perforation": "13"
    }
    ```
*   **Error Responses:**
    *   **403 Forbidden:** If the API key is invalid or missing.
    *   **404 Not Found:** If no issue with the given ID exists.

### `PUT /issues/{id}/`

Updates an existing stamp issue. This method supports partial updates, so you only need to provide the fields you want to change.

*   **Summary:** Update a Stamp Issue
*   **URL Parameter:** `id` (integer, required) - The unique ID of the stamp issue to update.
*   **Request Body:**
    A JSON object containing the fields to be updated.
    ```json
    {
      "name": "Updated Issue Name",
      "note": "Updated note about the issue.",
      "market_value": "6.00"
    }
    ```
*   **Success Response (200 OK):**
    The full, updated issue object.
    ```json
    {
      "id": 1,
      "year": 1,
      "date": "2023-01-15",
      "name": "Updated Issue Name",
      "total_printed": 10000,
      "market_value": "6.00",
      "stamp_type": 1,
      "paper_type": 1,
      "description": "A series on famous historical landmarks.",
      "country": 1,
      "note": "Updated note about the issue.",
      "perforation": "13"
    }
    ```
*   **Error Responses:**
    *   **400 Bad Request:** If the request body contains invalid data (e.g., invalid foreign key IDs).
    *   **403 Forbidden:** If the API key is invalid or missing.
    *   **404 Not Found:** If no issue with the given ID exists.

### `DELETE /issues/{id}/`

Permanently deletes a stamp issue.

*   **Summary:** Delete a Stamp Issue
*   **URL Parameter:** `id` (integer, required) - The ID of the stamp issue to delete.
*   **Success Response (200 OK):**
    A confirmation message indicating successful deletion.
    ```json
    {
        "message": "Issue with id 1 has been deleted successfully."
    }
    ```
*   **Error Responses:**
    *   **403 Forbidden:** If the API key is invalid or missing.
    *   **404 Not Found:** If no issue with the given ID exists.
