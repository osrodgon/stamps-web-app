# Collection Items API Documentation

Welcome to the API documentation for the Collection Items resource. This document provides detailed information about the RESTful endpoints for managing the individual stamps within a user's collection.

The Collection Items API allows you to add, view, update, and remove stamps from a collection, effectively acting as the link between the `collections` and `stamps` resources.

## Resource URL

The base URL for all version 1 endpoints for this resource is:

`/stamps_server/api/v1/collection_items/`

## Authentication

All endpoints are protected and require authentication via an API key or a password hash provided in the request headers. Please refer to the main `readme_api.md` for detailed authentication instructions.

---

## Model Description

The `CollectionItem` model represents a single stamp that a user has in a specific collection.

| Field | Type | Description |
| :--- | :--- | :--- |
| `id` | Integer | The unique identifier for the collection item. |
| `collection` | Foreign Key | A reference to the `Collection` this item belongs to. |
| `stamp` | Foreign Key | A reference to the master `Stamp` catalog entry. |
| `location` | Foreign Key | The physical or logical location where the stamp is stored (e.g., "Main Album"). |
| `condition_type` | Foreign Key | The condition of the stamp (e.g., "Mint", "Used"). |
| `price_paid` | Decimal | The amount paid for the stamp. |
| `acquisition_date` | Date | The date the stamp was acquired. |
| `note` | Text | Any personal notes about this specific item. |
| `quantity` | Integer | The number of identical copies of this stamp in the collection. |

---

## API Endpoints

### `GET /collection_items/`

Retrieves a list of all items across all collections.

*   **Summary:** List All Collection Items
*   **Success Response (200 OK):**
    A JSON array of collection item objects. Foreign key relationships are represented as nested objects.
    ```json
    [
      {
        "id": 1,
        "collection": { "id": 1, "user": "testuser", "name": "European Classics" },
        "stamp": { "id": 101, "name": "The Castle", "edifil_code": "4567" },
        "location": { "id": 1, "name": "Main Album" },
        "condition_type": { "id": 1, "name": "Mint" },
        "price_paid": "1.50",
        "acquisition_date": "2023-10-01",
        "note": "First day cover.",
        "quantity": 1
      }
    ]
    ```
*   **Error Response (403 Forbidden):** If the API key is invalid or missing.

### `POST /collection_items/`

Adds a new stamp to a collection.

*   **Summary:** Add a Stamp to a Collection
*   **Request Body:**
    A JSON object representing the new collection item. Foreign keys should be provided as integer IDs.
    ```json
    {
      "collection": 1,
      "stamp": 102,
      "location": 1,
      "condition_type": 2,
      "price_paid": "2.00",
      "acquisition_date": "2024-01-15",
      "note": "Purchased from auction.",
      "quantity": 1
    }
    ```
*   **Success Response (201 Created):**
    The full, newly created collection item object, with nested representations for foreign keys.
    ```json
    {
      "id": 2,
      "collection": { "id": 1, "user": "testuser", "name": "European Classics" },
      "stamp": { "id": 102, "name": "The Bridge", "edifil_code": "4568" },
      "location": { "id": 1, "name": "Main Album" },
      "condition_type": { "id": 2, "name": "Used" },
      "price_paid": "2.00",
      "acquisition_date": "2024-01-15",
      "note": "Purchased from auction.",
      "quantity": 1
    }
    ```
*   **Error Responses:**
    *   **400 Bad Request:** If the request body is invalid (e.g., missing required fields, invalid data types, or a unique constraint violation like adding the same stamp to the same collection twice).
    *   **403 Forbidden:** If the API key is invalid or missing.

### `GET /collection_items/{id}/`

Retrieves a single, specific collection item by its unique ID.

*   **Summary:** Retrieve a Collection Item by ID
*   **URL Parameter:** `id` (integer, required) - The unique ID of the collection item.
*   **Success Response (200 OK):**
    The requested collection item object with nested representations.
    ```json
    {
        "id": 1,
        "collection": { "id": 1, "user": "testuser", "name": "European Classics" },
        "stamp": { "id": 101, "name": "The Castle", "edifil_code": "4567" },
        "location": { "id": 1, "name": "Main Album" },
        "condition_type": { "id": 1, "name": "Mint" },
        "price_paid": "1.50",
        "acquisition_date": "2023-10-01",
        "note": "First day cover.",
        "quantity": 1
    }
    ```
*   **Error Responses:**
    *   **403 Forbidden:** If the API key is invalid or missing.
    *   **404 Not Found:** If no collection item with the given ID exists.

### `PUT /collection_items/{id}/`

Updates an existing collection item. This method supports partial updates, so you only need to provide the fields you want to change.

*   **Summary:** Update a Collection Item
*   **URL Parameter:** `id` (integer, required) - The unique ID of the collection item to update.
*   **Request Body:**
    A JSON object containing the fields to be updated.
    ```json
    {
      "price_paid": "1.75",
      "note": "Updated note about condition.",
      "quantity": 2
    }
    ```
*   **Success Response (200 OK):**
    The full, updated collection item object.
    ```json
    {
        "id": 1,
        "collection": { "id": 1, "user": "testuser", "name": "European Classics" },
        "stamp": { "id": 101, "name": "The Castle", "edifil_code": "4567" },
        "location": { "id": 1, "name": "Main Album" },
        "condition_type": { "id": 1, "name": "Mint" },
        "price_paid": "1.75",
        "acquisition_date": "2023-10-01",
        "note": "Updated note about condition.",
        "quantity": 2
    }
    ```
*   **Error Responses:**
    *   **400 Bad Request:** If the request body contains invalid data.
    *   **403 Forbidden:** If the API key is invalid or missing.
    *   **404 Not Found:** If no collection item with the given ID exists.

### `DELETE /collection_items/{id}/`

Permanently removes a stamp from a collection.

*   **Summary:** Remove a Stamp from a Collection
*   **URL Parameter:** `id` (integer, required) - The ID of the collection item to delete.
*   **Success Response (200 OK):**
    A confirmation message indicating successful deletion.
    ```json
    {
        "message": "Collection item with id 1 has been deleted successfully."
    }
    ```
*   **Error Responses:**
    *   **403 Forbidden:** If the API key is invalid or missing.
    *   **404 Not Found:** If no collection item with the given ID exists.

