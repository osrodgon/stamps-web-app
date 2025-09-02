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

### REST API Endpoints 
For detailed information about all available REST endpoints, please refer to the [API Documentation](./api.md).

## Frontend
TBD.

### Things to consider
- https://nicegui.io/ for Frontend
- https://justpy.io/ for Frontend
- https://github.com/reactive-python/reactpy for Frontend
- https://www.gradio.app/ for Frontend
