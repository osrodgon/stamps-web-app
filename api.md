# Stamps Collection API Documentation

This document provides a detailed description of the RESTful API endpoints for the Stamp Collection application.

## Years API Endpoints

This document details the RESTful API endpoints for managing `Year` entities in the stamp collection database.

**Base URL:** `/api/v1/years/`

---

#### 1. List and Create Years

**Endpoint:** `/api/v1/years/`

##### `GET` /

-   **Summary:** List All Years
-   **Description:** Retrieves a list of all year entries currently stored in the database. The response will contain an array of year objects.
-   **Responses:**
    -   **`200 OK`**: A list of years was successfully retrieved.
        ```json
        {
          "data": [
            {
              "id": 1,
              "year": 2023
            },
            {
              "id": 2,
              "year": 2024
            }
          ],
          "success": true,
          "message": "Retrieved successfully",
          "errors": null
        }
        ```

##### `POST` /

-   **Summary:** Create a New Year
-   **Description:** Adds a new year entry to the database. A successful creation returns the newly created year object with a `201 Created` status code.
-   **Request Body:**
    ```json
    {
      "year": 2025
    }
    ```
-   **Responses:**
    -   **`201 Created`**: The year was created successfully.
        ```json
        {
          "data": {
            "id": 3,
            "year": 2025
          },
          "success": true,
          "message": "Created successfully",
          "errors": null
        }
        ```
    -   **`400 Bad Request`**: The request payload was invalid (e.g., missing a required field).
        ```json
        {
          "data": null,
          "success": false,
          "message": "Request failed",
          "errors": {
            "information": "{'year': ['This field is required.']}"
          }
        }
        ```

---

#### 2. Retrieve, Update, and Delete a Specific Year

**Endpoint:** `/api/v1/years/{id}`

##### `GET` /{id}

-   **Summary:** Retrieve a Year by ID
-   **Description:** Fetches the details of a specific year entry by its unique identifier. If the year exists, its data is returned. Otherwise, a `404 Not Found` error is returned.
-   **URL Parameters:**
    -   `id` (integer, required): The unique ID of the year to retrieve.
-   **Responses:**
    -   **`200 OK`**: The requested year's data was retrieved successfully.
        ```json
        {
          "data": {
            "id": 1,
            "year": 2023
          },
          "success": true,
          "message": "Retrieved successfully",
          "errors": null
        }
        ```
    -   **`404 Not Found`**: No year was found for the provided ID.
        ```json
        {
          "data": null,
          "success": false,
          "message": "Request failed",
          "errors": {
            "information": "Year with id: 999 not found"
          }
        }
        ```

##### `PUT` /{id}

-   **Summary:** Update a Year
-   **Description:** Updates an existing year entry identified by its ID. A complete payload with all required fields is expected.
-   **URL Parameters:**
    -   `id` (integer, required): The unique ID of the year to update.
-   **Request Body:**
    ```json
    {
      "year": 2026
    }
    ```
-   **Responses:**
    -   **`200 OK`**: The year was updated successfully.
        ```json
        {
          "data": {
            "id": 1,
            "year": 2026
          },
          "success": true,
          "message": "Updated successfully",
          "errors": null
        }
        ```
    -   **`400 Bad Request`**: The request payload was invalid.
        ```json
        {
          "data": null,
          "success": false,
          "message": "Request failed",
          "errors": {
            "information": "{'year': ['A valid integer is required.']}"
          }
        }
        ```
    -   **`404 Not Found`**: The year with the specified ID was not found.
        ```json
        {
          "data": null,
          "success": false,
          "message": "Request failed",
          "errors": {
            "information": "Cannot update year with id: 999. Not found in the database"
          }
        }
        ```

##### `DELETE` /{id}

-   **Summary:** Delete a Year
-   **Description:** Deletes a year entry from the database using its ID.
-   **URL Parameters:**
    -   `id` (integer, required): The unique ID of the year to delete.
-   **Responses:**
    -   **`200 OK`**: The year was deleted successfully.
        ```json
        {
          "data": {
            "information": "Successfully deleted year with id: 1"
          },
          "success": true,
          "message": "Deleted successfully",
          "errors": null
        }
        ```
    -   **`404 Not Found`**: The year with the specified ID was not found.
        ```json
        {
          "data": null,
          "success": false,
          "message": "Request failed",
          "errors": {
            "information": "Cannot delete year with id: 999. Not found in the database"
          }
        }
        ```

## Config API Endpoints

This document details the RESTful API endpoints for managing `Config` entities in the stamp collection database. These endpoints allow for managing system-level configuration settings.

