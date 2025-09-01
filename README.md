# Stamps Collection Web App
This project is an application to store and stamps collection. It has two differentiated parts:

- The backend (API REST interface). 
- The frontend (User's interfaces).

## Backend
The backend is made with the Django framework. It provides an API to access the stamps collection stored in the database. For each one of the entities in the database, a django app will be created to handle the REST interface for that entity.

### Stamp Collection Database Schema

This document provides a detailed description of the database schema for the Stamp Collection application. The model is designed to organize and manage data related to stamp issues, individual stamps, and associated metadata.

The overall database structure is illustrated below:

![alt text](stamps_api_server/resources/stamps-db-model.png)

### Table Definitions

#### 1. `Year` Table
This table provides a chronological framework for organizing stamp issues.
- **id (int, PK):** Unique identifier for each year entry.
- **year (int):** The calendar year associated with stamp issues.

#### 2. `Issue` Table
The `issue` table serves as the central hub of the schema, connecting most related entities. It represents a set of stamps released for a specific theme or purpose.
- **id (int, PK):** Unique identifier for each issue.
- **year_id (int, FK):** References the `Year` table, linking an issue to a specific year.
- **date (date):** The exact release date of the issue.
- **country_id (int, FK):** References the `Country` table, linking an issue to a specific country.
- **name (varchar):** The official name or title of the issue.
- **number_issued (int):** Total number of issues released for this theme.
- **value (float):** The total face value of the entire issue.
- **number_owned (int):** The quantity of this issue owned by the collector.
- **number_stamps (int):** The total number of distinct stamps included in this issue.
- **stamp_type (int, FK):** References the `Stamp_Type` table to categorize the issue.
- **paper_type (int, FK):** References the `Paper_Type` table to specify the paper used.
- **total_value (float):** The cumulative value of stamps owned from this issue.
- **description (varchar):** A descriptive text about the issue.
- **located_in (int, FK):** References the `Location` table to specify where the issue is stored.
- **note (varchar):** Additional notes or remarks.
- **perforated (varchar):** Details about the stamp perforation.

#### 3. `Stamp` Table
This table details individual stamps within a given issue, including catalog and physical attributes.
- **id (int, PK):** Unique identifier for each stamp.
- **issue_id (int, FK):** References the `Issue` table, linking the stamp to its parent issue.
- **edifil_code (varchar):** Catalog code from the Edifil cataloging system.
- **face_value (varchar):** The nominal printed value on the stamp.
- **name (varchar):** The name or description of the individual stamp.
- **others_code (varchar):** Additional catalog codes from other systems.
- **image (varchar):** Path or reference to an image representing the stamp.
- **color (varchar):** The primary color of the stamp.

#### 4. `Stamp_Type` Table
This table defines classification categories for stamp issues.
- **id (int, PK):** Unique identifier for each stamp type.
- **name (varchar):** The name of the stamp type (e.g., "Commemorative", "Definitive", "Airmail").

#### 5. `Location` Table
This table tracks the physical or logical storage location of stamp issues.
- **id (int, PK):** Unique identifier for each storage location.
- **name (varchar):** Describes the storage location (e.g., "Main Album", "Folder B", "Box 1").

#### 6. `Country` Table
This table lists the countries of origin for the stamp issues.
- **id (int, PK):** Unique identifier for each country.
- **name (varchar):** The name of the country.

#### 7. `Paper_Type` Table
This table defines the types of paper used for stamp issues.
- **id (int, PK):** Unique identifier for each paper type.
- **name (varchar):** The name of the paper type (e.g., "Coated", "Uncoated", "Granite").

#### 8. `Config` Table
This table provides a key-value store for system-level configuration settings or customizable application metadata.
- **property (varchar, PK):** The name of the configuration property.
- **value (varchar):** The value assigned to the property.

### Relationships
The primary relationships between the tables are as follows:
- **One-to-Many:** A `Year` can have multiple `Issues`.
- **One-to-Many:** A `Country` can have multiple `Issues`.
- **One-to-Many:** An `Issue` can contain multiple `Stamps`.
- **Many-to-One:** Each `Issue` is associated with one `Stamp_Type`.
- **Many-to-One:** Each `Issue` is associated with one `Paper_Type`.
- **Many-to-One:** Each `Issue` is stored in one `Location`.

### Years API Endpoints

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

### Config API Endpoints

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
-   **Description:** Fetches a specific configuration entry using its unique ID.
-   **URL Parameters:**
    -   `id` (integer, required): The unique ID of the configuration entry to retrieve.
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
    -   `id` (integer, required): The unique ID of the configuration entry to update.
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
    -   `id` (integer, required): The unique ID of the configuration entry to delete.
-   **Responses:**
    -   **`200 OK`**: The configuration entry was deleted successfully.
        ```json
        {
          "data": {
            "information": "Successfully deleted config entry with id: 1"
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


## Frontend
TBD. 

### Things to consider
- https://nicegui.io/ for Frontend
- https://justpy.io/ for Frontend
- https://github.com/reactive-python/reactpy for Frontend
- https://www.gradio.app/ for Frontend





