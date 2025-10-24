class Messages:
    def success():
        return "Request successful"
    
    def failed():
        return "Request failed"
    
    def server_error():
        return "Internal server error"
    
    def created_successfully():
        return "Created successfully"
    
    def updated_successfully():
        return "Updated successfully"
    
    def partially_updated_successfully():
        return "Partially updated successfully"
    
    def deleted_successfully():
        return "Deleted successfully"
    
    def retrieved_successfully():
        return "Retrieved successfully"
    
    def field_required():
        return "This field is required."
    
    def field_not_allowed():
        return "This field is not allowed."
    
    def field_invalid():
        return "This field is invalid."
    
    class Code:
        def required():
            return "required"
        
        def other():
            return "other"
        
        def unique():
            return "unique"
        
        def invalid():
            return "invalid"
        
        def connection_lost():
            return "connection_lost"
        
        def permission_denied():
            return "permission_denied"
        
        def user_not_found():
            return "user_not_found"
        
    class Database:
        def querying(table_name, id):
            return f"Querying database for {table_name.lower()} with id: {id}."
        
        def not_found(table_name, id):
            return f"{table_name.title()} with id: {id} not found in the database."
        
        def error(table_name, id, error_message):
            return f"An unexpected error occurred while fetching {table_name.lower()} with id {id}: {error_message}."
        
        def user_not_found(username):
            return f"User {username} not found in the database."
        
        def connection_lost():
            return "Database connection lost."
        
        def unknow_user():
            return "Unknown user."
        
    class Get:
        def retrieve_one(table_name, id):
            return f"Attempting to retrieve {table_name.lower()} for id: {id}."

        def retrieve_all(table_name):
            return f"Attempting to retrieve all elements in {table_name}."
        
        def retrieved_all(table_name, count):
            return f"Found {count} {table_name.lower()} entries."
        
        def retrieved_one(table_name, id):
            return f"Successfully retrieved {table_name.lower()} with id: {id}."
        
        def not_found(table_name, id):
            return f"{table_name.title()} with id: {id} not found."
        
    class Post:
        def create_one(table_name, payload):
            return f"Attempting to create a new {table_name.lower()} with payload: {payload}."
        
        def created_one(table_name, id):
            return f"Successfully created {table_name.lower()} with id: {id}."
        
        def validation_failed(table_name, errors):
            return f"Payload validation failed for new {table_name.lower()} entry: {errors}."
        
        def already_exists(table_name, name):
            return f"{table_name.title()} with this {name} already exists."


    class Put:
        def update_one(table_name, id, payload):
            return f"Attempting to update {table_name.lower()} for id: {id} with payload: {payload}."

        def not_found(table_name, id):
            return f"Cannot update {table_name.lower()} with id: {id}. Not found in the database."
        
        def updated_one(table_name, id):
            return f"Successfully updated {table_name.lower()} with id: {id}."

        def validation_failed(table_name, id, errors):
            return f"Payload validation failed for {table_name.lower()} update (id: {id}): {errors}."
        
        def already_exists(table_name, name):
            return f"{table_name.title()} with this name already exists."


    class Delete:
        def delete_one(table_name, id):
            return f"Attempting to delete {table_name.lower()} for id: {id}."

        def not_found(table_name, id):
            return f"Cannot delete {table_name.lower()} with id: {id}. Not found in the database."

        def deleted_one(table_name, id):
            return f"Successfully deleted {table_name.lower()} with id: {id}."
        
    class APIKey:
        def invalid_key():
            return "Invalid API Key/Hash"
        
        def invalid_user():
            return "API Key is valid only for Collection Management API."
        
        def not_a_user():
            return "API Key has not a valid associated collection user."