**Base URL:** `/api/v1/config/`

---

#### 1. List and Create Configuration Entries

**Endpoint:** `/api/v1/config/`

##### `GET` /

-   **Summary:** List All Configuration Entries
-   **Description:** Retrieves a comprehensive list of all configuration key-value pairs stored in the system.
-   **Responses:**
    -   **`200 OK`**: A list of all configuration entries was successfully retrieved.
        ```json
        {
          "data": [
            {
              "property": "theme",
              "value": "dark"
            },
            {
              "property": "language",
              "value": "en"
            }
          ],
          "success": true,
          "message": "Retrieved successfully",
          "errors": null
        }
        ```

##### `POST` /

-   **Summary:** Create a Configuration Entry
-   **Description:** Adds a new configuration key-value pair to the database. The request body must contain the 'property' and 'value'.
-   **Request Body:**
    ```json
    {
      "property": "show_tutorials",
      "value": "true"
    }
    ```
-   **Responses:**
    -   **`201 Created`**: The configuration entry was created successfully.
        ```json
        {
          "data": {
            "property": "show_tutorials",
            "value": "true"
          },
          "success": true,
          "message": "Created successfully",
          "errors": null
        }
        ```
    -   **`400 Bad Request`**: The request payload was invalid or missing required fields.
        ```json
        {
          "data": null,
          "success": false,
          "message": "Request failed",
          "errors": {
            "information": "{'property': ['This field is required.']}"
          }
        }
        ```

---

#### 2. Retrieve, Update, and Delete a Specific Configuration Entry

**Endpoint:** `/api/v1/config/{id}`

##### `GET` /{id}

-   **Summary:** Retrieve a Configuration Entry by ID
-   **Description:** Fetches a specific configuration entry using its unique ID (the property name).
-   **URL Parameters:**
    -   `id` (string, required): The unique property name of the configuration entry to retrieve.
-   **Responses:**
    -   **`200 OK`**: The configuration entry was retrieved successfully.
        ```json
        {
          "data": {
            "property": "theme",
            "value": "dark"
          },
          "success": true,
          "message": "Retrieved successfully",
          "errors": null
        }
        ```
    -   **`404 Not Found`**: No configuration entry was found for the provided ID.
        ```json
        {
          "data": null,
          "success": false,
          "message": "Request failed",
          "errors": {
            "information": "Config entry for id: 999 not found"
          }
        }
        ```

##### `PUT` /{id}

-   **Summary:** Update a Configuration Entry
-   **Description:** Updates an existing configuration entry identified by its ID. The request body can contain a partial or full update.
-   **URL Parameters:**
    -   `id` (string, required): The unique property name of the configuration entry to update.
-   **Request Body:**
    ```json
    {
      "value": "light"
    }
    ```
-   **Responses:**
    -   **`200 OK`**: The configuration entry was updated successfully.
        ```json
        {
          "data": {
            "property": "theme",
            "value": "light"
          },
          "success": true,
          "message": "Updated successfully",
          "errors": null
        }
        ```
    -   **`400 Bad Request`**: The request payload was invalid (e.g., contained an unknown field).
        ```json
        {
          "data": null,
          "success": false,
          "message": "Request failed",
          "errors": {
            "information": "{'unsupported_field': ['This field is not allowed.']}"
          }
        }
        ```
    -   **`404 Not Found`**: The configuration entry with the specified ID was not found.
        ```json
        {
          "data": null,
          "success": false,
          "message": "Request failed",
          "errors": {
            "information": "Cannot update config entry with id: 999. Not found."
          }
        }
        ```

##### `DELETE` /{id}

-   **Summary:** Delete a Configuration Entry
-   **Description:** Permanently removes a configuration entry from the database using its ID.
-   **URL Parameters:**
    -   `id` (string, required): The unique property name of the configuration entry to delete.
-   **Responses:**
    -   **`200 OK`**: The configuration entry was deleted successfully.
        ```json
        {
          "data": {
            "information": "Successfully deleted config entry with id: theme"
          },
          "success": true,
          "message": "Deleted successfully",
          "errors": null
        }
        ```
    -   **`404 Not Found`**: The configuration entry with the specified ID was not found.
        ```json
        {
          "data": null,
          "success": false,
          "message": "Request failed",
          "errors": {
            "information": "Cannot delete config entry with id: 999. Not found."
          }
        }
        ```

## Stamp Types API Endpoints

This document details the RESTful API endpoints for managing `Stamp Type` entities in the stamp collection database.

**Base URL:** `/api/v1/stamp-types/`

