# Stamps API Documentations

This document provides an overview of the available API endpoints for the Stamps application.

## General Information

- The base URL for the API is not explicitly defined and is configured via environment variables. Placeholders like `{SERVER_URL_V1}` are used in this document.
- All responses are wrapped in a standardized JSON format.

---

## Years API

**Base Path:** `/{SERVER_URL_V1}/{YEARS_ENDPOINT}`

This API manages the year entries in the database.

### `GET /`

- **Summary:** List All Years
- **Description:** Retrieves a list of all year entries currently stored in the database.
- **Responses:**
    - `200 OK`: A list of years was successfully retrieved.
        - **Body:** `[{"id": 1, "year": 2023}, {"id": 2, "year": 2024}]`

### `POST /`

- **Summary:** Create a New Year
- **Description:** Adds a new year entry to the database.
- **Request Body:** `{ "year": integer }`
- **Responses:**
    - `201 Created`: The year was created successfully.
        - **Body:** `{"id": 1, "year": 2025}`
    - `400 Bad Request`: The request payload was invalid.

### `GET /{id}`

- **Summary:** Retrieve a Year by ID
- **Description:** Fetches the details of a specific year entry by its unique identifier.
- **Responses:**
    - `200 OK`: The requested year's data was retrieved successfully.
        - **Body:** `{"id": 1, "year": 2023}`
    - `404 Not Found`: No year was found for the provided ID.

### `PUT /{id}`

- **Summary:** Update a Year
- **Description:** Updates an existing year entry identified by its ID.
- **Request Body:** `{ "year": integer }`
- **Responses:**
    - `200 OK`: The year was updated successfully.
        - **Body:** `{ "id": integer, "year": integer }`
    - `400 Bad Request`: The request payload was invalid.
    - `404 Not Found`: The year with the specified ID was not found.

### `DELETE /{id}`

- **Summary:** Delete a Year
- **Description:** Deletes a year entry from the database using its ID.
- **Responses:**
    - `200 OK`: The year was deleted successfully.
    - `404 Not Found`: The year with the specified ID was not found.

---

## Config API

**Base Path:** `/{SERVER_URL_V1}/{CONFIG_ENDPOINT}`

This API manages system configuration settings.

### `GET /`

- **Summary:** List All Configuration Entries
- **Description:** Retrieves a comprehensive list of all configuration key-value pairs.
- **Responses:**
    - `200 OK`: A list of all configuration entries was successfully retrieved.
        - **Body:** `[{ "id": integer, "property": "string", "value": "string" }]`

### `POST /`

- **Summary:** Create a Configuration Entry
- **Description:** Adds a new configuration key-value pair to the database.
- **Request Body:** `{ "property": "string", "value": "string" }`
- **Responses:**
    - `201 Created`: The configuration entry was created successfully.
        - **Body:** `{ "id": integer, "property": "string", "value": "string" }`
    - `400 Bad Request`: The request payload was invalid.

### `GET /{id}`

- **Summary:** Retrieve a Configuration Entry by ID
- **Description:** Fetches a specific configuration entry using its unique ID.
- **Responses:**
    - `200 OK`: The configuration entry was retrieved successfully.
        - **Body:** `{ "id": integer, "property": "string", "value": "string" }`
    - `404 Not Found`: No configuration entry was found for the provided ID.

### `PUT /{id}`

- **Summary:** Update a Configuration Entry
- **Description:** Updates an existing configuration entry identified by its ID.
- **Request Body:** `{ "property": "string", "value": "string" }`
- **Responses:**
    - `200 OK`: The configuration entry was updated successfully.
        - **Body:** `{ "id": integer, "property": "string", "value": "string" }`
    - `400 Bad Request`: The request payload was invalid.
    - `404 Not Found`: The configuration entry with the specified ID was not found.

### `DELETE /{id}`

- **Summary:** Delete a Configuration Entry
- **Description:** Permanently removes a configuration entry from the database.
- **Responses:**
    - `200 OK`: The configuration entry was deleted successfully.
    - `404 Not Found`: The configuration entry with the specified ID was not found.

---

## Stamp Types API

