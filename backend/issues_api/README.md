# Issues API Documentation

Welcome to the API documentation for the Issues resource. This document provides detailed information about the RESTful endpoints for managing stamp issues.

The Issues API allows you to create, view, update, and delete stamp issues, which are typically series or sets of stamps released at a particular time. This resource has foreign key relationships to several lookup tables like `years`, `countries`, `stamp_types`, `print_types`, `printers`, `artists`, and `paper_types`.

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
| `total_printed` | BigInteger | Total number of stamps printed for this issue. |
| `market_value_mnh` | Decimal | Estimated market value of the issue in mint never hinged condition. |
| `market_value_used` | Decimal | Estimated market value of the issue in used condition. |
| `stamp_type` | Foreign Key | Type of stamp in this issue (links to `stamp_types_api.StampType`). |
| `print_type` | Foreign Key | Type of printing used (links to `print_types_api.PrintType`). |
| `printer` | Foreign Key | The printer company (links to `printers_api.Printer`). |
| `artist` | Foreign Key | The artist/engraver (links to `artists_api.Artist`). |
| `paper_type` | Foreign Key | Type of paper used (links to `paper_types_api.PaperType`). |
| `description` | Text | Detailed description of the issue. |
| `country` | Foreign Key | Country of origin for the issue (links to `countries_api.Country`). |
| `note` | Text | Any additional notes for the issue. |
| `perforation` | String | Perforation details (e.g., "13", "11.5x12"). |

---

## API Endpoints

### `GET /issues/`

Retrieves a list of all stamp issues with support for filtering, sorting, and pagination.

*   **Summary:** List All Stamp Issues
*   **Query Parameters:**
    
    | Parameter | Type | Description |
    | :--- | :--- | :--- |
    | `year` | String | Filter issues by year or year range (e.g., `2002` or `2000-2010`). |
    | `name` | String | Filter issues by name (case-insensitive, supports accented characters). |
    | `sortBy` | String | Sort issues by field (default: `date`). Options: `date`, `name`. |
    | `order` | String | Order direction (default: `asc`). Options: `asc`, `desc`. |
    | `page` | Integer | Page number (default: 1). |
    | `pageSize` | Integer | Number of items per page (default: 15). A value of 0 returns all items. |

*   **Filtering Behavior:**
    - When both `year` and `name` are provided:
        - If `year` is a single value (e.g., `2002`): Returns issues matching year **OR** name.
        - If `year` is a range (e.g., `2000-2010`): Returns issues matching year range **AND** name.
    - When only `year` is provided: Filters by year or year range.
    - When only `name` is provided: Filters by name.

*   **Success Response (200 OK):**
    A JSON object containing paginated stamp issues and pagination metadata.
    ```json
    {
      "issues": [
        {
          "id": 1,
          "year": "2023",
          "date": "2023-01-15",
          "name": "Historic Monuments",
          "total_printed": 10000,
          "market_value_mnh": "5.50",
          "market_value_used": "2.00",
          "stamp_type": "Commemorative",
          "print_type": "Offset",
          "printer": "FNMT",
          "artist": "John Smith",
          "paper_type": "Coated",
          "description": "A series on famous historical landmarks.",
          "country": "Spain",
          "note": "First issue of the year.",
          "perforation": "13"
        }
      ],
      "pagination": {
        "sort_by": "date",
        "order": "asc",
        "page": 1,
        "page_size": 15,
        "total": 100,
        "has_more": true
      }
    }
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
      "market_value_mnh": "7.00",
      "market_value_used": "3.00",
      "stamp_type": 2,
      "print_type": 1,
      "printer": 1,
      "artist": 1,
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
      "year": "2024",
      "date": "2024-02-20",
      "name": "Flora and Fauna",
      "total_printed": 15000,
      "market_value_mnh": "7.00",
      "market_value_used": "3.00",
      "stamp_type": "Definitive",
      "print_type": "Offset",
      "printer": "FNMT",
      "artist": "Jane Doe",
      "paper_type": "Coated",
      "description": "A series on local wildlife.",
      "country": "Spain",
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
      "year": "2023",
      "date": "2023-01-15",
      "name": "Historic Monuments",
      "total_printed": 10000,
      "market_value_mnh": "5.50",
      "market_value_used": "2.00",
      "stamp_type": "Commemorative",
      "print_type": "Offset",
      "printer": "FNMT",
      "artist": "John Smith",
      "paper_type": "Coated",
      "description": "A series on famous historical landmarks.",
      "country": "Spain",
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
      "market_value_mnh": "6.00"
    }
    ```
