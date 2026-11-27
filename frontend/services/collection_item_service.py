"""Service for the series of a collection (plan step B3).

It is separate from `CollectionService` because it speaks a different resource: the
items and the series of one collection. Like every service, it is Flet-free and takes
the user's JWT in the constructor; the page reads the token from `SharedPreferences`.

The series endpoint mirrors `/issues/`, so the parameters have the same names and the
response carries the same `pagination` block the table already understands.
"""

from __future__ import annotations

from urllib.parse import urlencode

import requests

from core.urls import URLs
from services.base_service import BaseService


class CollectionItemService(BaseService):
    """Service for the series and items of a collection.

    Public methods:
        get_series:          One page of the series of the collection.
        get_issue:           One series with its stamps and the caller's copies.
        remove_issue:        Remove the caller's copies of one series.
        add_item:            Add the caller's copy of a stamp.
        update_item:         Save the six fields of "Your copy".
        delete_item:         Remove the caller's copy.
        get_condition_types: The conditions the copy can have.
        get_locations:       The places a copy can be stored.
    """

    def __init__(self, token: str) -> None:
        """Take the user's JWT.

        Args:
            token: the token the login returned, sent as `Authorization: JWT`.
        """
        super().__init__()
        self._token: str = token

    @property
    def _auth_headers(self) -> dict[str, str]:
        """The header these endpoints accept, built from the token."""
        return {"Authorization": f"JWT {self._token}"}

    async def get_series(
        self,
        collection_id: int,
        page: int = 1,
        page_size: int = 15,
        name: str = "",
        year: str = "",
        sort_by: str = "date",
        order: str = "asc",
    ) -> requests.Response | None:
        """Fetch one page of the series of a collection.

        Args:
            collection_id: the collection whose series are read.
            page: 1-based page number.
            page_size: series per page; 0 means all.
            name: filter by series name.
            year: a year or a `start-end` range.
            sort_by: `date` or `name`.
            order: `asc` or `desc`.

        Returns:
            Raw requests.Response with `issues` and `pagination`, or None on a
            network error.
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

        url = f"{URLs.Backend.collections}{collection_id}/issues/?{urlencode(params)}"
        return await self._make_request(
            request_type=self.GET,
            url=url,
            headers=self._auth_headers,
        )

    async def get_issue(
        self, collection_id: int, issue_id: int
    ) -> requests.Response | None:
        """Fetch one series with every stamp and the caller's copy.

        Args:
            collection_id: the collection the series belongs to.
            issue_id: the series to read.

        Returns:
            Raw requests.Response with `issue`, `stamps` and `summary`, or None on
            a network error.
        """
        url = (
            f"{URLs.Backend.collections}{collection_id}/issues/{issue_id}/"
        )
        return await self._make_request(
            request_type=self.GET,
            url=url,
            headers=self._auth_headers,
        )

    async def remove_issue(
        self, collection_id: int, issue_id: int
    ) -> requests.Response | None:
        """Remove the caller's copies of one series from the collection.

        The catalogue keeps the series: this deletes what the collection holds.

        Args:
            collection_id: the collection the copies leave.
            issue_id: the series whose copies are removed.

        Returns:
            Raw requests.Response with how many copies went, or None on a network
            error.
        """
        url = (
            f"{URLs.Backend.collections}{collection_id}/issues/{issue_id}/"
        )
        return await self._make_request(
            request_type=self.DELETE,
            url=url,
            headers=self._auth_headers,
        )

    async def add_item(
        self, collection_id: int, stamp_id: int
    ) -> requests.Response | None:
        """Add the caller's copy of a catalogue stamp.

        Args:
            collection_id: the collection to add it to.
            stamp_id: the catalogue stamp.

        Returns:
            Raw requests.Response (201 on success, 409 when it is already there),
            or None on a network error.
        """
        url = f"{URLs.Backend.collections}{collection_id}/items/"
        return await self._make_request(
            request_type=self.POST,
            url=url,
            payload={"stamp": stamp_id},
            headers=self._auth_headers,
        )

    async def update_item(
        self, item_id: int, data: dict
    ) -> requests.Response | None:
        """Save the six fields of one copy.

        Args:
            item_id: the collection item.
            data: the fields to write; the API refuses anything but the six.

        Returns:
            Raw requests.Response (200 on success), or None on a network error.
        """
        url = f"{URLs.Backend.collection_items}{item_id}"
        return await self._make_request(
            request_type=self.PUT,
            url=url,
            payload=data,
            headers=self._auth_headers,
        )

    async def delete_item(self, item_id: int) -> requests.Response | None:
        """Remove the caller's copy.

        Args:
            item_id: the collection item.

        Returns:
            Raw requests.Response (200 on success), or None on a network error.
        """
        url = f"{URLs.Backend.collection_items}{item_id}"
        return await self._make_request(
            request_type=self.DELETE,
            url=url,
            headers=self._auth_headers,
        )

    async def get_condition_types(self) -> requests.Response | None:
        """Fetch the conditions a copy can have."""
        return await self._make_request(
            request_type=self.GET,
            url=URLs.Backend.condition_types,
            headers=self._auth_headers,
        )

    async def get_locations(self) -> requests.Response | None:
        """Fetch the places a copy can be stored in."""
        return await self._make_request(
            request_type=self.GET,
            url=URLs.Backend.locations,
            headers=self._auth_headers,
        )
