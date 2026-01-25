from core.urls import URLs
from services.base_service import BaseService
from settings import API_MASTER_KEY, USER_JWT_TOKEN
from nicegui import app


class StampsService(BaseService):
    """
    Service layer for interacting with the Stamp Database API.

    Provides methods for fetching foundational stamp data including years, 
    published issues, print methods, and stamp categories.
    """

    def _get_headers(self):
        """Helper to construct authentication headers."""
        return {'Authorization': f'Api-Key {API_MASTER_KEY}'}
    
    async def get_years(self):
        """
        Fetches the available years from the backend.
        
        Returns:
            requests.Response | None:   The response object containing the list of years.
        """
        return await self._make_request(
            request_type=self.GET,
            url=URLs.Backend.years,
            payload=None,
            headers=self._get_headers()
        )

    async def get_issues(self, year: int=None, series_name: str=None):
        """
        Retrieves stamp issues, optionally filtered by year or series name.

        Args:
            year (int, optional): The exact year to filter by. Defaults to None.
            series_name (str, optional): A substring search for the series name. Defaults to None.

        Returns:
            requests.Response|None: The API response or None on auth/network failure.
        """
        query_parts = []
        if year:
            query_parts.append(f"year={year}")
        if series_name:
            query_parts.append(f"name={series_name}")

        if query_parts:
            url = f"{URLs.Backend.issues}?{'&'.join(query_parts)}"
        else:
            url = URLs.Backend.issues
            
        return await self._make_request(
            request_type=self.GET,
            url=url,
            payload=None,
            headers=self._get_headers()
        )
        
    async def get_print_types(self):
        """
        Fetches the available print types from the backend.
        
        This method retrieves the different types of printing methods used for stamps.

        Returns:
            requests.Response | None:   The response object containing the print types on success, 
                                        or None if the request fails or authentication is missing.
        """
        return await self._make_request(
            request_type=self.GET,
            url=URLs.Backend.print_types,
            payload=None,
            headers=self._get_headers()
        )

    async def get_stamp_types(self):
        """
        Fetches the available stamp types from the backend.
        
        This method retrieves the different types of stamps available.

        Returns:
            requests.Response | None:   The response object containing the stamp types on success, 
                                        or None if the request fails or authentication is missing.
        """
        return await self._make_request(
            request_type=self.GET,
            url=URLs.Backend.stamp_types,
            payload=None,
            headers=self._get_headers()
        )

    async def get_stamps(self, issue_id: int):
        """
        Fetches the individual stamps belonging to a specific issue.

        This method retrieves the master list of stamps associated with an issue ID.
        It is typically used for populating the stamp gallery in the UI.

        Args:
            issue_id (int): The unique identifier of the issue.

        Returns:
            requests.Response|None: The API response object or None on failure.
        """
        url = f"{URLs.Backend.stamps}?issue_id={issue_id}"

        return await self._make_request(
            request_type=self.GET,
            url=url,
            payload=None,
            headers=self._get_headers()
        )
