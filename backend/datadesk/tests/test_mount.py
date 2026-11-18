"""S1 acceptance: DataDesk is mounted only when the flag is on.

The URLconf is imported once per process, so the flag cannot be flipped by
``override_settings`` alone: the module has to be reloaded after the override.
These tests do exactly that and restore the original URLconf afterwards.
"""
import importlib

import pytest
from django.test import Client, override_settings
from django.urls import clear_url_caches, reverse

DATADESK_PATH = "/datadesk/"


@pytest.fixture
def reload_urlconf():
    """Reloads ``_backend.urls`` and restores it when the test ends."""

    def _reload() -> None:
        clear_url_caches()
        import _backend.urls

        importlib.reload(_backend.urls)

    yield _reload

    clear_url_caches()
    import _backend.urls

    importlib.reload(_backend.urls)


@pytest.mark.django_db
class TestDataDeskMount:
    """Checks the feature flag gates the `/datadesk/` mount."""

    def test_disabled_returns_404(self, reload_urlconf) -> None:
        with override_settings(DATADESK_ENABLED=False):
            reload_urlconf()
            response = Client().get(DATADESK_PATH)

        assert response.status_code == 404

    def test_enabled_returns_200(self, reload_urlconf) -> None:
        with override_settings(DATADESK_ENABLED=True):
            reload_urlconf()
            response = Client().get(DATADESK_PATH)

        assert response.status_code == 200
        assert b"DataDesk" in response.content

    def test_enabled_mounts_on_its_own_path(self, reload_urlconf) -> None:
        with override_settings(DATADESK_ENABLED=True):
            reload_urlconf()
            reversed_url = reverse("datadesk:dashboard")

        assert reversed_url == DATADESK_PATH
        assert "api/v1" not in reversed_url