**Base Path:** `/{SERVER_URL_V1}/{STAMP_TYPES_ENDPOINT}`

This API manages the types of stamps available.

### `GET /`

- **Summary:** List All Stamp Types
- **Description:** Retrieves a list of all stamp type entries.
- **Responses:**
    - `200 OK`: A list of stamp types was successfully retrieved.
        - **Body:** `[{ "id": integer, "name": "string" }]`

### `POST /`

- **Summary:** Create a New Stamp Type
- **Description:** Adds a new stamp type entry to the database.
- **Request Body:** `{ "name": "string" }`
- **Responses:**
    - `201 Created`: The stamp type was created successfully.
        - **Body:** `{ "id": integer, "name": "string" }`
    - `400 Bad Request`: The request payload was invalid.

### `GET /{id}`

- **Summary:** Retrieve a Stamp Type by ID
- **Description:** Fetches the details of a specific stamp type entry by its unique identifier.
- **Responses:**
    - `200 OK`: The requested stamp type's data was retrieved successfully.
        - **Body:** `{ "id": integer, "name": "string" }`
    - `404 Not Found`: No stamp type was found for the provided ID.

### `PUT /{id}`

- **Summary:** Update a Stamp Type
- **Description:** Updates an existing stamp type entry identified by its ID.
- **Request Body:** `{ "name": "string" }`
- **Responses:**
    - `200 OK`: The stamp type was updated successfully.
        - **Body:** `{ "id": integer, "name": "string" }`
    - `400 Bad Request`: The request payload was invalid.
    - `404 Not Found`: The stamp type with the specified ID was not found.

### `DELETE /{id}`

- **Summary:** Delete a Stamp Type
- **Description:** Deletes a stamp type entry from the database using its ID.
- **Responses:**
    - `200 OK`: The stamp type was deleted successfully.
    - `404 Not Found`: The stamp type with the specified ID was not found.

---

## Paper Types API

**Base Path:** `/{SERVER_URL_V1}/{PAPER_TYPES_ENDPOINT}`

This API manages the types of paper used for stamps.

### `GET /`

- **Summary:** List All Paper Types
- **Description:** Retrieves a list of all paper type entries.
- **Responses:**
    - `200 OK`: A list of paper types was successfully retrieved.
        - **Body:** `[{ "id": integer, "name": "string" }]`

### `POST /`

- **Summary:** Create a New Paper Type
- **Description:** Adds a new paper type entry to the database.
- **Request Body:** `{ "name": "string" }`
- **Responses:**
    - `201 Created`: The paper type was created successfully.
        - **Body:** `{ "id": integer, "name": "string" }`
    - `400 Bad Request`: The request payload was invalid.

### `GET /{id}`

- **Summary:** Retrieve a Paper Type by ID
- **Description:** Fetches the details of a specific paper type entry by its unique identifier.
- **Responses:**
    - `200 OK`: The requested paper type's data was retrieved successfully.
        - **Body:** `{ "id": integer, "name": "string" }`
    - `404 Not Found`: No paper type was found for the provided ID.

### `PUT /{id}`

- **Summary:** Update a Paper Type
- **Description:** Updates an existing paper type entry identified by its ID.
- **Request Body:** `{ "name": "string" }`
- **Responses:**
    - `200 OK`: The paper type was updated successfully.
        - **Body:** `{ "id": integer, "name": "string" }`
    - `400 Bad Request`: The request payload was invalid.
    - `404 Not Found`: The paper type with the specified ID was not found.

### `DELETE /{id}`

- **Summary:** Delete a Paper Type
- **Description:** Deletes a paper type entry from the database using its ID.
- **Responses:**
    - `200 OK`: The paper type was deleted successfully.
    - `404 Not Found`: The paper type with the specified ID was not found.

---

## Locations API

**Base Path:** `/{SERVER_URL_V1}/{LOCATIONS_ENDPOINT}`

This API manages the locations of stamps.

### `GET /`

- **Summary:** List All Locations
- **Description:** Retrieves a list of all location entries.
- **Responses:**
    - `200 OK`: A list of locations was successfully retrieved.
        - **Body:** `[{ "id": integer, "name": "string" }]`

