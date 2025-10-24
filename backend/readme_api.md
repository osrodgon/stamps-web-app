# Stamps Collection API Documentation

Welcome to the API documentation for the Stamps Collection application. This document provides detailed information about the available RESTful endpoints for managing your stamp collection, accessing catalog data, and configuring the application.

The base URL for all version 1 endpoints is: `/stamps_server/api/v1/`

## Authentication

All endpoints are protected and require authentication. You can authenticate by providing one of the following in the request header:

*   **Header:** `X-API-Key: <your_api_key> or <your_password_hash>`
---

## API Endpoints

The API is organized into several resource categories:

1.  Config Management
2.  Database Management
3.  Collection Management
4.  User Management

---

## Config Management

Endpoints for managing system configuration settings.

### Config Resource

**Resource URL:** `/config/`

#### `GET /config/`

Retrieves a list of all configuration key-value pairs.

*   **Summary:** List All Configuration Entries
*   **Success Response (200 OK):**
    ```json
    [
      {
        "property": "some_property",
        "value": "some_value"
      },
      {
        "property": "another_property",
        "value": "another_value"
      }
    ]
    ```
*   **Error Response (403 Forbidden):** If the API key is invalid or missing.

#### `POST /config/`

Creates a new configuration key-value pair.

*   **Summary:** Create a Configuration Entry
*   **Request Body:**
    ```json
    {
      "property": "new_property",
      "value": "new_value"
    }
    ```
*   **Success Response (201 Created):**
    ```json
    {
      "property": "new_property",
      "value": "new_value"
    }
    ```
*   **Error Responses:**
    *   **400 Bad Request:** If the request body is invalid (e.g., missing fields, property already exists).
    *   **403 Forbidden:** If the API key is invalid or missing.

#### `GET /config/{id}/`

Retrieves a single configuration entry by its ID.

*   **Summary:** Get Configuration Entry by ID
*   **URL Parameter:** `id` (integer, required) - The ID of the configuration entry.
*   **Success Response (200 OK):**
    ```json
    {
      "id": 1,
      "property": "some_property",
      "value": "some_value"
    }
    ```
*   **Error Responses:**
    *   **403 Forbidden:** If the API key is invalid or missing.
    *   **404 Not Found:** If no configuration with the given property exists.

#### `PUT /config/{id}/`

Updates an existing configuration entry.

*   **Summary:** Update Configuration Entry
*   **URL Parameter:** `id` (integer, required) - The ID of the configuration entry to update.
*   **Request Body:**
    ```json
    {
      "value": "updated_value"
    }
    ```
*   **Success Response (200 OK):**
    ```json
    {
      "id": 1,
      "property": "some_property",
      "value": "updated_value"
    }
    ```
*   **Error Responses:**
    *   **400 Bad Request:** If the request body is invalid.
    *   **403 Forbidden:** If the API key is invalid or missing.
    *   **404 Not Found:** If no configuration with the given property exists.

#### `DELETE /config/{id}/`

Deletes a configuration entry.

*   **Summary:** Delete Configuration Entry
*   **URL Parameter:** `id` (integer, required) - The ID of the configuration entry to delete.
*   **Success Response (204 No Content):** An empty response indicating successful deletion.
*   **Error Responses:**
    *   **403 Forbidden:** If the API key is invalid or missing.
    *   **404 Not Found:** If no configuration with the given property exists.

---

## Database Management

APIs for managing the core stamp catalog data, including lookup tables and core entities. These endpoints typically provide full CRUD (Create, Read, Update, Delete) operations.

### Issues Resource

**Resource URL:** `/issues/`

Manages stamp issues, which are series or sets of stamps. This is a complex resource with foreign key relationships to many lookup tables.

#### `GET /issues/`

*   **Summary:** List All Stamp Issues
*   **Success Response (200 OK):** A list of all stamp issue objects.
    ```json
    [
      {
        "id": 1,
        "year_id": 1,
        "date": "2023-01-15",
        "name": "Historic Monuments",
        "total_printed": 10000,
        "market_value": 5.50,
        "stamp_type_id": 1,
        "country_id": 1
      }
    ]
    ```
*   **Error Response (403 Forbidden):** If the API key is invalid or missing.

#### `POST /issues/`

*   **Summary:** Create a Stamp Issue
*   **Request Body:**
    ```json
    {
      "year_id": 1,
      "date": "2024-02-20",
      "name": "Flora and Fauna",
      "total_printed": 15000,
      "market_value": 7.00,
      "stamp_type_id": 2,
      "country_id": 2,
      "description": "A series on local wildlife."
    }
    ```
