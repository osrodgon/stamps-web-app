"""The parameterised routes of the Flet app (plan step B3).

`ROUTE_HANDLERS` in `main.py` is an exact-match dict, which is enough for `/login` or
`/collections` but not for `/collections/7`. This class holds the routes that carry an
id and builds their view, so the table stays exact and a new screen adds one pattern.
"""

from __future__ import annotations

import re
from typing import Optional

import flet as ft

from core.urls import URLs
from pages.collection.collection_series_page import CollectionSeriesPage


class RouteResolver:
    """Turns a path with an id into the view that renders it."""

    #: `/collections/<id>` — the series of one collection.
    SERIES = re.compile(
        rf"{re.escape(URLs.Frontend.collections)}/(?P<collection_id>\d+)"
    )

    @classmethod
    def view(cls, route: str, page: ft.Page) -> Optional[ft.View]:
        """Return the view for a parameterised route, or None.

        Args:
            route: the path Flet received.
            page: the Flet page the view is built on.

        Returns:
            The view, or None when the path has no ids this class knows.
        """
        series = cls.SERIES.fullmatch(route)
        if series is not None:
            return CollectionSeriesPage(page, int(series.group("collection_id")))
        return None
