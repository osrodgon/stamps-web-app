"""
Service for stamp issue API communication.

Provides methods to fetch, sort, search, and delete stamp issues
via the backend REST API, as well as fetching the full list of
available years from the /years/ endpoint.
"""

from urllib.parse import urlencode

import requests

from services.base_service import BaseService
from core.urls import URLs
from settings import API_MASTER_KEY


class IssueService(BaseService):
    """Service for managing stamp issue data through the backend API.

    Public methods:
        get_issues:       Paginated issue list with sort, name, and year filters.
        delete_issue:     Remove an issue by ID.
        delete_stamp:     Remove a stamp by ID.
        get_issue_stamps: Fetch stamps belonging to a specific issue.
        get_years:        Fetch all available years for range selector initialization.
    """

    async def get_issues(
        self,
        page: int = 1,
        page_size: int = 15,
        sort_by: str = "date",
        order: str = "asc",
        name: str = "",
        year: str = "",
    ) -> requests.Response | None:
        """
        Fetch a paginated, sorted list of stamp issues.

        Query params match the backend IssuesView GET endpoint:
          - sortBy, order, page, pageSize, name, year

        Args:
            page: Page number (1-indexed).
            page_size: Items per page (0 means all).
            sort_by: Field to sort by ("date" or "name").
            order: Sort order ("asc" or "desc").
            name: Filter by issue name (case-insensitive).
            year: Filter by year or year range (e.g. "2002" or "2000-2010").

        Returns:
            Raw requests.Response, or None on network error.
        """
        params: dict[str, str | int] = {
            "page": page,
            "pageSize": page_size,
            "sortBy": sort_by,
            "order": order,
        }
        if name:
            params["name"] = name
        if year:
            params["year"] = year

        url = f"{URLs.Backend.issues}?{urlencode(params)}"
        return await self._make_request(
            request_type=self.GET,
            url=url,
            headers={"Authorization": f"Api-Key {API_MASTER_KEY}"},
        )

    async def delete_issue(self, issue_id: int) -> requests.Response | None:
        """
        Delete a stamp issue by ID.

        Args:
            issue_id: The ID of the issue to delete.

        Returns:
            Raw requests.Response, or None on network error.
        """
        url = f"{URLs.Backend.issues}{issue_id}/"
        return await self._make_request(
            request_type=self.DELETE,
            url=url,
            headers={"Authorization": f"Api-Key {API_MASTER_KEY}"},
        )

    async def delete_stamp(self, stamp_id: int) -> requests.Response | None:
        """Delete a stamp by ID.

        Sends a DELETE request to the backend stamps endpoint. The URL
        intentionally omits a trailing slash to match the backend's
        ``path('<int:id>', ...)`` route pattern.

        Args:
            stamp_id: The ID of the stamp to delete.

        Returns:
            Raw requests.Response (status 200 on success), or None on network error.
        """
        url = f"{URLs.Backend.stamps}{stamp_id}"
        return await self._make_request(
            request_type=self.DELETE,
            url=url,
            headers={"Authorization": f"Api-Key {API_MASTER_KEY}"},
        )

    async def get_issue_stamps(self, issue_id: int) -> requests.Response | None:
        """
        Fetch stamps belonging to a specific issue.

        Args:
            issue_id: The ID of the issue.

        Returns:
            Raw requests.Response, or None on network error.
        """
        url = f"{URLs.Backend.stamps}?issue_id={issue_id}"
        return await self._make_request(
            request_type=self.GET,
            url=url,
            headers={"Authorization": f"Api-Key {API_MASTER_KEY}"},
        )

    async def get_years(self) -> requests.Response | None:
        """Fetch all available years from the backend.

        GET /years/ returns a list of {"id": int, "year": int} objects
        ordered ascending. The frontend computes min/max from the list.

        Returns:
            Raw requests.Response, or None on network error.
        """
        return await self._make_request(
            request_type=self.GET,
            url=URLs.Backend.years,
            headers={"Authorization": f"Api-Key {API_MASTER_KEY}"},
        )