*   **Success Response (201 Created):** The full created issue object.
*   **Error Responses:**
    *   **400 Bad Request:** If the request body is invalid.
    *   **403 Forbidden:** If the API key is invalid or missing.

#### `GET /issues/{id}/`

*   **Summary:** Retrieve a Stamp Issue by ID
*   **URL Parameter:** `id` (integer, required) - The ID of the stamp issue.
*   **Success Response (200 OK):** The requested stamp issue object.
*   **Error Responses:**
    *   **403 Forbidden:** If the API key is invalid or missing.
    *   **404 Not Found:** If no issue with the given ID exists.

#### `PUT /issues/{id}/`

*   **Summary:** Update a Stamp Issue
*   **URL Parameter:** `id` (integer, required) - The ID of the stamp issue.
*   **Request Body:**
    ```json
    {
      "name": "Updated Issue Name",
      "note": "Updated note."
    }
    ```
*   **Success Response (200 OK):** The full updated issue object.
*   **Error Responses:**
    *   **400 Bad Request:** If the request body is invalid.
    *   **403 Forbidden:** If the API key is invalid or missing.
    *   **404 Not Found:** If no issue with the given ID exists.

#### `DELETE /issues/{id}/`

*   **Summary:** Delete a Stamp Issue
*   **URL Parameter:** `id` (integer, required) - The ID of the stamp issue.
*   **Success Response (204 No Content):** An empty response indicating successful deletion.
*   **Error Responses:**
    *   **403 Forbidden:** If the API key is invalid or missing.
    *   **404 Not Found:** If no issue with the given ID exists.

### Stamps Resource

**Resource URL:** `/stamps/`

Manages individual stamps within an issue.

#### `GET /stamps/`

*   **Summary:** List All Stamps
*   **Success Response (200 OK):** A list of all stamp objects.
    ```json
    [
      {
        "id": 1,
        "issue_id": 1,
        "edifil_code": "4567",
        "name": "The Castle",
        "color_id": 3
      }
    ]
    ```
*   **Error Response (403 Forbidden):** If the API key is invalid or missing.

#### `POST /stamps/`

*   **Summary:** Create a Stamp
*   **Request Body:**
    ```json
    {
      "issue_id": 1,
      "edifil_code": "4568",
      "face_value": "0.50",
      "name": "The Bridge",
      "color_id": 4
    }
    ```
*   **Success Response (201 Created):** The full created stamp object.
*   **Error Responses:**
    *   **400 Bad Request:** If the request body is invalid.
    *   **403 Forbidden:** If the API key is invalid or missing.

#### `GET /stamps/{id}/`

*   **Summary:** Retrieve a Stamp by ID
*   **URL Parameter:** `id` (integer, required) - The ID of the stamp.
*   **Success Response (200 OK):** The requested stamp object.
*   **Error Responses:**
    *   **403 Forbidden:** If the API key is invalid or missing.
    *   **404 Not Found:** If no stamp with the given ID exists.

#### `PUT /stamps/{id}/`

*   **Summary:** Update a Stamp
*   **URL Parameter:** `id` (integer, required) - The ID of the stamp.
*   **Request Body:**
    ```json
    {
      "edifil_code": "4567-A",
      "color_id": 5
    }
    ```
*   **Success Response (200 OK):** The full updated stamp object.
*   **Error Responses:**
    *   **400 Bad Request:** If the request body is invalid.
    *   **403 Forbidden:** If the API key is invalid or missing.
    *   **404 Not Found:** If no stamp with the given ID exists.

#### `DELETE /stamps/{id}/`

*   **Summary:** Delete a Stamp
*   **URL Parameter:** `id` (integer, required) - The ID of the stamp.
*   **Success Response (204 No Content):** An empty response indicating successful deletion.
*   **Error Responses:**
    *   **403 Forbidden:** If the API key is invalid or missing.
    *   **404 Not Found:** If no stamp with the given ID exists.

### Lookup Table Resources

The following resources for managing reference data follow a standard RESTful pattern with a primary key of `id` (integer).

For each resource (e.g., `/colors/`, `/countries/`, etc.), the following standard RESTful operations are available.

#### `GET /<resource>/`
*   **Summary:** List All Entries (e.g., List All Colors)
*   **Success Response (200 OK):** `[{"id": 1, "name": "Red"}, {"id": 2, "name": "Blue"}]`

