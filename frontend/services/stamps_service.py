from core.urls import URLs
from services.base_service import BaseService


class StampsService(BaseService):
    """Service for handling stamps-related API calls."""
    
    async def get_years(self, api_key: str = None, token: str = None):
        """
        Fetches the available years from the backend.
        
        Returns:
            requests.Response | None: The response object on success, or None on error.
        """
        if api_key is None and token is None:
            self.log.error("API Key or token is required.")
            return None
        
        if api_key is not None:
            headers = {'Authorization': f'Api-Key {api_key}'}
        else:
            headers = {'Authorization': f'Bearer {token}'}
            
        return await self._make_request(
            request_type=self.GET,
            url=URLs.Backend.years,
            payload=None,
            headers=headers
        )

    async def get_issues(self, year: int=0, api_key: str = None, token: str = None):
        """
        Fetches stamp issues, optionally filtered by year.

        Args:
            year (int, optional):   The year to filter issues by. If 0 or not provided,
                                    it may fetch all issues depending on the API's behavior.
                                    Defaults to 0.

        Returns:
            requests.Response | None: The response object on success, or None on error.
        """
        if api_key is None and token is None:
            self.log.error("API Key or token is required.")
            return None
        
        if api_key is not None:
            headers = {'Authorization': f'Api-Key {api_key}'}
        else:
            headers = {'Authorization': f'Bearer {token}'}
            
        if year == 0:
            url = URLs.Backend.issues
        else:
            url = f"{URLs.Backend.issues}?year={year}"

        return await self._make_request(
            request_type=self.GET,
            url=url,
            payload=None,
            headers=headers
        )
        
    async def get_print_types(self, api_key: str = None, token: str = None):
        """
        Fetches the available print types from the backend.
        
        Returns:
            requests.Response | None: The response object on success, or None on error.
        """
        if api_key is None and token is None:
            self.log.error("API Key or token is required.")
            return None
        
        if api_key is not None:
            headers = {'Authorization': f'Api-Key {api_key}'}
        else:
            headers = {'Authorization': f'Bearer {token}'}
        
        return await self._make_request(
            request_type=self.GET,
            url=URLs.Backend.print_types,
            payload=None,
            headers=headers
        )

