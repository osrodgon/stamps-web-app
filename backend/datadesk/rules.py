"""Rules about the year of a series, shared by the form and the write layer.

The workspace form uses them to bound its input and the write layer to validate
what arrives, so the browser and the server cannot drift apart: a year the form
accepts is a year the writer accepts.
"""

from django.utils import timezone

MIN_SERIES_YEAR = 1800
"""Anything below this is a typo, not a year of the collection."""

YEARS_AHEAD = 2
"""How far past the current year a series may be dated (catalogues announce)."""


def series_year_bounds() -> tuple[int, int]:
    """Returns the range a series year may take, both ends included."""
    return MIN_SERIES_YEAR, timezone.now().year + YEARS_AHEAD