### `POST /`

- **Summary:** Create a New Location
- **Description:** Adds a new location entry to the database.
- **Request Body:** `{ "name": "string" }`
- **Responses:**
    - `201 Created`: The location was created successfully.
        - **Body:** `{ "id": integer, "name": "string" }`
    - `400 Bad Request`: The request payload was invalid.

### `GET /{id}`

- **Summary:** Retrieve a Location by ID
- **Description:** Fetches the details of a specific location entry by its unique identifier.
- **Responses:**
    - `200 OK`: The requested location's data was retrieved successfully.
        - **Body:** `{ "id": integer, "name": "string" }`
    - `404 Not Found`: No location was found for the provided ID.

### `PUT /{id}`

- **Summary:** Update a Location
- **Description:** Updates an existing location entry identified by its ID.
- **Request Body:** `{ "name": "string" }`
- **Responses:**
    - `200 OK`: The location was updated successfully.
        - **Body:** `{ "id": integer, "name": "string" }`
    - `400 Bad Request`: The request payload was invalid.
    - `404 Not Found`: The location with the specified ID was not found.

### `DELETE /{id}`

- **Summary:** Delete a Location
- **Description:** Deletes a location entry from the database using its ID.
- **Responses:**
    - `200 OK`: The location was deleted successfully.
    - `404 Not Found`: The location with the specified ID was not found.

---

## Countries API

**Base Path:** `/{SERVER_URL_V1}/{COUNTRIES_ENDPOINT}`

This API manages the countries of origin for stamp issues.

### `GET /`

- **Summary:** List All Countries
- **Description:** Retrieves a list of all country entries.
- **Responses:**
    - `200 OK`: A list of countries was successfully retrieved.
        - **Body:** `[{ "id": integer, "name": "string" }]`

### `POST /`

- **Summary:** Create a New Country
- **Description:** Adds a new country entry to the database.
- **Request Body:** `{ "name": "string" }`
- **Responses:**
    - `201 Created`: The country was created successfully.
        - **Body:** `{ "id": integer, "name": "string" }`
    - `400 Bad Request`: The request payload was invalid.

### `GET /{id}`

- **Summary:** Retrieve a Country by ID
- **Description:** Fetches the details of a specific country entry by its unique identifier.
- **Responses:**
    - `200 OK`: The requested country's data was retrieved successfully.
        - **Body:** `{ "id": integer, "name": "string" }`
    - `404 Not Found`: No country was found for the provided ID.

### `PUT /{id}`

- **Summary:** Update a Country
- **Description:** Updates an existing country entry identified by its ID.
- **Request Body:** `{ "name": "string" }`
- **Responses:**
    - `200 OK`: The country was updated successfully.
        - **Body:** `{ "id": integer, "name": "string" }`
    - `400 Bad Request`: The request payload was invalid.
    - `404 Not Found`: The country with the specified ID was not found.

### `DELETE /{id}`

- **Summary:** Delete a Country
- **Description:** Deletes a country entry from the database using its ID.
- **Responses:**
    - `200 OK`: The country was deleted successfully.
    - `404 Not Found`: The country with the specified ID was not found.

---

## Issues API

**Base Path:** `/{SERVER_URL_V1}/{ISSUES_ENDPOINT}`

This API manages the stamp issues in the database.

### `GET /`

- **Summary:** List All Issues
- **Description:** Retrieves a list of all issue entries currently stored in the database.
- **Responses:**
    - `200 OK`: A list of issues was successfully retrieved.
        - **Body:** `[{ "id": 1, "year_id": 1, "date": "2023-01-15", "country_id": 1, "name": "Historic Monuments", "number_issued": 10000, "value": 5.50, "number_owned": 1, "number_stamps": 5, "stamp_type": 1, "paper_type": 1, "total_value": 5.50, "description": "A series on historic monuments.", "located_in": 1, "note": "First day cover.", "perforated": "13.5" }]`

### `POST /`

