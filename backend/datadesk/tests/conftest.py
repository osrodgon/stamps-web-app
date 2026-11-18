"""Fixtures shared by the DataDesk tests."""
import importlib

import pytest
from django.test import override_settings
from django.urls import clear_url_caches

from datadesk.tests.helpers import UNHASHED_STATIC_STORAGES


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
