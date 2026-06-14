"""
Service for stamp issue API communication.

Provides methods to fetch, sort, search, and delete stamp issues
via the backend REST API, as well as fetching the full list of
available years from the /years/ endpoint.
"""

from urllib.parse import urlencode
from typing import Any

import requests

from services.base_service import BaseService
from core.urls import URLs
from settings import API_MASTER_KEY


class IssueService(BaseService):
    """Service for managing stamp issue data through the backend API.

    Public methods:
        get_issues:         Paginated issue list with sort, name, and year filters.
        create_issue:       Create a new stamp issue via POST.
        update_issue:       Update an existing stamp issue.
        delete_issue:       Remove an issue by ID.
        delete_stamp:       Remove a stamp by ID.
        get_issue_stamps:   Fetch stamps belonging to a specific issue.
        get_countries:      Fetch all countries (reference data).
        get_artists:        Fetch all artists (reference data).
        get_stamp_types:    Fetch all stamp types (reference data).
        get_paper_types:    Fetch all paper types (reference data).
        get_print_types:    Fetch all print types (reference data).
        get_printers:       Fetch all printers (reference data).
        get_years:          Fetch all available years.
        create_country:     Create a new country.
        create_artist:      Create a new artist.
        create_stamp_type:  Create a new stamp type.
        create_paper_type:  Create a new paper type.
        create_print_type:  Create a new print type.
        create_printer:     Create a new printer.
        create_year:        Create a new year.
    """

    # --- Auth headers ---

    @property
    def _auth_headers(self) -> dict[str, str]:
        return {"Authorization": f"Api-Key {API_MASTER_KEY}"}

    # --- Generic reference-data helpers ---

    async def _fetch_ref(self, url: str) -> list[dict]:
        """GET a reference-data endpoint and return the data list.

        Args:
            url: The full API URL for the reference-data endpoint.

        Returns:
            List of dicts, or empty list on error.
        """
        response = await self._make_request(
            request_type=self.GET,
            url=url,
            headers=self._auth_headers,
        )
        if response and response.status_code == requests.codes.ok:
            return response.json().get("data", [])
        return []

    async def _create_ref(self, url: str, name: str) -> int | None:
        """POST a new reference-data entity and return its ID.

        Args:
            url: The full API URL for the reference-data endpoint.
            name: The name of the new entity.

        Returns:
            The new entity's ID on success, None on failure.
        """
        response = await self._make_request(
            request_type=self.POST,
            url=url,
            payload={"name": name},
            headers=self._auth_headers,
        )
        if response and response.status_code == requests.codes.created:
            return response.json().get("data", {}).get("id")
        return None

    # --- Issues ---

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
            headers=self._auth_headers,
        )

    async def create_issue(self, data: dict[str, Any]) -> requests.Response | None:
        """Create a new stamp issue.

        POST to /issues/ with the IssueRequestSerializer payload.

        Args:
            data: Issue creation payload (year, date, country, name, etc.).

        Returns:
            Raw requests.Response, or None on network error.
        """
        return await self._make_request(
            request_type=self.POST,
            url=URLs.Backend.issues,
            payload=data,
            headers=self._auth_headers,
        )

    async def update_issue(self, issue_id: int, data: dict[str, Any]) -> requests.Response | None:
        """Update an existing stamp issue via PUT.

        Sends a partial update (``partial=True`` on backend) with only
        the fields provided in ``data``.

        Args:
            issue_id: The ID of the issue to update.
            data: Dict of fields to update (e.g. ``{"stamp_type": 3}``).

        Returns:
            Raw requests.Response, or None on network error.
        """
        url = f"{URLs.Backend.issues}{issue_id}/"
        return await self._make_request(
            request_type=self.PUT,
            url=url,
            headers=self._auth_headers,
            payload=data,
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
            headers=self._auth_headers,
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
            headers=self._auth_headers,
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
            headers=self._auth_headers,
        )

    # --- Reference data: getters ---

    async def create_stamp(self, data: dict[str, Any]) -> requests.Response | None:
        """Create a new stamp.

        POST to /stamps/ with the StampRequestSerializer payload.

        Args:
            data: Stamp creation payload (issue, name, face_value, etc.).

        Returns:
            Raw requests.Response, or None on network error.
        """
        return await self._make_request(
            request_type=self.POST,
            url=URLs.Backend.stamps,
            payload=data,
            headers=self._auth_headers,
        )

    async def get_colors(self) -> requests.Response | None:
        """Fetch all colors from the backend.

        Returns:
            Raw requests.Response (data is list of color objects), or None.
        """
        return await self._make_request(
            request_type=self.GET,
            url=URLs.Backend.colors,
            headers=self._auth_headers,
        )

    async def get_countries(self) -> list[dict]:
        return await self._fetch_ref(URLs.Backend.countries)

    async def get_artists(self) -> list[dict]:
        return await self._fetch_ref(URLs.Backend.artists)

    async def get_stamp_types(self) -> list[dict]:
        return await self._fetch_ref(URLs.Backend.stamp_types)

    async def get_paper_types(self) -> list[dict]:
        return await self._fetch_ref(URLs.Backend.paper_types)

    async def get_print_types(self) -> list[dict]:
        return await self._fetch_ref(URLs.Backend.print_types)

    async def get_printers(self) -> list[dict]:
        return await self._fetch_ref(URLs.Backend.printers)

    async def get_years(self) -> requests.Response | None:
        """Fetch all available years from the backend.

        GET /years/ returns a list of {"id": int, "year": int} objects
        ordered ascending. The frontend computes min/max from the list.

        NOTE: returns raw Response (not list[dict]) because the caller
        needs the full response object to distinguish "no data" from
        "network error".
        """
        return await self._make_request(
            request_type=self.GET,
            url=URLs.Backend.years,
            headers=self._auth_headers,
        )

    # --- Reference data: creators ---

    async def create_country(self, name: str) -> int | None:
        return await self._create_ref(URLs.Backend.countries, name)

    async def create_artist(self, name: str) -> int | None:
        return await self._create_ref(URLs.Backend.artists, name)

    async def create_stamp_type(self, name: str) -> int | None:
        return await self._create_ref(URLs.Backend.stamp_types, name)

    async def create_paper_type(self, name: str) -> int | None:
        return await self._create_ref(URLs.Backend.paper_types, name)

    async def create_print_type(self, name: str) -> int | None:
        return await self._create_ref(URLs.Backend.print_types, name)

    async def create_printer(self, name: str) -> int | None:
        return await self._create_ref(URLs.Backend.printers, name)

    async def create_year(self, year: int) -> int | None:
        """Create a new year.

        Args:
            year: The year integer.

        Returns:
            The new year's ID on success, None on failure.
        """
        response = await self._make_request(
            request_type=self.POST,
            url=URLs.Backend.years,
            payload={"year": year},
            headers=self._auth_headers,
        )
        if response and response.status_code == requests.codes.created:
            return response.json().get("data", {}).get("id")
        return None
