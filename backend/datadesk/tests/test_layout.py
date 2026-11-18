"""S2 acceptance: the shared page shell and the assets it pulls in."""
import re

import pytest
from django.test import Client, RequestFactory, override_settings
from django.template.loader import render_to_string

from datadesk.tests.helpers import UNHASHED_STATIC_STORAGES

VENDOR_ASSETS = (
    "datadesk/vendor/htmx.min.js",
    "datadesk/vendor/alpine.min.js",
    "datadesk/vendor/tabulator.min.js",
    "datadesk/vendor/tabulator.min.css",
)


@pytest.fixture
def base_html(reload_urlconf) -> str:
    """Renders ``base.html`` with the app mounted and a real request."""
    with override_settings(
        DATADESK_ENABLED=True, STORAGES=UNHASHED_STATIC_STORAGES
    ):
        reload_urlconf()
        request = RequestFactory().get("/datadesk/")
        return render_to_string("datadesk/base.html", request=request)


class TestBaseLayout:
    """The layout every DataDesk screen is built on."""

    def test_renders_the_topbar_with_the_brand(self, base_html: str) -> None:
        assert 'class="dd-topbar"' in base_html
        assert "dd-brand" in base_html

    def test_links_the_vendored_assets(self, base_html: str) -> None:
        for asset in VENDOR_ASSETS:
            assert asset in base_html

    def test_links_the_datadesk_stylesheet(self, base_html: str) -> None:
        assert "datadesk/datadesk.css" in base_html

    def test_body_carries_the_csrf_header_for_htmx(self, base_html: str) -> None:
        match = re.search(r'"X-CSRFToken": "([^"]*)"', base_html)

        assert match is not None
        assert len(match.group(1)) == 64


class TestDashboardOnTheBaseLayout:
    """``dashboard.html`` extends the shell instead of duplicating it."""

    @pytest.mark.django_db
    def test_dashboard_renders_inside_the_shell(
        self, reload_urlconf, django_user_model
    ) -> None:
        django_user_model.objects.create_user(
            username="curator", password="s3cret-pass", is_staff=True
        )
        with override_settings(
            DATADESK_ENABLED=True, STORAGES=UNHASHED_STATIC_STORAGES
        ):
            reload_urlconf()
            client = Client()
            client.login(username="curator", password="s3cret-pass")
            response = client.get("/datadesk/")

        content = response.content.decode()
        assert response.status_code == 200
        assert 'class="dd-topbar"' in content
        assert "dd-main" in content
        assert "<b>Dashboard</b>" in content