#### `POST /<resource>/`
*   **Summary:** Create an Entry (e.g., Create a Color)
*   **Request Body:** `{"name": "Green"}`
*   **Success Response (201 Created):** `{"id": 3, "name": "Green"}`

#### `GET /<resource>/{id}/`
*   **Summary:** Retrieve an Entry by ID (e.g., Retrieve a Color)
*   **Success Response (200 OK):** `{"id": 1, "name": "Red"}`

#### `PUT /<resource>/{id}/`
*   **Summary:** Update an Entry (e.g., Update a Color)
*   **Request Body:** `{"name": "Dark Red"}`
*   **Success Response (200 OK):** `{"id": 1, "name": "Dark Red"}`

#### `DELETE /<resource>/{id}/`
*   **Summary:** Delete an Entry (e.g., Delete a Color)
*   **Success Response (204 No Content):** An empty response.

---

## Collection Management

APIs for managing user-specific collections and related entities.

### Collections Resource (`/collections/`)

Manages a user's personal stamp collections.

#### `GET /collections/`

Retrieves a list of all collections for the authenticated user.

*   **Summary:** List All Collections
*   **Success Response (200 OK):**
    ```json
    [
      {
        "id": 1,
        "user": "testuser",
        "name": "European Classics"
      }
    ]
    ```
*   **Error Responses:**
    *   **403 Forbidden:** If the API key is invalid or missing.

#### `POST /collections/`

Creates a new collection for the authenticated user.

*   **Summary:** Create a Collection
*   **Request Body:**
    ```json
    {
      "user": "testuser",
      "name": "American Commemoratives"
    }
    ```
*   **Success Response (201 Created):**
    ```json
    {
      "id": 2,
      "user": "testuser",
      "name": "American Commemoratives"
    }
    ```
*   **Error Responses:**
    *   **400 Bad Request:** If the request body is invalid.
    *   **403 Forbidden:** If the API key is invalid or missing.
    *   **404 Not Found:** If the user associated with the API key is not found.

#### `GET /collections/{id}/`

Retrieves a single collection by its ID.

*   **Summary:** Retrieve a Collection by ID
*   **URL Parameter:** `id` (integer, required) - The ID of the collection.
*   **Success Response (200 OK):**
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

#### `PUT /collections/{id}/`

*   **Summary:** Update a Collection
*   **URL Parameter:** `id` (integer, required) - The ID of the collection.
*   **Request Body:**
    ```json
    {
      "name": "Updated Collection Name"
    }
    ```
*   **Success Response (200 OK):**
    ```json
    {
      "id": 1,
      "user": "testuser",
      "name": "Updated Collection Name"
    }
    ```
*   **Error Responses:**
    *   **400 Bad Request:** If the request body is invalid.
    *   **403 Forbidden:** If the API key is invalid or missing.
    *   **404 Not Found:** If no collection with the given ID exists.


#### `DELETE /collections/{id}/`

*   **Summary:** Delete a Collection
*   **URL Parameter:** `id` (integer, required) - The ID of the collection to delete.
*   **Success Response (204 No Content):** An empty response indicating successful deletion.
*   **Error Responses:**
    *   **403 Forbidden:** If the API key is invalid or missing.
    *   **404 Not Found:** If no collection with the given ID exists.

### Collection Items Resource (`/collection_items/`)

Manages the items (stamps) within a specific collection, acting as a junction between `collections` and `stamps`.

#### `GET /collection_items/`

Retrieves a list of all items across all collections.

*   **Summary:** List All Collection Items
*   **Success Response (200 OK):**
    ```json
    [
      {
        "id": 1,
        "collection_id": 1,
        "stamp_id": 101
      }
    ]
    ```
*   **Error Responses:**
    *   **403 Forbidden:** If the API key is invalid or missing.

#### `POST /collection_items/`

Adds a stamp to a collection.

*   **Summary:** Add a Stamp to a Collection
*   **Request Body:**
    ```json
    {
      "collection_id": 1,
      "stamp_id": 102
    }
    ```
*   **Success Response (201 Created):**
    ```json
    {
      "id": 2,
      "collection_id": 1,
      "stamp_id": 102
    }
    ```
*   **Error Responses:**
    *   **400 Bad Request:** If the request body is invalid.
    *   **403 Forbidden:** If the API key is invalid or missing.


#### `GET /collection_items/{id}/`

