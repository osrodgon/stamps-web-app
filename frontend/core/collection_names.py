"""The name of a collection, remembered across the screens (2026-11-28).

Moving between series — or clicking the collection in the breadcrumb — rebuilds the
screen, and every rebuild used to fetch the collection just to write its name in the
header: the name arrived a moment later, so it was painted twice. A collection is
renamed in one place and the id never changes, so the name is worth keeping.

The cache is a process-wide dictionary with three operations and no expiry: the overview
remembers every name it lists, the series screen remembers the one it opened, and the
series detail reads it before asking the API. A miss is not an error: the screen falls
back to the request it always made.
"""

from __future__ import annotations

from typing import Optional


class CollectionNames:
    """What the app knows about each collection's name, by id."""

    #: `{collection id: name}`; small enough to keep for the life of the process.
    _names: dict[int, str] = {}

    @classmethod
    def remember(cls, collection_id: int, name: str) -> None:
        """Keep a name, overriding whatever was there.

        Args:
            collection_id: the collection's id.
            name: what it is called; an empty name is not worth keeping.
        """
        if name:
            cls._names[int(collection_id)] = name

    @classmethod
    def get(cls, collection_id: int) -> Optional[str]:
        """The name the app has, or None when it has never seen it.

        Args:
            collection_id: the collection's id.

        Returns:
            The remembered name, or None.
        """
        return cls._names.get(int(collection_id))

    @classmethod
    def forget(cls, collection_id: int) -> None:
        """Drop a name, for a collection that was deleted or renamed elsewhere.

        Args:
            collection_id: the collection's id.
        """
        cls._names.pop(int(collection_id), None)

    @classmethod
    def clear(cls) -> None:
        """Empty the cache; the tests use it to start from nothing."""
        cls._names.clear()
