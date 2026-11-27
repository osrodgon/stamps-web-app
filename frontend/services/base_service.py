"""
Base service class for RESTful API communication.

This module provides the BaseService class that serves as the foundation
for all API service classes in the application. It provides:
- Asynchronous HTTP request handling (GET, POST, PUT, DELETE)
- Thread-based request execution to avoid blocking
- Logging of requests and responses
- Error handling with graceful fallback to None

Example:
    from services.base_service import BaseService
    
    class MyService(BaseService):
        async def fetch_data(self):
            response = await self._make_request(
                request_type=self.GET,
                url="https://api.example.com/data"
            )
            return response.json() if response else None
"""

import asyncio
import requests
from core.logger import Logger


class BaseService(Logger):
    """A base class for handling RESTful API requests with common HTTP methods.
    
    This class provides the foundational methods for making asynchronous HTTP
    requests to backend services. Subclasses should implement specific API
    operations (like login, fetch_stamps, etc.) using the _make_request method.
    
    Attributes:
        GET: Constant for HTTP GET requests (value: 1)
        POST: Constant for HTTP POST requests (value: 2)
        PUT: Constant for HTTP PUT requests (value: 3)
        DELETE: Constant for HTTP DELETE requests (value: 4)
    """
    GET=1
    POST=2
    PUT=3
    DELETE=4
    
    def __init__(self):
        """Initializes the BaseService, setting up the logger."""
        super().__init__()
        self.log.debug("BaseService initialized.")
        
    async def _make_request(self, request_type: int, url: str, payload: dict = None, headers: dict = None) -> requests.Response | None:
        """
        Makes an asynchronous HTTP request to the specified URL.

        This method supports GET, POST, PUT, and DELETE requests and wraps the
        synchronous `requests` call in an `asyncio.to_thread` to avoid blocking.

        Args:
            request_type (int): The type of HTTP request (e.g., BaseService.GET, BaseService.POST).
            url (str): The URL for the request.
            payload (dict, optional): The JSON payload to send with the request.
            headers (dict, optional): The headers to send with the request.

        Returns:
            requests.Response | None: The response object on success, or None on a network error.
        """
        
        match request_type:
            case self.GET:
                self.log.debug(f"Making GET request to {url}")
                rest_method = requests.get
            case self.POST:
                self.log.debug(f"Making POST request to {url}")
                rest_method = requests.post
            case self.PUT:
                self.log.debug(f"Making PUT request to {url}")
                rest_method = requests.put
            case self.DELETE:
                self.log.debug(f"Making DELETE request to {url}")
                rest_method = requests.delete
            case _:
                self.log.error(f"Unknown request type: {request_type}. Defaulting to GET.")
                rest_method = requests.get
                
        try:
            response = await asyncio.to_thread(
                    rest_method, 
                    url, 
                    json=payload,
                    headers=headers,
                    timeout=180
                )
            
            self.log.debug(f"Received response with status code {response.status_code} from {url}")
            return response
        except requests.exceptions.RequestException as e:
            self.log.error(f'Network error: {e}')
            return None
