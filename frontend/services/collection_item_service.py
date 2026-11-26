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
        get_series: One page of the series the collection holds something of.
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
