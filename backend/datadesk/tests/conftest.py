"""Fixtures shared by the DataDesk tests."""
import importlib

import pytest
from django.core.cache import cache
from django.test import override_settings
from django.urls import clear_url_caches

from colors_api.models import Color
from countries_api.models import Country
from datadesk.tests.helpers import UNHASHED_STATIC_STORAGES
from issues_api.models import Issue
from stamps_api.models import Stamp
from years_api.models import Year


@pytest.fixture
def reload_urlconf():
    """Reloads ``_backend.urls`` so ``DATADESK_ENABLED`` overrides apply.

    The URLconf is imported once per process; ``override_settings`` alone does
    not remount the app, so the module is reloaded and restored afterwards.
    """

    def _reload() -> None:
        clear_url_caches()
        import _backend.urls

        importlib.reload(_backend.urls)

    yield _reload

    clear_url_caches()
    import _backend.urls

    importlib.reload(_backend.urls)


@pytest.fixture
def mounted(reload_urlconf):
    """Mounts DataDesk and renders templates without a collected manifest."""
    with override_settings(
        DATADESK_ENABLED=True, STORAGES=UNHASHED_STATIC_STORAGES
    ):
        reload_urlconf()
        yield


@pytest.fixture
def dataset(db, tmp_path, settings) -> dict:
    """Small, explicit dataset: every counter has rows and gaps.

    One stamp gets a picture in a temporary images folder, so the "without
    image" counter is checked against a folder and not against a missing one.
    """
    pictures = tmp_path / "stamps"
    (pictures / "1987").mkdir(parents=True)
    picture = pictures / "1987" / "1234.webp"
    picture.write_bytes(b"RIFF\x00\x00\x00\x00WEBPVP8 ")
    settings.DATADESK_STAMP_IMAGES = pictures
    cache.clear()

    year = Year.objects.create(year=1987)
    spain = Country.objects.create(name="España")
    color = Color.objects.create(name="Carmín")

    complete = Issue.objects.create(
        year=year, date="1987-05-12", name="Exposición de Málaga", country=spain
    )
    no_country = Issue.objects.create(year=year, date="1987-06-01", name="Sin país")
    no_date = Issue.objects.create(year=year, name="Sin fecha", country=spain)
    no_stamps = Issue.objects.create(
        year=year, date="1987-07-01", name="Sin sellos", country=spain
    )

    good = Stamp.objects.create(
        issue=complete,
        face_value="15 Ptas",
        name="Retrato",
        fesofi_code="1234",
    )
    good.colors.set([color])
    no_color = Stamp.objects.create(
        issue=complete, face_value="5 Ptas", name="Sin color"
    )
    no_face_value = Stamp.objects.create(
        issue=no_country, face_value="", name="Sin facial", image="stamps/c.jpg"
    )
    no_face_value.colors.set([color])
    dated = Stamp.objects.create(
        issue=no_date, face_value="1 Pta", name="Serie con fecha", image="stamps/d.jpg"
    )
    dated.colors.set([color])

    return {
        "issues": (complete, no_country, no_date, no_stamps),
        "stamps": (good, no_color, no_face_value),
    }
