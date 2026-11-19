"""Stamp images, read from a folder mounted into the container (S10).

The pictures do not live in the database: `Stamp.image` is empty and the frontend
keeps one ``.webp`` per FESOFI code under ``<year>/<code>.webp``. DataDesk reads
that same folder read-only, so adding an image on the server needs no rebuild —
it shows up here within the cache lifetime.

A missing folder is not an error: it means "no pictures configured" and every
stamp falls back to the hollow marker.

The listing is cached once per minute and **handed to the caller**, because the
shared cache is a file: reading it is cheap but not free, and a page of stamps
would pay for it once per row.
"""
import logging
import re
from pathlib import Path

from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

IMAGE_SUFFIX = ".webp"
"""Extension of the files the frontend ships."""

CODE_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
"""FESOFI codes are alphanumeric (``0001``, ``SPD2262``); nothing else is a file."""

INDEX_TIMEOUT = 60
"""Seconds the folder listing is reused.

A minute is the right trade: an image dropped on the server shows up on the next
refresh, and no request has to walk 136 folders twice.
"""

ImageIndex = frozenset[tuple[str, str]]
"""The pairs a folder scan produces."""


def image_root() -> Path:
    """Returns the folder that holds the ``<year>/<code>.webp`` tree."""
    return Path(settings.DATADESK_STAMP_IMAGES)


def image_index() -> ImageIndex:
    """Returns every ``(year, code)`` pair that has a picture, cached."""
    key = f"datadesk.stamp_images:{image_root()}"
    cached = cache.get(key)
    if cached is not None:
        return cached

    index = _scan(image_root())
    cache.set(key, index, INDEX_TIMEOUT)
    return index


def has_picture(
    year: int | str | None,
    code: str | None,
    index: ImageIndex | None = None,
) -> bool:
    """Tells whether a stamp has a picture, without touching the disk.

    Counting the "needs attention" queue asks this 9.000 times; resolving a path
    for each row would cost two ``resolve`` calls apiece for an answer that only
    needs set membership.
    """
    if year in (None, "") or not code:
        return False

    return (str(year), code) in (index if index is not None else image_index())


def image_path(
    year: int | str | None,
    code: str | None,
    index: ImageIndex | None = None,
) -> Path | None:
    """Resolves the picture of one stamp, or ``None`` when there is none.

    The year comes from the series, never from the stamp: a stamp belongs to
    exactly one series and inherits its year. Callers that resolve many stamps
    at once pass the index so it is read from the cache only once.
    """
    if year in (None, "") or not code or not CODE_PATTERN.match(code):
        return None

    folder = str(year)
    if (folder, code) not in (index if index is not None else image_index()):
        return None

    root = image_root().resolve()
    path = (root / folder / f"{code}{IMAGE_SUFFIX}").resolve()
    if not path.is_relative_to(root):
        return None
    return path


def _scan(root: Path) -> ImageIndex:
    """Walks the tree once and returns the pairs that exist.

    An empty folder is warned about as well as a missing one: a bind mount whose
    host path does not exist is silently created as an empty directory, and the
    only symptom is every thumbnail falling back to the placeholder. The message
    says where to look instead of leaving the cause to a guess.
    """
    if not root.is_dir():
        logger.warning("DataDesk stamp images folder not found: %s", root)
        return frozenset()

    found = frozenset(
        (folder.name, picture.stem)
        for folder in root.iterdir()
        if folder.is_dir()
        for picture in folder.glob(f"*{IMAGE_SUFFIX}")
    )
    if not found:
        logger.warning(
            "DataDesk stamp images folder is empty: %s (a bind mount whose host "
            "path does not exist is created empty, with no error)",
            root,
        )
    return found
