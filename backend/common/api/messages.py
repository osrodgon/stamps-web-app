class Messages:
    class Database:
        def querying(table_name, id):
            return f"Querying database for {table_name.lower()} with id: {id}."
        
        def not_found(table_name, id):
            return f"{table_name.title()} with id: {id} not found in the database."
        
        def error(table_name, id, error_message):
            return f"An unexpected error occurred while fetching {table_name.lower()} with id {id}: {error_message}"
        

			
# GET			f"Attempting to retrieve color for id: {pk}"
# 			f"Color with id: {pk} not found"
# 			f"Successfully retrieved color with id: {pk}"
# 			"Attempting to retrieve all elements in Color."
# 			f"Found {len(colors)} color entries."

# 			LOG f"Attempting to retrieve {table_name} for id: {pk}"
# 			MSG f"{table_name} with id: {pk} not found"
# 			LOG f"Successfully retrieved {table_name} with id: {pk}"
# 			LOG f"Attempting to retrieve all elements in {trable_name}."
# 			LOG f"Found {i} {table_name} entries."
			
# POST		f"Attempting to create a new color with payload: {request.data}"
# 			f"Successfully created color with id: {instance.id}"
# 			f"Payload validation failed for new color entry: {color.errors}"

# 			LOG f"Attempting to create a new {table_name} with payload: {payload}"
# 			LOG f"Successfully created {table_name} with id: {id}"
# 			LOG f"Payload validation failed for new {table_name} entry: {errors}"
			
# PUT			f"Attempting to update color for id: {pk} with payload: {request.data}"
# 			f"Cannot update Color with id: {pk}. Not found in the database"
# 			f"Successfully updated color with id: {instance.id}"
# 			f"Payload validation failed for color update (id: {pk}): {updated_color.errors}"
			

# 			LOG f"Attempting to update {table_name} for id: {pk} with payload: {payload}"
# 			MSG f"Cannot update {table_name} with id: {pk}. Not found in the database"
# 			LOG f"Successfully updated {table_name} with id: {id}"
# 			LOG f"Payload validation failed for {table_name} update (id: {id}): {errors}"

			
# DELETE		f"Attempting to delete color for id: {pk}"
# 			f"Cannot delete Color with id: {pk}. Not found in the database"
# 			f"Successfully deleted Color with id: {pk}"

# 			LOG f"Attempting to delete {table_name} for id: {pk}"
# 			MSG f"Cannot delete {table_name} with id: {pk}. Not found in the database"
# 			MSG f"Successfully deleted {table_name} with id: {pk}"