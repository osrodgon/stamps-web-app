"""S4 acceptance: English and Spanish, and the frontend locales untouched."""
import pytest
from django.conf import settings
from django.core.management import call_command
from django.test import Client

LANGUAGE_URL = "/datadesk/language/"
DASHBOARD_URL = "/datadesk/"
LOGIN_URL = "/datadesk/login/"
SPANISH_HINT = "Mantenimiento interno de la base de datos."
SPANISH_DASHBOARD = "Panel"
ENGLISH_DASHBOARD = "Dashboard"


@pytest.fixture
def staff_client(mounted, django_user_model) -> Client:
    """Logs a staff user in so the dashboard is reachable."""
    django_user_model.objects.create_user(
        username="curator", password="s3cret-pass", is_staff=True
    )
    client = Client()
    client.login(username="curator", password="s3cret-pass")
    return client


@pytest.mark.django_db
class TestLanguageSwitch:
    """The EN/ES control changes the interface language."""

    def test_spanish_is_installed(self) -> None:
        assert settings.DATADESK_LANGUAGES == ("en", "es")
        assert "django.middleware.locale.LocaleMiddleware" in settings.MIDDLEWARE

    def test_dashboard_starts_in_english(self, staff_client) -> None:
        content = staff_client.get(DASHBOARD_URL).content.decode()

        assert ENGLISH_DASHBOARD in content
        assert SPANISH_HINT not in content

    def test_switching_to_spanish_translates_the_dashboard(
        self, staff_client
    ) -> None:
        staff_client.post(
            LANGUAGE_URL, {"language": "es", "next": DASHBOARD_URL}
        )

        content = staff_client.get(DASHBOARD_URL).content.decode()

        assert SPANISH_HINT in content
        assert SPANISH_DASHBOARD in content

    def test_spanish_survives_a_reload(self, staff_client) -> None:
        staff_client.post(
            LANGUAGE_URL, {"language": "es", "next": DASHBOARD_URL}
        )
        staff_client.get(DASHBOARD_URL)

        content = staff_client.get(DASHBOARD_URL).content.decode()

        assert SPANISH_HINT in content

    def test_switching_back_to_english(self, staff_client) -> None:
        staff_client.post(LANGUAGE_URL, {"language": "es", "next": DASHBOARD_URL})
        staff_client.post(LANGUAGE_URL, {"language": "en", "next": DASHBOARD_URL})

        content = staff_client.get(DASHBOARD_URL).content.decode()

        assert ENGLISH_DASHBOARD in content
        assert SPANISH_HINT not in content

    def test_unknown_language_is_ignored(self, staff_client) -> None:
        response = staff_client.post(
            LANGUAGE_URL, {"language": "fr", "next": DASHBOARD_URL}
        )

        content = staff_client.get(DASHBOARD_URL).content.decode()
        assert response.status_code == 302
        assert ENGLISH_DASHBOARD in content
        assert SPANISH_HINT not in content

    def test_language_switch_is_post_only(self, staff_client) -> None:
        assert staff_client.get(LANGUAGE_URL).status_code == 405

    def test_anonymous_cannot_switch(self, mounted) -> None:
        response = Client().post(LANGUAGE_URL, {"language": "es"})

        assert response.status_code == 302
        assert response["Location"].startswith(LOGIN_URL)

    def test_login_page_is_translated(self, mounted) -> None:
        client = Client()
        client.cookies[settings.LANGUAGE_COOKIE_NAME] = "es"

        content = client.get(LOGIN_URL).content.decode()

        assert "Contraseña" in content


class TestCatalogs:
    """The catalogs are compiled and stay complete."""

    def test_compiled_catalogs_are_up_to_date(self) -> None:
        call_command("datadesk_make_messages", "--check")

    @pytest.mark.parametrize("language", ["en", "es"])
    def test_every_entry_is_translated(self, language: str) -> None:
        import polib

        path = settings.BASE_DIR / "datadesk" / "locale" / language / "LC_MESSAGES"
        catalog = polib.pofile(str(path / "django.po"))

        assert len(catalog) > 0
        assert [entry.msgid for entry in catalog if not entry.msgstr] == []

    def test_the_frontend_locales_are_not_referenced(self) -> None:
        """`assets/locales/*.json` belongs to the public app and stays untouched."""
        datadesk_dir = settings.BASE_DIR / "datadesk"
        offenders = [
            str(path)
            for path in datadesk_dir.rglob("*")
            if path.is_file()
            and path.suffix in {".py", ".html"}
            and "tests" not in path.parts
            and "assets/locales" in path.read_text(encoding="utf-8")
        ]

        assert offenders == []
