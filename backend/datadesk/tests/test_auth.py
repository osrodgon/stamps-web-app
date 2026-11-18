"""S3 acceptance: login, logout, staff gate and login throttling."""
import json
import subprocess
import sys
import time
from pathlib import Path

import pytest
from django.conf import settings
from django.core.cache import cache
from django.core.cache.backends.filebased import FileBasedCache
from django.test import Client, override_settings

from datadesk.tests.helpers import UNHASHED_STATIC_STORAGES
from datadesk.views import auth

LOGIN_URL = "/datadesk/login/"
LOGOUT_URL = "/datadesk/logout/"
DASHBOARD_URL = "/datadesk/"
THROTTLE_KEY = "datadesk:login:{username}:127.0.0.1"


@pytest.fixture
def mounted(reload_urlconf):
    """Mounts DataDesk and renders templates without a collected manifest."""
    with override_settings(
        DATADESK_ENABLED=True, STORAGES=UNHASHED_STATIC_STORAGES
    ):
        reload_urlconf()
        yield


@pytest.fixture
def local_cache(settings) -> None:
    """Keeps the throttle counters in memory, so tests never touch .cache/."""
    settings.CACHES = {
        "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}
    }
    cache.clear()
    yield
    cache.clear()


def make_user(django_user_model, username, *, is_staff, password="s3cret-pass"):
    """Creates a user with the flags the gate looks at."""
    return django_user_model.objects.create_user(
        username=username, password=password, is_staff=is_staff
    )


@pytest.mark.django_db
class TestStaffGate:
    """Only active staff users get into `/datadesk/`."""

    def test_anonymous_is_redirected_to_the_login(self, mounted) -> None:
        response = Client().get(DASHBOARD_URL)

        assert response.status_code == 302
        assert response["Location"] == f"{LOGIN_URL}?next={DASHBOARD_URL}"

    def test_non_staff_user_gets_403(self, mounted, django_user_model) -> None:
        make_user(django_user_model, "visitor", is_staff=False)
        client = Client()
        client.login(username="visitor", password="s3cret-pass")

        response = client.get(DASHBOARD_URL)

        assert response.status_code == 403

    def test_staff_user_gets_the_dashboard(self, mounted, django_user_model) -> None:
        make_user(django_user_model, "curator", is_staff=True)
        client = Client()
        client.login(username="curator", password="s3cret-pass")

        response = client.get(DASHBOARD_URL)

        assert response.status_code == 200

    def test_gate_leaves_other_paths_alone(self, mounted) -> None:
        """The `is_staff` gate is path-scoped: admin and the API keep working."""
        client = Client()

        assert client.get("/admin/login/").status_code == 200
        assert (
            client.get("/stamps-backend/api/v1/health/").status_code != 403
        )

    def test_json_caller_gets_401_instead_of_a_redirect(self, mounted) -> None:
        response = Client().get(DASHBOARD_URL, headers={"Accept": "application/json"})

        assert response.status_code == 401
        assert response.json()["success"] is False


@pytest.mark.django_db
class TestLoginAndLogout:
    """The login form and the logout view behave as expected."""

    def test_login_page_renders(self, mounted) -> None:
        response = Client().get(LOGIN_URL)

        assert response.status_code == 200
        assert b'name="username"' in response.content
        assert b'name="password"' in response.content

    def test_valid_credentials_land_on_the_dashboard(
        self, mounted, django_user_model
    ) -> None:
        make_user(django_user_model, "curator", is_staff=True)

        response = Client().post(
            LOGIN_URL,
            {"username": "curator", "password": "s3cret-pass"},
        )

        assert response.status_code == 302
        assert response["Location"] == DASHBOARD_URL

    def test_logout_rejects_get(self, mounted, django_user_model) -> None:
        make_user(django_user_model, "curator", is_staff=True)
        client = Client()
        client.login(username="curator", password="s3cret-pass")

        assert client.get(LOGOUT_URL).status_code == 405

    def test_logout_closes_the_session(self, mounted, django_user_model) -> None:
        make_user(django_user_model, "curator", is_staff=True)
        client = Client()
        client.login(username="curator", password="s3cret-pass")

        response = client.post(LOGOUT_URL)

        assert response.status_code == 302
        assert response["Location"] == LOGIN_URL
        assert client.get(DASHBOARD_URL).status_code == 302


