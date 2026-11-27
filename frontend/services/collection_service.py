"""Service for the collections API, asked with the user's JWT (plan step A3).

The catalogue services speak with the master key. These endpoints are different:
they answer about one person, and they take the token the login returned. That is
why the service receives the token instead of reading `settings`: the page reads it
from `SharedPreferences` (Flet) and hands it over, so this layer stays Flet-free and
testable without a page.

The service does not interpret status codes. A 403 is "the session expired" for the
page, not for the HTTP client, exactly as `IssueService` leaves the meaning of a
status to its caller.
"""

from __future__ import annotations

import requests

from core.urls import URLs
from services.base_service import BaseService


class CollectionService(BaseService):
    """Service for the collections of the logged-in user.

    Public methods:
        get_collections:    The caller's collections with their counters and covers.
        create_collection:  Create one, owned by the caller.
        update_collection:  Rename one (PUT, the field that changes is the name).
        delete_collection:  Remove one, and its items with it.
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

    async def get_collections(self) -> requests.Response | None:
        """Fetch the caller's collections.

        Returns:
            Raw requests.Response with one row per collection, or None on a
            network error.
        """
        return await self._make_request(
            request_type=self.GET,
            url=URLs.Backend.collections,
            headers=self._auth_headers,
        )

    async def create_collection(self, name: str) -> requests.Response | None:
        """Create a collection owned by the caller.

        Args:
            name: the collection's name.

        Returns:
            Raw requests.Response (201 on success), or None on a network error.
        """
        return await self._make_request(
            request_type=self.POST,
            url=URLs.Backend.collections,
            payload={"name": name},
            headers=self._auth_headers,
        )

    async def update_collection(
        self, collection_id: int, name: str
    ) -> requests.Response | None:
        """Rename a collection of the caller.

        The backend's route has no trailing slash after the id, so the URL is built
        without one.

        Args:
            collection_id: the id of the collection to rename.
            name: the new name.

        Returns:
            Raw requests.Response (200 on success), or None on a network error.
        """
        url = f"{URLs.Backend.collections}{collection_id}"
        return await self._make_request(
            request_type=self.PUT,
            url=url,
            payload={"name": name},
            headers=self._auth_headers,
        )

    async def delete_collection(self, collection_id: int) -> requests.Response | None:
        """Delete a collection of the caller, and its items with it.

        Args:
            collection_id: the id of the collection to delete.

        Returns:
            Raw requests.Response (200 on success), or None on a network error.
        """
        url = f"{URLs.Backend.collections}{collection_id}"
        return await self._make_request(
            request_type=self.DELETE,
            url=url,
            headers=self._auth_headers,
        )