---

#### 1. List and Create Stamp Types

**Endpoint:** `/api/v1/stamp-types/`

##### `GET` /

-   **Summary:** List All Stamp Types
-   **Description:** Retrieves a list of all stamp type entries currently stored in the database.
-   **Responses:**
    -   **`200 OK`**: A list of stamp types was successfully retrieved.
        ```json
        {
          "data": [
            {
              "id": 1,
              "name": "Commemorative"
            },
            {
              "id": 2,
              "name": "Definitive"
            }
          ],
          "success": true,
          "message": "Retrieved successfully",
          "errors": null
        }
        ```

##### `POST` /

-   **Summary:** Create a New Stamp Type
-   **Description:** Adds a new stamp type entry to the database. A successful creation returns the newly created stamp type object with a `201 Created` status code.
-   **Request Body:**
    ```json
    {
      "name": "Airmail"
    }
    ```
-   **Responses:**
    -   **`201 Created`**: The stamp type was created successfully.
        ```json
        {
          "data": {
            "id": 3,
            "name": "Airmail"
          },
          "success": true,
          "message": "Created successfully",
          "errors": null
        }
        ```
    -   **`400 Bad Request`**: The request payload was invalid (e.g., missing a required field).
        ```json
        {
          "data": null,
          "success": false,
          "message": "Request failed",
          "errors": {
            "information": "{'name': ['This field is required.']}"
          }
        }
        ```

---

#### 2. Retrieve, Update, and Delete a Specific Stamp Type

**Endpoint:** `/api/v1/stamp-types/{id}`

##### `GET` /{id}

-   **Summary:** Retrieve a Stamp Type by ID
-   **Description:** Fetches the details of a specific stamp type entry by its unique identifier.
-   **URL Parameters:**
    -   `id` (integer, required): The unique ID of the stamp type to retrieve.
-   **Responses:**
    -   **`200 OK`**: The requested stamp type's data was retrieved successfully.
        ```json
        {
          "data": {
            "id": 1,
            "name": "Commemorative"
          },
          "success": true,
          "message": "Retrieved successfully",
          "errors": null
        }
        ```
    -   **`404 Not Found`**: No stamp type was found for the provided ID.
        ```json
        {
          "data": null,
          "success": false,
          "message": "Request failed",
          "errors": {
            "information": "StampType with id: 999 not found"
          }
        }
        ```

##### `PUT` /{id}

-   **Summary:** Update a Stamp Type
-   **Description:** Updates an existing stamp type entry identified by its ID. A complete payload with all required fields is expected.
-   **URL Parameters:**
    -   `id` (integer, required): The unique ID of the stamp type to update.
-   **Request Body:**
    ```json
    {
      "name": "Special"
    }
    ```
-   **Responses:**
    -   **`200 OK`**: The stamp type was updated successfully.
        ```json
        {
          "data": {
            "id": 1,
            "name": "Special"
          },
          "success": true,
          "message": "Updated successfully",
          "errors": null
        }
        ```
    -   **`400 Bad Request`**: The request payload was invalid.
        ```json
        {
          "data": null,
          "success": false,
          "message": "Request failed",
          "errors": {
            "information": "{'name': ['This field may not be blank.']}"
          }
        }
        ```
    -   **`404 Not Found`**: The stamp type with the specified ID was not found.
        ```json
        {
          "data": null,
          "success": false,
          "message": "Request failed",
          "errors": {
            "information": "Cannot update StampType with id: 999. Not found in the database"
          }
        }
        ```

##### `DELETE` /{id}

-   **Summary:** Delete a Stamp Type
-   **Description:** Deletes a stamp type entry from the database using its ID.
-   **URL Parameters:**
    -   `id` (integer, required): The unique ID of the stamp type to delete.
-   **Responses:**
    -   **`200 OK`**: The stamp type was deleted successfully.
        ```json
        {
          "data": {
            "information": "Successfully deleted StampType with id: 1"
          },
          "success": true,
          "message": "Deleted successfully",
          "errors": null
        }
        ```
    -   **`404 Not Found`**: The stamp type with the specified ID was not found.
        ```json
        {
          "data": null,
          "success": false,
          "message": "Request failed",
          "errors": {
            "information": "Cannot delete StampType with id: 999. Not found in the database"
          }
        }
        ```

## Issues API Endpoints

TBD. This section will contain the API documentation for managing Issues.

## Stamps API Endpoints

TBD. This section will contain the API documentation for managing Stamps.

## Countries API Endpoints

TBD. This section will contain the API documentation for managing Countries.

