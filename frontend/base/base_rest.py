import asyncio
import requests

from base.base_ui import BaseUI

class BaseRest(BaseUI):
    """A base class for handling RESTful API requests with common HTTP methods."""
    GET=1
    POST=2
    PUT=3
    DELETE=4
    
    def __init__(self):
        """Initializes the BaseRest, setting up the logger."""
        super().__init__()
        self.log.debug("BaseRest initialized.")
        
    
    async def _make_request(self, request_type: int, url: str, payload: dict) -> requests.Response:
        """
        Makes an asynchronous HTTP request to the specified URL.

        This method supports GET, POST, PUT, and DELETE requests and wraps the
        synchronous `requests` call in an `asyncio.to_thread` to avoid blocking.

        Args:
            request_type (int): The type of HTTP request (e.g., BaseRest.GET, BaseRest.POST).
            url (str): The URL for the request.
            payload (dict): The JSON payload to send with the request.

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
                    timeout=5
                )
            
            self.log.debug(f"Received response with status code {response.status_code} from {url}")
            return response
        except requests.exceptions.RequestException as e:
            self.log.error(f'Network error: {e}')
            return None 