- **Summary:** Create a New Issue
- **Description:** Adds a new issue entry to the database.
- **Request Body:** `{ "year_id": 1, "date": "2024-02-20", "country_id": 2, "name": "Flora and Fauna", "number_issued": 15000, "value": 7.00, "number_owned": 0, "number_stamps": 6, "stamp_type": 2, "paper_type": 1, "description": "A series on local wildlife.", "located_in": 2, "note": "", "perforated": "14" }`
- **Responses:**
    - `201 Created`: The issue was created successfully.
        - **Body:** `{ "id": 2, "year_id": 1, "date": "2024-02-20", "country_id": 2, "name": "Flora and Fauna", ... }`
    - `400 Bad Request`: The request payload was invalid.

### `GET /{id}`

- **Summary:** Retrieve an Issue by ID
- **Description:** Fetches the details of a specific issue entry by its unique identifier.
- **Responses:**
    - `200 OK`: The requested issue's data was retrieved successfully.
        - **Body:** `{ "id": 1, "year_id": 1, "date": "2023-01-15", "country_id": 1, "name": "Historic Monuments", ... }`
    - `404 Not Found`: No issue was found for the provided ID.

### `PUT /{id}`

- **Summary:** Update an Issue
- **Description:** Updates an existing issue entry identified by its ID.
- **Request Body:** `{ "name": "Updated Issue Name", "note": "Updated note." }`
- **Responses:**
    - `200 OK`: The issue was updated successfully.
        - **Body:** `{ "id": 1, "name": "Updated Issue Name", "note": "Updated note.", ... }`
    - `400 Bad Request`: The request payload was invalid.
    - `404 Not Found`: The issue with the specified ID was not found.

### `DELETE /{id}`

- **Summary:** Delete an Issue
- **Description:** Deletes an issue entry from the database using its ID.
- **Responses:**
    - `200 OK`: The issue was deleted successfully.
    - `404 Not Found`: The issue with the specified ID was not found.

---

## Stamps API

**Base Path:** `/{SERVER_URL_V1}/{STAMPS_ENDPOINT}`

This API manages individual stamps within an issue.

### `GET /`

- **Summary:** List All Stamps
- **Description:** Retrieves a list of all stamp entries.
- **Responses:**
    - `200 OK`: A list of stamps was successfully retrieved.
        - **Body:** `[{ "id": 1, "issue_id": 1, "edifil_code": "4567", "face_value": "1.00", "name": "The Castle", "others_code": "SG123", "image": "/images/stamp1.jpg", "color": "Blue" }]`

### `POST /`

- **Summary:** Create a New Stamp
- **Description:** Adds a new stamp entry to the database, linked to an issue.
- **Request Body:** `{ "issue_id": 1, "edifil_code": "4568", "face_value": "0.50", "name": "The Bridge", "color": "Green" }`
- **Responses:**
    - `201 Created`: The stamp was created successfully.
        - **Body:** `{ "id": 2, "issue_id": 1, "edifil_code": "4568", "face_value": "0.50", "name": "The Bridge", ... }`
    - `400 Bad Request`: The request payload was invalid.

### `GET /{id}`

- **Summary:** Retrieve a Stamp by ID
- **Description:** Fetches the details of a specific stamp entry by its unique identifier.
- **Responses:**
    - `200 OK`: The requested stamp's data was retrieved successfully.
        - **Body:** `{ "id": 1, "issue_id": 1, "edifil_code": "4567", ... }`
    - `404 Not Found`: No stamp was found for the provided ID.

### `PUT /{id}`

- **Summary:** Update a Stamp
- **Description:** Updates an existing stamp entry identified by its ID.
- **Request Body:** `{ "edifil_code": "4567-A", "color": "Dark Blue" }`
- **Responses:**
    - `200 OK`: The stamp was updated successfully.
        - **Body:** `{ "id": 2, "edifil_code": "4567-A", "color": "Dark Blue", ... }`
    - `400 Bad Request`: The request payload was invalid.
    - `404 Not Found`: The stamp with the specified ID was not found.

### `DELETE /{id}`

- **Summary:** Delete a Stamp
- **Description:** Deletes a stamp entry from the database using its ID.
- **Responses:**
    - `200 OK`: The stamp was deleted successfully.
    - `404 Not Found`: The stamp with the specified ID was not found.
