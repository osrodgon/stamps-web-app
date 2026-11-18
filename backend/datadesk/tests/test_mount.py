"""S1 acceptance: DataDesk is mounted only when the flag is on."""
from django.test import Client, override_settings
from django.urls import reverse

DATADESK_PATH = "/datadesk/"


class TestDataDeskMount:
    """Checks the feature flag gates the `/datadesk/` mount."""

    def test_disabled_returns_404(self, reload_urlconf) -> None:
        with override_settings(DATADESK_ENABLED=False):
            reload_urlconf()
            response = Client().get(DATADESK_PATH)

        assert response.status_code == 404

    def test_enabled_mounts_the_app(self, reload_urlconf) -> None:
        """The flag on replaces the 404 with the app: anonymous hits the login."""
        with override_settings(DATADESK_ENABLED=True):
            reload_urlconf()
            response = Client().get(DATADESK_PATH)

        assert response.status_code == 302
        assert response["Location"].startswith("/datadesk/login/")

    def test_enabled_mounts_on_its_own_path(self, reload_urlconf) -> None:
        with override_settings(DATADESK_ENABLED=True):
            reload_urlconf()
            reversed_url = reverse("datadesk:dashboard")

        assert reversed_url == DATADESK_PATH
        assert "api/v1" not in reversed_url
