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

---

## Series, copies and the catalogue

Beyond the collection itself, these endpoints read what it holds and write the user's copies.
The user always comes from the JWT (`Authorization: JWT <token>`); a collection or a series
that is not the caller's answers **404**, and a request without a token **403**.

| Method | Path | What it does |
| :--- | :--- | :--- |
| `GET` | `/collections/{id}/issues/` | One page of the series the collection holds something of. |
| `GET` | `/collections/{id}/issues/{issue_id}/` | One series with every stamp, the user's `item` or `null`, the summary and its place in the list. |
| `DELETE` | `/collections/{id}/issues/{issue_id}/` | Removes the user's copies of that series. The catalogue keeps the series. |
| `POST` | `/collections/{id}/items/` | Adds the user's copy of one stamp (`stamp` in the body). |
| `POST` | `/collections/{id}/items/bulk/` | Adds many: one stamp, one series or one whole year. |
| `GET` | `/collections/{id}/catalogue/issues/` | The catalogue: every series with stamps, with how many the collection owns. |
| `GET` | `/collections/{id}/catalogue/issues/{issue_id}/` | One series of the catalogue, owned or not. |

### The series page

`GET /collections/{id}/issues/` mirrors `/issues/`: `page`, `pageSize` (0 means all),
`name`, `year` (`1850`, `1850-1860`, `1850-`, `-1860`), `sortBy` (`date` or `name`) and
`order` (`asc` or `desc`), with the same `pagination` block. Each row carries `cover`,
`total_stamps`, `owned_stamps`, `paid` and `catalogue_mnh`. **Two queries**, whatever the
page size.

### One series

`GET /collections/{id}/issues/{issue_id}/` returns `issue`, its `stamps` (each with the
caller's `item` or `null`), `summary` (`owned`, `total`, `paid`) and `neighbours`:

```json
"neighbours": {"position": 3, "total": 28, "previous": 2549, "next": 2552}
```

`neighbours` is `null` in the catalogue detail, which has no list behind it. The reading
detail costs five queries: the issue, its stamps, their colours, the copies and the ids of
the list the arrows walk.

`DELETE` on the same path removes the copies of that series and answers
`{"deleted": 5}`. A series the collection does not hold answers 404.

### Adding copies

`POST /collections/{id}/items/` adds one `stamp` (201, 404 unknown stamp, 409 already
there). It does not overwrite a copy that exists.

`POST /collections/{id}/items/bulk/` takes **one scope per request**:

```json
{"scope": "stamp", "ids": [10, 11]}
{"scope": "issue", "issue": 42}
{"scope": "year", "year": 1850}
```

One transaction; a stamp already in the collection is **skipped**, not refused. The answer
is `{"created": 3, "skipped": 2, "total": 5}`. A scope over **500 stamps** answers 400 and
writes nothing; a scope with no stamps answers 404. The copies are created with the
collection and the stamp only — condition, price, date, location and note are the user's to
fill in, and `quantity` starts at **1**.

### The catalogue the dialog browses

`GET /collections/{id}/catalogue/issues/` is the series page above without the ownership
scope: every series with stamps, held or not, with `owned_stamps` at 0 for the ones the
collection does not have. Same parameters, same `pagination` block, **two queries**.

`GET /collections/{id}/catalogue/issues/{issue_id}/` is the series detail above without the
ownership precondition: any series of the catalogue, with `item` or `null` per stamp and
`neighbours: null`. Four queries.