*   **Success Response (200 OK):**
    The full, updated issue object.
    ```json
    {
      "id": 1,
      "year": "2023",
      "date": "2023-01-15",
      "name": "Updated Issue Name",
      "total_printed": 10000,
      "market_value_mnh": "6.00",
      "market_value_used": "2.00",
      "stamp_type": "Commemorative",
      "print_type": "Offset",
      "printer": "FNMT",
      "artist": "John Smith",
      "paper_type": "Coated",
      "description": "A series on famous historical landmarks.",
      "country": "Spain",
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

---

## Collection Endpoint

### `POST /issues/collections/`

Creates a new issue with all related entities (stamps, colors, etc.) in a single request. This endpoint is designed for creating complete issue entries with all associated data from AI extraction or bulk import operations.

*   **Summary:** Create Issue with Related Entities
*   **Description:** Creates a complete issue entry in the database, including all related entities such as stamps, colors, and other associated data. This endpoint expects a comprehensive payload containing all necessary information to create the issue and its related entities in a single transactional request.
*   **Request Body:**
    A JSON object containing the issue data and related stamps.
    ```json
    {
      "issue_name": "Olimpiadas Barcelona 1992",
      "description": "Series commemorating the Barcelona 1992 Olympic Games",
      "issue_date": "1992-07-25",
      "artist": "José María Cruz Novillo",
      "printer": "Fábrica Nacional de Moneda y Timbre",
      "print_type": "Offset",
      "perforation": "13 x 13",
      "paper_type": "Estucado",
      "stamp_type": "Sello",
      "notes": "Commemorative series for Barcelona Olympics",
      "total_printed": 5000000,
      "market_value_mnh": 25.50,
      "market_value_used": 8.00,
      "stamps": [
        {
          "edifil_code": "2461",
          "fesofi_code": "2461",
          "face_value": "5 PTA",
          "description": "Olympic rings and logo",
          "amount_printed": 1000000,
          "color": "Multicolor",
          "market_value_mnh": 3.50,
          "market_value_used": 1.00
        }
      ]
    }
    ```
    
    **Request Fields:**
    
    | Field | Type | Required | Description |
    | :--- | :--- | :--- | :--- |
    | `issue_name` | String | Yes | Name of the stamp issue. |
    | `description` | String | No | Historical description (default: "n/a"). |
    | `issue_date` | Date | No | Issue date in YYYY-MM-DD format. |
    | `artist` | String | No | Artist/engraver name (default: "n/a"). |
    | `printer` | String | No | Printer name (default: "n/a"). |
    | `print_type` | String | No | Printing technique (default: "n/a"). |
    | `perforation` | String | No | Perforation measurement (default: "n/a"). |
    | `paper_type` | String | No | Paper type (default: "n/a"). |
    | `stamp_type` | String | No | Format type (default: "n/a"). |
    | `notes` | String | No | Additional notes (default: "n/a"). |
    | `total_printed` | Integer | No | Total printed quantity. |
    | `market_value_mnh` | Float | No | Market value in mint condition. |
    | `market_value_used` | Float | No | Market value in used condition. |
    | `stamps` | Array | Yes | List of individual stamp details. |
    
    **Stamp Object Fields:**
    
    | Field | Type | Description |
    | :--- | :--- | :--- |
    | `edifil_code` | String | Edifil catalog code. |
    | `fesofi_code` | String | Fesofi catalog code. |
    | `face_value` | String | Exact face value (e.g., "5 PTA"). |
    | `description` | String | Design/motive description. |
    | `amount_printed` | Integer | Individual stamp print run. |
    | `color` | String | Color description. |
    | `market_value_mnh` | Float | Market value in mint condition. |
    | `market_value_used` | Float | Market value in used condition. |

*   **Success Response (201 Created):**
    The created issue collection object with summary information.
    ```json
    {
      "issue_name": "Olimpiadas Barcelona 1992",
      "issue_date": "1992-07-25"
    }
    ```

*   **Error Responses:**
    *   **400 Bad Request:** If the request body is invalid (e.g., missing required fields, invalid data).
        ```json
        {
          "error": ["Invalid data provided"],
          "message": null
        }
        ```
    *   **403 Forbidden:** If the API key is invalid or missing.