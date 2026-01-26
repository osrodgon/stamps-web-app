import requests
from services.base_service import BaseService
from core.urls import URLs
from nicegui import app
from settings import USER_ID, USER_JWT_TOKEN, USER_LANGUAGE, API_MASTER_KEY

class ConfigService(BaseService):
    """
    Service for managing application configuration via the backend REST API.
    
    This service facilitates the retrieval, creation, update, and deletion 
    of user-specific configuration properties, such as language settings.
    It synchronizes these settings with NiceGUI's app.storage.user.
    """
    
    def __init__(self):
        super().__init__()
        
    async def load_user_config(self) -> list:
        """
        Retrieves all configuration entries from the backend for the current user.
        
        Returns:
            list: A list of configuration entry dictionaries.
        """    
        headers = {'Authorization': f'Api-Key {API_MASTER_KEY}'}
        response = await self._make_request(
            request_type=self.GET,
            url=f"{URLs.Backend.config}?user_id={app.storage.user.get(USER_ID)}",
            headers=headers
        )
        
        if response and response.status_code == requests.codes.ok:
            data = response.json().get('data', [])
            
            # Update local storage with allowed retrieved settings
            for entry in data:
                prop = entry.get('property')
                if prop == USER_LANGUAGE:
                    app.storage.user[prop] = entry.get('value')
            
            return data
            
        self.log.error(f"Failed to fetch configuration. Status: {response.status_code if response else 'No response'}")
        return []

    async def save_user_config(self) -> bool:
        """
        Saves supported configuration properties from app.storage.user to the backend.
        
        Currently supports:
        - USER_LANGUAGE
        
        Returns:
            bool: True if all operations were successful, False otherwise.
        """
        user_id = app.storage.user.get(USER_ID)
        
        if not user_id:
            self.log.error("User ID is missing. User may not be logged in.")
            return False
            
        headers = {'Authorization': f'Api-Key {API_MASTER_KEY}'}
        
        # Fetch current configs from backend to determine whether to POST or PUT
        response = await self._make_request(
            request_type=self.GET,
            url=f"{URLs.Backend.config}?user_id={user_id}",
            headers=headers
        )
        
        if response and response.status_code == requests.codes.ok:
            data = response.json().get('data', [])
            
            # Identify properties to save from app.storage.user
            supported_properties = [USER_LANGUAGE]
            
            success = True
            for prop in supported_properties:
                value = app.storage.user.get(prop)
                if value is None:
                    continue
                    
                payload = {
                    'user': user_id,
                    'property': prop,
                    'value': value
                }
                
                existing_config = next((c for c in data if c['property'] == prop), None)
                
                if existing_config:
                    # Perform update (PUT)
                    url = f"{URLs.Backend.config}{existing_config['id']}"
                    response = await self._make_request(
                        request_type=self.PUT,
                        url=url,
                        payload=payload,
                        headers=headers
                    )
                else:
                    # Perform creation (POST)
                    response = await self._make_request(
                        request_type=self.POST,
                        url=URLs.Backend.config,
                        payload=payload,
                        headers=headers
                    )
                    
                if not (response and response.status_code in [requests.codes.ok, requests.codes.created]):
                    self.log.error(f"Failed to save configuration '{prop}'. Status: {response.status_code if response else 'No response'}")
                    success = False
                else:
                    self.log.info(f"Configuration '{prop}' saved successfully.")
            
            return success
            
        self.log.error(f"Failed to fetch configuration for saving. Status: {response.status_code if response else 'No response'}")
        return False

    async def delete_user_config(self, property_name: str) -> bool:
        """
        Deletes a specific configuration property for the current user.
        
        Args:
            property_name (str): The key of the configuration to delete.
            
        Returns:
            bool: True if deleted successfully, False otherwise.
        """            
        headers = {'Authorization': f'Api-Key {API_MASTER_KEY}'}
        url = f"{URLs.Backend.config}{app.storage.user[USER_ID]}"
        response = await self._make_request(
            request_type=self.DELETE,
            url=url,
            headers=headers
        )
        
        if response and response.status_code == requests.codes.ok:
            if property_name in app.storage.user:
                del app.storage.user[property_name]
            self.log.info(f"Configuration '{property_name}' deleted successfully.")
            return True
            
        self.log.error(f"Failed to delete configuration '{property_name}'. Status: {response.status_code if response else 'No response'}")
        return False