@pytest.mark.django_db
class TestLoginThrottle:
    """Failed logins are counted in the cache and answered with 429."""

    def _fail(self, client: Client, attempts: int, username: str = "curator"):
        """Posts the wrong password ``attempts`` times."""
        response = None
        for _ in range(attempts):
            response = client.post(
                LOGIN_URL, {"username": username, "password": "wrong"}
            )
        return response

    def test_sixth_failure_is_throttled(
        self, mounted, local_cache, django_user_model
    ) -> None:
        make_user(django_user_model, "curator", is_staff=True)
        client = Client()

        response = self._fail(client, 6)

        assert response.status_code == 429
        assert response["Retry-After"].isdigit()

    def test_below_the_limit_still_renders_the_form(
        self, mounted, local_cache, django_user_model
    ) -> None:
        make_user(django_user_model, "curator", is_staff=True)

        response = self._fail(Client(), 5)

        assert response.status_code == 200

    def test_successful_login_clears_the_counter(
        self, mounted, local_cache, django_user_model
    ) -> None:
        make_user(django_user_model, "curator", is_staff=True)
        client = Client()
        key = THROTTLE_KEY.format(username="curator")
        self._fail(client, 4)
        assert cache.get(key) == 4

        client.post(LOGIN_URL, {"username": "curator", "password": "s3cret-pass"})
        response = self._fail(Client(), 2)

        assert cache.get(key) == 2
        assert response.status_code == 200

    def test_counter_expires_with_the_window(
        self, mounted, local_cache, django_user_model, mocker
    ) -> None:
        make_user(django_user_model, "curator", is_staff=True)
        mocker.patch.object(auth, "THROTTLE_WINDOW_SECONDS", 1)
        client = Client()
        assert self._fail(client, 6).status_code == 429

        time.sleep(1.1)

        assert self._fail(Client(), 1).status_code == 200

    def test_htmx_caller_gets_the_partial(
        self, mounted, local_cache, django_user_model
    ) -> None:
        make_user(django_user_model, "curator", is_staff=True)

        for _ in range(5):
            Client().post(LOGIN_URL, {"username": "curator", "password": "wrong"})
        response = Client().post(
            LOGIN_URL,
            {"username": "curator", "password": "wrong"},
            headers={"HX-Request": "true"},
        )

        assert response.status_code == 429
        assert b"<html" not in response.content
        assert b"Too many failed attempts" in response.content


class TestThrottleCacheBackend:
    """The counter lives in the file cache, shared by the gunicorn workers."""

    def test_default_backend_is_the_file_cache(self) -> None:
        backend = settings.CACHES["default"]["BACKEND"]

        assert backend == "django.core.cache.backends.filebased.FileBasedCache"
        assert str(settings.CACHES["default"]["LOCATION"]).endswith(".cache")

    def test_two_workers_see_the_same_counter(self, tmp_path: Path) -> None:
        first = FileBasedCache(str(tmp_path / "shared"), {})
        second = FileBasedCache(str(tmp_path / "shared"), {})

        first.set("datadesk:login:curator:127.0.0.1", 4)
        second.incr("datadesk:login:curator:127.0.0.1")

        assert first.get("datadesk:login:curator:127.0.0.1") == 5


class TestTlsSettings:
    """`DATADESK_TLS` only flips cookie and proxy settings, never logic."""

    def test_current_settings_match_the_flag(self) -> None:
        assert settings.SESSION_COOKIE_SECURE is settings.DATADESK_TLS
        assert settings.CSRF_COOKIE_SECURE is settings.DATADESK_TLS

    @pytest.mark.parametrize(
        ("flag", "secure", "proxy_header"),
        (("0", False, None), ("1", True, ["HTTP_X_FORWARDED_PROTO", "https"])),
    )
    def test_flag_drives_cookies_and_proxy_header(
        self, flag: str, secure: bool, proxy_header: list[str] | None
    ) -> None:
        result = self._settings_with_tls(flag)

        assert result["session_cookie_secure"] is secure
        assert result["csrf_cookie_secure"] is secure
        assert result["proxy_header"] == proxy_header

    def test_secure_proxy_header_is_absent_when_tls_is_off(self) -> None:
        result = self._settings_with_tls("0")

        assert result["proxy_header"] is None

    @staticmethod
    def _settings_with_tls(flag: str) -> dict:
        """Imports the real settings module in a throwaway process.

        Settings are built once per process, so `override_settings` cannot show
        what the module does under a different environment.
        """
        script = (
            "import json, os, django;"
            "os.environ.setdefault('DJANGO_SETTINGS_MODULE', '_backend.settings');"
            "django.setup();"
            "from django.conf import settings;"
            "print(json.dumps({"
            "'session_cookie_secure': settings.SESSION_COOKIE_SECURE,"
            "'csrf_cookie_secure': settings.CSRF_COOKIE_SECURE,"
            "'proxy_header': list(settings.SECURE_PROXY_SSL_HEADER)"
            " if settings.SECURE_PROXY_SSL_HEADER[1] else None}))"
        )
        env = {"DJANGO_SETTINGS_MODULE": "_backend.settings", "DATADESK_TLS": flag}
        completed = subprocess.run(
            [sys.executable, "-c", script],
            cwd=settings.BASE_DIR,
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )

        return json.loads(completed.stdout.strip().splitlines()[-1])