Retrieves a specific collection item entry.

*   **Summary:** Retrieve a Collection Item by ID
*   **URL Parameter:** `id` (integer, required) - The ID of the collection item.
*   **Success Response (200 OK):**
    ```json
    {
      "id": 1,
      "collection_id": 1,
      "stamp_id": 101
    }
    ```
*   **Error Responses:**
    *   **403 Forbidden:** If the API key is invalid or missing.
    *   **404 Not Found:** If no collection item with the given ID exists.

#### `PUT /collection_items/{id}/`

*   **Summary:** Update a Collection Item
*   **URL Parameter:** `id` (integer, required) - The ID of the collection item.
*   **Request Body:**
    ```json
    {
      "stamp_id": 103
    }
    ```
*   **Success Response (200 OK):**
    ```json
    {
      "id": 1,
      "collection_id": 1,
      "stamp_id": 103
    }
    ```
*   **Error Responses:**
    *   **400 Bad Request:** If the request body is invalid.
    *   **403 Forbidden:** If the API key is invalid or missing.
    *   **404 Not Found:** If no collection item with the given ID exists.


#### `DELETE /collection_items/{id}/`

*   **Summary:** Remove a Stamp from a Collection
*   **URL Parameter:** `id` (integer, required) - The ID of the collection item to delete.
*   **Success Response (204 No Content):** An empty response indicating successful deletion.
*   **Error Responses:**
    *   **403 Forbidden:** If the API key is invalid or missing.
    *   **404 Not Found:** If no collection item with the given ID exists.

### Locations Resource (`/locations/`)

Manages geographical locations relevant to a user's collection (e.g., storage location, purchase location). This resource follows the standard RESTful pattern for Lookup Tables.

#### `GET /locations/`

Retrieves a list of all location entries.

*   **Summary:** List All Locations
*   **Success Response (200 OK):** `[{"id": 1, "name": "Main Album"}, {"id": 2, "name": "Safe Deposit Box"}]`
*   **Error Responses:**
    *   **403 Forbidden:** If the API key is invalid or missing.

#### `POST /locations/`

Creates a new location entry.

*   **Summary:** Create a Location
*   **Request Body:** `{"name": "Trade Binder"}`
*   **Success Response (201 Created):** `{"id": 3, "name": "Trade Binder"}`
*   **Error Responses:**
    *   **400 Bad Request:** If the request body is invalid.
    *   **403 Forbidden:** If the API key is invalid or missing.

#### `GET /locations/{id}/`

Retrieves a single location entry by its ID.

*   **Summary:** Retrieve a Location by ID
*   **URL Parameter:** `id` (integer, required) - The ID of the location.
*   **Success Response (200 OK):** `{"id": 1, "name": "Main Album"}`
*   **Error Responses:**
    *   **403 Forbidden:** If the API key is invalid or missing.
    *   **404 Not Found:** If no location with the given ID exists.

#### `PUT /locations/{id}/`

Updates an existing location entry.

*   **Summary:** Update a Location
*   **URL Parameter:** `id` (integer, required) - The ID of the location to update.
*   **Request Body:** `{"name": "Primary Album"}`
*   **Success Response (200 OK):** `{"id": 1, "name": "Primary Album"}`
*   **Error Responses:**
    *   **400 Bad Request:** If the request body is invalid.
    *   **403 Forbidden:** If the API key is invalid or missing.
    *   **404 Not Found:** If no location with the given ID exists.

#### `DELETE /locations/{id}/`

Deletes a location entry.

*   **Summary:** Delete a Location
*   **URL Parameter:** `id` (integer, required) - The ID of the location to delete.
*   **Success Response (204 No Content):** An empty response.
*   **Error Responses:**
    *   **403 Forbidden:** If the API key is invalid or missing.
    *   **404 Not Found:** If no location with the given ID exists.

### Condition Types Resource (`/condition_types/`)

Manages stamp condition types (e.g., Mint, Used). This resource follows the standard RESTful pattern for Lookup Tables.

#### `GET /condition_types/`

Retrieves a list of all condition type entries.

*   **Summary:** List All Condition Types
*   **Success Response (200 OK):** `[{"id": 1, "name": "Mint"}, {"id": 2, "name": "Used"}]`
*   **Error Responses:**
    *   **403 Forbidden:** If the API key is invalid or missing.

#### `POST /condition_types/`

Creates a new condition type entry.