## Locations API Endpoints

This document details the RESTful API endpoints for managing `Location` entities in the stamp collection database.

**Base URL:** `/api/v1/locations/`

---

#### 1. List and Create Locations

**Endpoint:** `/api/v1/locations/`

##### `GET` /

-   **Summary:** List All Locations
-   **Description:** Retrieves a list of all location entries currently stored in the database. The response will contain an array of location objects.
-   **Responses:**
    -   **`200 OK`**: A list of locations was successfully retrieved.
        ```json
        {
          "data": [
            {
              "id": 1,
              "name": "United States",
              "code": "USA"
            },
            {
              "id": 2,
              "name": "Germany",
              "code": "DEU"
            }
          ],
          "success": true,
          "message": "Retrieved successfully",
          "errors": null
        }
        ```

##### `POST` /

-   **Summary:** Create a New Location
-   **Description:** Adds a new location entry to the database. A successful creation returns the newly created location object with a `201 Created` status code.
-   **Request Body:**
    ```json
    {
      "name": "France",
      "code": "FRA"
    }
    ```
-   **Responses:**
    -   **`201 Created`**: The location was created successfully.
        ```json
        {
          "data": {
            "id": 3,
            "name": "France",
            "code": "FRA"
          },
          "success": true,
          "message": "Created successfully",
          "errors": null
        }
        ```
    -   **`400 Bad Request`**: The request payload was invalid (e.g., missing a required field).
        ```json
        {
          "data": null,
          "success": false,
          "message": "Request failed",
          "errors": {
            "code": ["This field is required."]
          }
        }
        ```

---

#### 2. Retrieve, Update, and Delete a Specific Location

**Endpoint:** `/api/v1/locations/{id}`

##### `GET` /{id}

-   **Summary:** Retrieve a Location by ID
-   **Description:** Fetches the details of a specific location entry by its unique identifier. If the location exists, its data is returned. Otherwise, a `404 Not Found` error is returned.
-   **URL Parameters:**
    -   `id` (integer, required): The unique ID of the location to retrieve.
-   **Responses:**
    -   **`200 OK`**: The requested location's data was retrieved successfully.
        ```json
        {
          "data": {
            "id": 1,
            "name": "United States",
            "code": "USA"
          },
          "success": true,
          "message": "Retrieved successfully",
          "errors": null
        }
        ```
    -   **`404 Not Found`**: No location was found for the provided ID.
        ```json
        {
          "data": null,
          "success": false,
          "message": "Request failed",
          "errors": {
            "information": "Location with id: 999 not found"
          }
        }
        ```

##### `PUT` /{id}

-   **Summary:** Update a Location
-   **Description:** Updates an existing location entry identified by its ID. A complete payload with all required fields is expected.
-   **URL Parameters:**
    -   `id` (integer, required): The unique ID of the location to update.
-   **Request Body:**
    ```json
    {
      "name": "United States of America",
      "code": "USA"
    }
    ```
-   **Responses:**
    -   **`200 OK`**: The location was updated successfully.
        ```json
        {
          "data": {
            "id": 1,
            "name": "United States of America",
            "code": "USA"
          },
          "success": true,
          "message": "Updated successfully",
          "errors": null
        }
        ```
    -   **`400 Bad Request`**: The request payload was invalid.
        ```json
        {
          "data": null,
          "success": false,
          "message": "Request failed",
          "errors": {
            "name": ["This field may not be blank."]
          }
        }
        ```
    -   **`404 Not Found`**: The location with the specified ID was not found.
        ```json
        {
          "data": null,
          "success": false,
          "message": "Request failed",
          "errors": {
            "information": "Cannot update Location with id: 999. Not found in the database"
          }
        }
        ```

##### `DELETE` /{id}

-   **Summary:** Delete a Location
-   **Description:** Deletes a location entry from the database using its ID.
-   **URL Parameters:**
    -   `id` (integer, required): The unique ID of the location to delete.
-   **Responses:**
    -   **`200 OK`**: The location was deleted successfully.
        ```json
        {
          "data": {
            "information": "Successfully deleted Location with id: 1"
          },
          "success": true,
          "message": "Deleted successfully",
          "errors": null
        }
        ```
    -   **`404 Not Found`**: The location with the specified ID was not found.
        ```json
        {
          "data": null,
          "success": false,
          "message": "Request failed",
          "errors": {
            "information": "Cannot delete Location with id: 999. Not found in the database"
          }
        }
        ```

## Paper Types API Endpoints

TBD. This section will contain the API documentation for managing Paper Types.
