"""The version stamp on DataDesk's own assets.

With ``DEBUG`` on, ``/static/`` has no content hash, and a browser that keeps
yesterday's ``workbench.js`` runs it against today's HTML. S30 hit exactly that:
the new filter selects were on screen (they come from the template) while the
script that reads them was the old one, so the URL filtered and the grid did
not. Stamping the URL with the newest file's mtime makes the browser ask again
as soon as anything changes.

In production the manifest hashes already do this; the stamp is harmless there.
"""

from functools import lru_cache
from pathlib import Path
from typing import Any

from django.conf import settings


@lru_cache(maxsize=1)
def asset_version() -> str:
    """Returns a stamp that changes when a DataDesk asset changes.

    The vendor folder is left out: those files are pinned by ``VERSIONS.md`` and
    do not change between releases, so stamping them would only refetch half a
    megabyte of Tabulator for nothing.
    """
    root = Path(settings.BASE_DIR) / "datadesk" / "static" / "datadesk"
    files = [
        path
        for path in root.rglob("*")
        if path.is_file() and "vendor" not in path.relative_to(root).parts
    ]
    if not files:
        return ""
    return str(int(max(path.stat().st_mtime for path in files)))


def assets(request: Any) -> dict[str, str]:
    """Makes the stamp available to every DataDesk template."""
    return {"datadesk_asset_version": asset_version()}
