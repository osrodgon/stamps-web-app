from services.base_service import BaseService
from core.urls import URLs
from settings import API_MASTER_KEY

class StampsService(BaseService):
    """Service for handling stamps-related API calls."""
    
    async def get_years(self):
        """
        Fetches the available years from the backend.
        
        Returns:
            requests.Response | None: The response object on success, or None on error.
        """
        headers = {'Authorization': f'Api-Key {API_MASTER_KEY}'}
        return await self._make_request(
            request_type=self.GET,
            url=URLs.Backend.years,
            payload=None,
            headers=headers
        )

    async def get_issues(self, year: int=0):
        """
        Fetches stamp issues, optionally filtered by year.

        Args:
            year (int, optional):   The year to filter issues by. If 0 or not provided,
                                    it may fetch all issues depending on the API's behavior.
                                    Defaults to 0.

        Returns:
            requests.Response | None: The response object on success, or None on error.
        """
        headers = {'Authorization': f'Api-Key {API_MASTER_KEY}'}
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
