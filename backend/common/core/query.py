"""Reading a query parameter once (plan step C2).

Two views of the collection module read the same six parameters with the same defaults,
because the catalogue page mirrors the collection's. The `try/except` that turns `"abc"`
into the default lives here instead of in both.
"""

from __future__ import annotations

from typing import Optional


class Query:
    """Helpers for the values that arrive as strings."""

    @staticmethod
    def int_param(value: Optional[str], default: int) -> int:
        """Read an integer query parameter, or `default` when it is not one.

        Args:
            value: the raw parameter; `None` when it did not come.
            default: what to answer when it is missing or not a number.

        Returns:
            The number, or the default.
        """
        try:
            return int(value)
        except (TypeError, ValueError):
            return default