*   **Summary:** Create a Condition Type
*   **Request Body:** `{"name": "Damaged"}`
*   **Success Response (201 Created):** `{"id": 3, "name": "Damaged"}`
*   **Error Responses:**
    *   **400 Bad Request:** If the request body is invalid.
    *   **403 Forbidden:** If the API key is invalid or missing.

#### `GET /condition_types/{id}/`

Retrieves a single condition type entry by its ID.

*   **Summary:** Retrieve a Condition Type by ID
*   **URL Parameter:** `id` (integer, required) - The ID of the condition type.
*   **Success Response (200 OK):** `{"id": 1, "name": "Mint"}`
*   **Error Responses:**
    *   **403 Forbidden:** If the API key is invalid or missing.
    *   **404 Not Found:** If no condition type with the given ID exists.

#### `PUT /condition_types/{id}/`

Updates an existing condition type entry.

*   **Summary:** Update a Condition Type
*   **Request Body:** `{"name": "Mint Never Hinged"}`
*   **Success Response (200 OK):** `{"id": 1, "name": "Mint Never Hinged"}`
*   **Error Responses:**
    *   **400 Bad Request:** If the request body is invalid.
    *   **403 Forbidden:** If the API key is invalid or missing.
    *   **404 Not Found:** If no condition type with the given ID exists.

#### `DELETE /condition_types/{id}/`

Deletes a condition type entry.

*   **Summary:** Delete a Condition Type
*   **URL Parameter:** `id` (integer, required) - The ID of the condition type to delete.
*   **Success Response (204 No Content):** An empty response.
*   **Error Responses:**
    *   **403 Forbidden:** If the API key is invalid or missing.
    *   **404 Not Found:** If no condition type with the given ID exists.

---

## User Management

APIs for managing users and their API keys.

### Users Resource

**Resource URL:** `/users/` 

#### `GET /users/`

Retrieves a list of all users.

*   **Summary:** List All Users
*   **Success Response (200 OK):**
    ```json
    [
      {
        "id": 1,
        "username": "testuser",
        "email": "test@example.com",
        "api_key": "some_api_key_string",
        "password_hash": "hashed_password_string"
      }
    ]
    ```
*   **Error Response (403 Forbidden):** If the API key is invalid or missing.

#### `POST /users/`

Creates a new user, generating a unique API key and password hash.

*   **Summary:** Create a New User
*   **Request Body:**
    ```json
    {
      "username": "newuser",
      "email": "new@example.com",
      "password": "a_strong_password"
    }
    ```
*   **Success Response (201 Created):**
    ```json
    {
      "id": 2,
      "username": "newuser",
      "email": "new@example.com",
      "api_key": "generated_api_key",
      "password_hash": "generated_password_hash"
    }
    ```
*   **Error Responses:**
    *   **400 Bad Request:** If the request body is invalid (e.g., missing fields, username already exists).
    *   **403 Forbidden:** If the API key is invalid or missing.

#### `GET /users/{id}/`

Retrieves a single user by their ID.

*   **Summary:** Retrieve a User by ID
*   **URL Parameter:** `id` (integer, required) - The unique ID of the user.
*   **Success Response (200 OK):**
    ```json
    {
      "id": 1,
      "username": "testuser",
      "email": "test@example.com",
      "api_key": "some_api_key_string",
      "password_hash": "hashed_password_string"
    }
    ```
*   **Error Responses:**
    *   **403 Forbidden:** If the API key is invalid or missing.
    *   **404 Not Found:** If no user with the given ID exists.

#### `PUT /users/{id}/`

Updates an existing user's details.

*   **Summary:** Update a User
*   **URL Parameter:** `id` (integer, required) - The unique ID of the user to update.
*   **Request Body:**
    ```json
    {
      "username": "updated_username",
      "email": "updated_email@example.com",
      "password": "new_password"
    }
    ```
*   **Success Response (200 OK):** The full updated user object.
*   **Error Responses:**
    *   **400 Bad Request:** If the request body is invalid.
    *   **403 Forbidden:** If the API key is invalid or missing.
    *   **404 Not Found:** If no user with the given ID exists.

#### `DELETE /users/{id}/`

Deletes a user.

*   **Summary:** Delete a User
*   **URL Parameter:** `id` (integer, required) - The unique ID of the user to delete.
*   **Success Response (200 OK):** A confirmation message indicating successful deletion.
*   **Error Responses:**
    *   **403 Forbidden:** If the API key is invalid or missing.
    *   **404 Not Found:** If no user with the given ID exists.