# Users API Documentation

Welcome to the API documentation for the Users resource. This document provides detailed information about the RESTful endpoints for managing users of the application.

The Users API allows for creating, viewing, updating, and deleting user accounts. It also handles the generation and management of user-specific API keys and password hashes.

## Resource URL

The base URL for all version 1 endpoints for this resource is:

`/stamps_server/api/v1/users/`

## Authentication

All endpoints are protected and require authentication via an API key or a password hash provided in the request headers. Please refer to the main `readme_api.md` for detailed authentication instructions.

---

## Model Description

The `UserCollection` model represents a user of the application.

| Field | Type | Description |
| :--- | :--- | :--- |
| `id` | Integer | The unique identifier for the user. |
| `username` | String | The user's unique username. |
| `email` | Email | The user's unique email address. |
| `password_hash` | String | The securely hashed password for the user. |
| `api_key` | String | The unique API key assigned to the user for authentication. |
| `first_name` | String | The user's first name. |
| `last_name` | String | The user's last name. |
| `registration_date` | DateTime | The date and time the user registered. |
| `is_active` | Boolean | Designates whether this user should be treated as active. |

---

## API Endpoints

### `GET /users/`

Retrieves a list of all users.

*   **Summary:** List All Users
*   **Success Response (200 OK):**
    A JSON array of user objects.
    ```json
    [
      {
        "id": 1,
        "username": "testuser",
        "email": "test@example.com",
        "api_key": "some_api_key_string",
        "password_hash": "hashed_password_string",
        "first_name": "Test",
        "last_name": "User",
        "registration_date": "2024-01-01T12:00:00Z",
        "is_active": true
      }
    ]
    ```
*   **Error Responses:**
    *   **403 Forbidden:** If the API key is invalid or missing.

### `POST /users/`

Creates a new user, generating a unique API key and password hash.

*   **Summary:** Create a New User
*   **Request Body:**
    A JSON object representing the new user.
    ```json
    {
      "username": "newuser",
      "email": "new@example.com",
      "password": "a_strong_password",
      "first_name": "New",
      "last_name": "User"
    }
    ```
*   **Success Response (201 Created):**
    The full, newly created user object.
    ```json
    {
      "id": 2,
      "username": "newuser",
      "email": "new@example.com",
      "api_key": "generated_api_key",
      "password_hash": "generated_password_hash",
      "first_name": "New",
      "last_name": "User",
      "registration_date": "2024-05-21T10:30:00Z",
      "is_active": true
    }
    ```
*   **Error Responses:**
    *   **400 Bad Request:** If the request body is invalid (e.g., missing fields, username or email already exists).
    *   **403 Forbidden:** If the API key is invalid or missing.

### `GET /users/{id}/`

Retrieves a single, specific user by their unique ID.

*   **Summary:** Retrieve a User by ID
*   **URL Parameter:** `id` (integer, required) - The unique ID of the user.
*   **Success Response (200 OK):**
    The requested user object.
    ```json
    {
      "id": 1,
      "username": "testuser",
      "email": "test@example.com",
      "api_key": "some_api_key_string",
      "password_hash": "hashed_password_string",
      "first_name": "Test",
      "last_name": "User",
      "registration_date": "2024-01-01T12:00:00Z",
      "is_active": true
    }
    ```
*   **Error Responses:**
    *   **403 Forbidden:** If the API key is invalid or missing.
    *   **404 Not Found:** If no user with the given ID exists.

### `PUT /users/{id}/`

Updates an existing user's details. This method supports partial updates.

*   **Summary:** Update a User
*   **URL Parameter:** `id` (integer, required) - The unique ID of the user to update.
*   **Request Body:**
    A JSON object containing the fields to be updated.
    ```json
    {
      "email": "updated_email@example.com",
      "is_active": false
    }
    ```
*   **Success Response (200 OK):**
    The full, updated user object.
    ```json
    {
      "id": 1,
      "username": "testuser",
      "email": "updated_email@example.com",
      "api_key": "some_api_key_string",
      "password_hash": "hashed_password_string",
      "first_name": "Test",
      "last_name": "User",
      "registration_date": "2024-01-01T12:00:00Z",
      "is_active": false
    }
    ```
*   **Error Responses:**
    *   **400 Bad Request:** If the request body contains invalid data (e.g., a duplicate username or email).
    *   **403 Forbidden:** If the API key is invalid or missing.
    *   **404 Not Found:** If no user with the given ID exists.

### `DELETE /users/{id}/`

Permanently deletes a user.

*   **Summary:** Delete a User
*   **URL Parameter:** `id` (integer, required) - The ID of the user to delete.
*   **Success Response (200 OK):**
    A confirmation message indicating successful deletion.
    ```json
    {
        "message": "User with id 1 has been deleted successfully."
    }
    ```
*   **Error Responses:**
    *   **403 Forbidden:** If the API key is invalid or missing.
    *   **404 Not Found:** If no user with the given ID exists.