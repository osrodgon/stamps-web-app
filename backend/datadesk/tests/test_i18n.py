"""S4 acceptance: English and Spanish, and the frontend locales untouched."""
import re
from pathlib import Path

import pytest
from django.conf import settings
from django.core.management import call_command
from django.test import Client

LANGUAGE_URL = "/datadesk/language/"
SCRIPT_DIR = Path(__file__).resolve().parent.parent / "static" / "datadesk"
DASHBOARD_URL = "/datadesk/"
LOGIN_URL = "/datadesk/login/"
SPANISH_HINT = "Mantenimiento interno de la base de datos."

PROSE_SINK = re.compile(
    r"""\.(?:textContent|innerHTML|title|placeholder|alt)\s*=\s*["']([^"']*)["']"""
)
"""Where a script could put text on the screen without the server knowing."""

PROSE = re.compile(r"[A-Za-z]{2,}\s+[A-Za-z]{2,}")
"""Two words in a row: the glyphs a script may own (×, →, ·) have none."""
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

        def untranslated(entry) -> bool:
            """A plural entry keeps its forms in ``msgstr_plural``, not ``msgstr``."""
            if entry.msgid_plural:
                return any(not form for form in entry.msgstr_plural.values())
            return not entry.msgstr

        assert [entry.msgid for entry in catalog if untranslated(entry)] == []

    @pytest.mark.parametrize("language", ["en", "es"])
    def test_every_plural_has_the_forms_the_language_needs(self, language: str) -> None:
        """Both catalogs declare two forms; a plural entry must fill both."""
        import polib

        path = settings.BASE_DIR / "datadesk" / "locale" / language / "LC_MESSAGES"
        catalog = polib.pofile(str(path / "django.po"))

        for entry in catalog:
            if entry.msgid_plural:
                assert set(entry.msgstr_plural) == {0, 1}

    def test_check_notices_an_uncompiled_translation(self, tmp_path: Path) -> None:
        """A translation edited in the .po is stale until the .mo is rebuilt."""
        import polib

        from datadesk.management.commands.datadesk_make_messages import Command

        po_path = tmp_path / "django.po"
        catalog = polib.POFile()
        catalog.append(polib.POEntry(msgid="Sign in", msgstr="Entrar"))
        catalog.save(str(po_path))
        catalog.save_as_mofile(str(po_path.with_suffix(".mo")))

        assert Command._is_stale(po_path) is False

        catalog[0].msgstr = "Acceder"
        catalog.save(str(po_path))

        assert Command._is_stale(po_path) is True

    def test_the_scripts_hold_no_interface_text(self) -> None:
        """A sentence written in the JS is a sentence nobody translated.

        Class names, selectors and the three glyphs are fine; prose is not, and
        the only place it could hide is the handful of sinks that put text on
        screen. The check is a regex, so the two assertions below it say what
        "prose" means before it is applied to the files.
        """
        assert PROSE.search("No rows yet.")
        assert not PROSE.search("×")

        offenders = []
        for path in sorted(SCRIPT_DIR.glob("*.js")):
            source = path.read_text(encoding="utf-8")
            offenders += [
                f"{path.name}: {match.group(1)!r}"
                for match in PROSE_SINK.finditer(source)
                if PROSE.search(match.group(1))
            ]

        assert offenders == []

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
