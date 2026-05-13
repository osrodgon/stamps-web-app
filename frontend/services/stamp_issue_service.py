"""
Service for stamp issue API communication.

Provides methods to fetch, sort, search, and delete stamp issues
via the backend REST API.
"""

from urllib.parse import urlencode

import requests

from services.base_service import BaseService
from core.urls import URLs
from settings import API_MASTER_KEY


class StampIssueService(BaseService):
    """Service for managing stamp issue data through the backend API."""

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
        )
