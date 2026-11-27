"""Service for the catalogue a collection can add from (plan step C3).

It is separate from `CollectionItemService` because it speaks a different subject:
that one is about the copies the user owns, this one about the catalogue a collection
can still add from. Like every service in the app it is Flet-free and takes the user's
JWT in the constructor; the page reads the token and passes it in.

The two reads mirror the collection's own endpoints — same parameters, same
`pagination` block — so the dialog reuses the parsing the other screens already do.
"""

from __future__ import annotations

from urllib.parse import urlencode

import requests

from core.urls import URLs
from services.base_service import BaseService


class CatalogueService(BaseService):
    """Service for the catalogue of one collection.

    Public methods:
        search_issues: One page of the catalogue, with what the collection owns.
        get_issue:     One series of the catalogue, with `item` or None per stamp.
        add_stamps:    Add some stamps of the catalogue by id.
        add_issue:     Add every stamp of a series.
        add_year:      Add every stamp of a year.
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

    async def search_issues(
        self,
        collection_id: int,
        page: int = 1,
        page_size: int = 15,
        name: str = "",
        year: str = "",
        sort_by: str = "date",
        order: str = "asc",
    ) -> requests.Response | None:
        """Fetch one page of the catalogue for a collection.

        Args:
            collection_id: the collection the catalogue is read for.
            page: 1-based page number.
            page_size: series per page; 0 means all.
            name: filter by series name.
            year: a year or a range, with either end open (`1850-`, `-1860`).
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

        url = (
            f"{URLs.Backend.collections}{collection_id}"
            f"/catalogue/issues/?{urlencode(params)}"
        )
        return await self._make_request(
            request_type=self.GET,
            url=url,
            headers=self._auth_headers,
        )

    async def get_issue(
        self, collection_id: int, issue_id: int
    ) -> requests.Response | None:
        """Fetch one series of the catalogue, owned or not.

        Args:
            collection_id: the collection the copies would go into.
            issue_id: the series to read.

        Returns:
            Raw requests.Response with `issue`, `stamps` and `summary`, or None on
            a network error.
        """
        url = (
            f"{URLs.Backend.collections}{collection_id}"
            f"/catalogue/issues/{issue_id}/"
        )
        return await self._make_request(
            request_type=self.GET,
            url=url,
            headers=self._auth_headers,
        )

    async def add_stamps(
        self, collection_id: int, stamp_ids: list[int]
    ) -> requests.Response | None:
        """Add some stamps of the catalogue by id.

        Args:
            collection_id: the collection the copies go into.
            stamp_ids: the catalogue stamps to add.

        Returns:
            Raw requests.Response (201 with the three counts), or None on a
            network error.
        """
        return await self.__add(
            collection_id, {"scope": "stamp", "ids": list(stamp_ids)}
        )

    async def add_issue(
        self, collection_id: int, issue_id: int
    ) -> requests.Response | None:
        """Add every stamp of a series.

        Args:
            collection_id: the collection the copies go into.
            issue_id: the series whose stamps are added.

        Returns:
            Raw requests.Response (201 with the three counts), or None on a
            network error.
        """
        return await self.__add(
            collection_id, {"scope": "issue", "issue": issue_id}
        )

    async def add_year(
        self, collection_id: int, year: int
    ) -> requests.Response | None:
        """Add every stamp of a year of the catalogue.

        Args:
            collection_id: the collection the copies go into.
            year: the emission year whose stamps are added.

        Returns:
            Raw requests.Response (201 with the three counts), or None on a
            network error.
        """
        return await self.__add(collection_id, {"scope": "year", "year": year})

    async def __add(
        self, collection_id: int, payload: dict
    ) -> requests.Response | None:
        """Post one scope to the bulk endpoint.

        The three adds differ only in the body, and the endpoint is one: the scope
        is what says which key travels.

        Args:
            collection_id: the collection the copies go into.
            payload: the scope and its key.

        Returns:
            Raw requests.Response, or None on a network error.
        """
        url = f"{URLs.Backend.collections}{collection_id}/items/bulk/"
        return await self._make_request(
            request_type=self.POST,
            url=url,
            payload=payload,
            headers=self._auth_headers,
        )
