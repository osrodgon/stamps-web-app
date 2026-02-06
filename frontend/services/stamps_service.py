from urllib.parse import urlencode
from core.urls import URLs
from services.base_service import BaseService
from settings import API_MASTER_KEY


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

    async def get_issues(self, year: int=None, series_name: str=None, page: int=None, page_size: int=None, sort_by: str='date', descending: bool=False):
        """
        Retrieves stamp issues, optionally filtered by year or series name.

        Args:
            year (int, optional): The exact year to filter by. Defaults to None.
            series_name (str, optional): A substring search for the series name. Defaults to None.

        Returns:
            requests.Response|None: The API response or None on auth/network failure.
        """
        params = {}
        if year:
            if str(year).endswith('*'):
                params['year'] = self._convert_year_pattern_to_range(year)
            else:
                params['year'] = year
        if series_name:
            params['name'] = series_name
        if  page is not None:
            params['page'] = page
        if page_size is not None:
            params['pageSize'] = page_size
        if sort_by:
            params['sortBy'] = sort_by
        if descending is not None:
            params['order'] = 'desc' if descending else 'asc'
        
        query_string = urlencode(params) if params else ''
        url = f"{URLs.Backend.issues}?{query_string}" if query_string else URLs.Backend.issues
            
        return await self._make_request(
            request_type=self.GET,
            url=url,
            payload=None,
            headers=self._get_headers()
        )
        
    def _convert_year_pattern_to_range(self, year_pattern: str) -> str:
        """
        Converts a year pattern to a range for API filtering.
        
        Supports patterns like:
        - '20*' -> '2000-2099' (2-digit year with wildcard)
        - '202*' -> '2020-2029' (3-digit year with wildcard)  
        - '2023' -> 2023 (exact year)
        
        Args:
            year_pattern (str): The year pattern to convert.
            
        Returns:
            str or int: The converted year range or exact year, or None if invalid.
        """
        s = year_pattern.strip()
        
        # Handle 3-digit year with wildcard (e.g., '202*' -> '2020-2029')
        if len(s) == 4 and s.endswith('*') and s[:-1].isdigit():
            prefix = s[:-1]
            return f'{prefix}0-{prefix}9'

        # Handle 2-digit year with wildcard (e.g., '20*' -> '2000-2099')
        elif len(s) == 3 and s.endswith('*') and s[:-1].isdigit():
            prefix = s[:-1]
            return f'{prefix}00-{prefix}99'

        # Handle exact year (e.g., '2023' -> 2023)
        elif len(s) == 4 and s.isdigit():
            return int(s)

        return None
        
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
