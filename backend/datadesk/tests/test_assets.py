"""S2 acceptance: the vendored assets exist, are pinned and are intact."""
import hashlib
import re
from pathlib import Path

import pytest
from django.contrib.staticfiles import finders

VENDOR_FILES = (
    "datadesk/vendor/inter-latin-var.woff2",
    "datadesk/vendor/htmx.min.js",
    "datadesk/vendor/alpine.min.js",
    "datadesk/vendor/tabulator.min.js",
    "datadesk/vendor/tabulator.min.css",
)
VERSIONS_DOC = "datadesk/vendor/VERSIONS.md"
MIN_ASSET_SIZE = 10_000


def _sha256(path: Path) -> str:
    """Returns the hex digest of a file."""
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


@pytest.fixture(scope="module")
def versions_doc() -> str:
    """Reads the pinned-versions document."""
    path = finders.find(VERSIONS_DOC)
    assert path is not None
    return Path(path).read_text(encoding="utf-8")


class TestVendoredAssets:
    """The vendor bundle is committed, not fetched at runtime."""

    def test_every_asset_is_found_by_the_staticfiles_finders(self) -> None:
        for asset in VENDOR_FILES:
            assert finders.find(asset) is not None, asset

    def test_every_asset_has_content(self) -> None:
        for asset in VENDOR_FILES:
            size = Path(finders.find(asset)).stat().st_size
            assert size > MIN_ASSET_SIZE, f"{asset} is only {size} bytes"

    def test_versions_doc_pins_the_hashes(self, versions_doc: str) -> None:
        for asset in VENDOR_FILES:
            digest = _sha256(Path(finders.find(asset)))
            assert digest in versions_doc, f"{asset} does not match VERSIONS.md"

    def test_versions_doc_pins_a_version_per_asset(self, versions_doc: str) -> None:
        """Every row names a version. Two components are enough: the font's own
        version is 4.001, and the libraries use three."""
        for asset in VENDOR_FILES:
            row = next(
                line for line in versions_doc.splitlines() if Path(asset).name in line
            )
            assert re.search(r"\d+\.\d+", row), row
