"""
Authentication service for the Stamps web application.

This module provides the AuthService class for handling user authentication
API calls to the backend. It supports:
- User login with username/password
- User registration (signup) with required fields

Example:
    from services.auth_service import AuthService
    
    auth_service = AuthService()
    
    # Login
    response = await auth_service.login({"username": "user", "password": "pass"})
    
    # Signup
    response = await auth_service.signup({
        "username": "newuser",
        "email": "user@example.com",
        "password": "securepassword"
    })
"""

from services.base_service import BaseService
from core.urls import URLs
from settings import API_MASTER_KEY


class AuthService(BaseService):
    """Service for handling authentication-related API calls.
    
    This class extends BaseService to provide authentication-specific
    operations including login and signup. It handles communication
    with the backend authentication endpoints.
    
    Attributes:
        login: Async method to authenticate a user
        signup: Async method to register a new user
    """
    
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
