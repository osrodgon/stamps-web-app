from core.urls import URLs
from services.base_service import BaseService


class StampsService(BaseService):
    """
    Service layer for interacting with the Stamp Database API.

    Provides methods for fetching foundational stamp data including years, 
    published issues, print methods, and stamp categories.
    """
    
    async def get_years(self, api_key: str = None, token: str = None):
        """
        Fetches the available years from the backend.
        
        This method retrieves a list of years for which stamp issues exist. Authentication
        is required via either an API key or a user token.

        Args:
            api_key (str, optional): The API master key for authentication. Defaults to None.
            token (str, optional): The user's JWT token for authentication. Defaults to None.

        Returns:
            requests.Response | None:   The response object containing the list of years on success, 
                                        or None if the request fails or authentication is missing.
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

    async def get_issues(self, year: int=None, series_name: str=None, api_key: str = None, token: str = None):
        """
        Retrieves stamp issues, optionally filtered by year or series name.

        Args:
            year (int, optional): The exact year to filter by. Defaults to None.
            series_name (str, optional): A substring search for the series name. Defaults to None.
            api_key (str, optional): Authentication master key.
            token (str, optional): User JWT token.

        Returns:
            requests.Response|None: The API response or None on auth/network failure.
        """
        if api_key is None and token is None:
            self.log.error("API Key or token is required.")
            return None
        
        if api_key is not None:
            headers = {'Authorization': f'Api-Key {api_key}'}
        else:
            headers = {'Authorization': f'Bearer {token}'}
            
        if not year and not series_name:
            url = URLs.Backend.issues
        elif year:
            url = f"{URLs.Backend.issues}?year={year}"
        elif series_name:
            url = f"{URLs.Backend.issues}?name={series_name}"

        return await self._make_request(
            request_type=self.GET,
            url=url,
            payload=None,
            headers=headers
        )
        
    async def get_print_types(self, api_key: str = None, token: str = None):
        """
        Fetches the available print types from the backend.
        
        This method retrieves the different types of printing methods used for stamps.
        Authentication is required via either an API key or a user token.

        Args:
            api_key (str, optional): The API master key for authentication. Defaults to None.
            token (str, optional): The user's JWT token for authentication. Defaults to None.

        Returns:
            requests.Response | None:   The response object containing the print types on success, 
                                        or None if the request fails or authentication is missing.
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

    async def get_stamp_types(self, api_key: str = None, token: str = None):
        """
        Fetches the available stamp types from the backend.
        
        This method retrieves the different types of stamps available.
        Authentication is required via either an API key or a user token.

        Args:
            api_key (str, optional): The API master key for authentication. Defaults to None.
            token (str, optional): The user's JWT token for authentication. Defaults to None.

        Returns:
            requests.Response | None:   The response object containing the stamp types on success, 
                                        or None if the request fails or authentication is missing.
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
            url=URLs.Backend.stamp_types,
            payload=None,
            headers=headers
        )

    async def get_stamps(self, issue_id: int, api_key: str = None, token: str = None):
        """
        Fetches the individual stamps belonging to a specific issue.

        This method retrieves the master list of stamps associated with an issue ID.
        It is typically used for populating the stamp gallery in the UI.

        Args:
            issue_id (int): The unique identifier of the issue.
            api_key (str, optional): Authentication master key.
            token (str, optional): User JWT token.

        Returns:
            requests.Response|None: The API response object or None on failure.
        """
        if api_key is None and token is None:
            self.log.error("API Key or token is required.")
            return None
        
        if api_key is not None:
            headers = {'Authorization': f'Api-Key {api_key}'}
        else:
            headers = {'Authorization': f'Bearer {token}'}
            
        url = f"{URLs.Backend.stamps}?issue_id={issue_id}"

        return await self._make_request(
            request_type=self.GET,
            url=url,
            payload=None,
            headers=headers
        )


