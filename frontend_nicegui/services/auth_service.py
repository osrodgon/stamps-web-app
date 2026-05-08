from services.base_service import BaseService
from core.urls import URLs
from settings import API_MASTER_KEY

class AuthService(BaseService):
    """Service for handling authentication-related API calls."""
    
    async def login(self, payload: dict):
        """
        Sends a login request to the backend.
        
        Args:
            payload (dict): The user credentials (username, password).
            
        Returns:
            requests.Response | None: The response object on success, or None on error.
        """
        return await self._make_request(
            request_type=self.POST, 
            url=URLs.Backend.login, 
            payload=payload
        )
        
    async def signup(self, payload: dict):
        """
        Sends a signup request to the backend.
        
        Args:
            payload (dict): The user registration data.
            
        Returns:
            requests.Response | None: The response object on success, or None on error.
        """
        headers = {'Authorization': f'Api-Key {API_MASTER_KEY}'}
        return await self._make_request(
            request_type=self.POST, 
            url=URLs.Backend.signup, 
            payload=payload, 
            headers=headers
        )
