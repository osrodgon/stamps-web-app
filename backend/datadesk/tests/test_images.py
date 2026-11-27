"""S10: stamp pictures and colour tones.

The pictures are not in the database: they are a ``<year>/<code>.webp`` tree
mounted read-only from the frontend, and the tones come from `palette.py`.
"""
from pathlib import Path

import pytest
from django.contrib.staticfiles import finders
from django.core.cache import cache
from django.test import Client
from django.urls import reverse

from datadesk.images import image_index, image_path
from datadesk.palette import TONES, tone_for
from datadesk.service import issue_queryset, stamp_rows
from issues_api.models import Issue
from stamps_api.models import Stamp
from years_api.models import Year

PICTURE_BYTES = b"RIFF\x00\x00\x00\x00WEBPVP8 "


@pytest.fixture
def pictures(tmp_path, db, settings) -> dict:
    """A mounted folder with one picture, and stamps with and without one."""
    root = tmp_path / "stamps"
    folder = root / "1987"
    folder.mkdir(parents=True)
    (folder / "1234.webp").write_bytes(PICTURE_BYTES)
    settings.DATADESK_STAMP_IMAGES = root
    cache.clear()

    issue = Issue.objects.create(year=Year.objects.create(year=1987), name="Con foto")
    with_picture = Stamp.objects.create(
        issue=issue, name="Con foto", face_value="1 Pta", fesofi_code="1234"
    )
    without = Stamp.objects.create(
        issue=issue, name="Sin foto", face_value="1 Pta", fesofi_code="9999"
    )

    return {"root": root, "issue": issue, "with": with_picture, "without": without}


@pytest.fixture
def staff_client(mounted, django_user_model) -> Client:
    """A logged-in staff client."""
    django_user_model.objects.create_user(
        username="curator", password="s3cret-pass", is_staff=True
    )
    client = Client()
    client.login(username="curator", password="s3cret-pass")
    return client


class TestImageResolution:
    """The folder layout is the whole contract."""

    def test_a_known_pair_resolves_to_its_file(self, pictures) -> None:
        path = image_path(1987, "1234")

        assert path is not None
        assert path.name == "1234.webp"
        assert path.is_file()

    @pytest.mark.django_db
    def test_an_unknown_code_has_no_file(self, pictures) -> None:
        assert image_path(1987, "0000") is None

    @pytest.mark.django_db
    def test_an_unknown_year_has_no_file(self, pictures) -> None:
        assert image_path(1901, "1234") is None

    @pytest.mark.django_db
    def test_an_empty_year_or_code_is_not_a_file(self, pictures) -> None:
        assert image_path(None, "1234") is None
        assert image_path(1987, None) is None
        assert image_path(1987, "") is None

    @pytest.mark.django_db
    def test_a_code_cannot_escape_the_folder(self, pictures) -> None:
        assert image_path(1987, "../1987/1234") is None
        assert image_path(1987, "/etc/passwd") is None
        assert image_path(1987, "..%2F1987") is None

    @pytest.mark.django_db
    def test_a_missing_folder_means_no_pictures(self, tmp_path, settings) -> None:
        settings.DATADESK_STAMP_IMAGES = tmp_path / "nowhere"
        cache.clear()

        assert image_index() == set()
        assert image_path(1987, "1234") is None

    @pytest.mark.django_db
    def test_an_empty_folder_is_reported(self, tmp_path, settings, caplog) -> None:
        """A bind mount with a host path that does not exist is created empty."""
        empty = tmp_path / "images"
        empty.mkdir()
        settings.DATADESK_STAMP_IMAGES = empty
        cache.clear()

        with caplog.at_level("WARNING"):
            assert image_index() == set()

        assert "is empty" in caplog.text
        assert str(empty) in caplog.text

    @pytest.mark.django_db
    def test_a_new_file_appears_after_the_cache_expires(self, pictures) -> None:
        assert image_path(1987, "1234") is not None  # warms the cached listing

        folder = pictures["root"] / "1987"
        (folder / "5555.webp").write_bytes(PICTURE_BYTES)

        assert image_path(1987, "5555") is None  # cached for a minute

        cache.clear()

        assert image_path(1987, "5555") is not None


@pytest.mark.django_db
class TestBorder:
    """The picture is served through DataDesk, not from a public folder."""

    def test_the_file_is_served_as_webp(self, staff_client, pictures) -> None:
        url = reverse("datadesk:stamp_image", args=[pictures["with"].pk])

        response = staff_client.get(url)

        assert response.status_code == 200
        assert response["Content-Type"] == "image/webp"
        assert response["Cache-Control"].startswith("private")
        assert b"".join(response.streaming_content) == PICTURE_BYTES

    def test_a_stamp_without_picture_is_a_404(self, staff_client, pictures) -> None:
        url = reverse("datadesk:stamp_image", args=[pictures["without"].pk])

        assert staff_client.get(url).status_code == 404

    def test_a_missing_stamp_is_a_404(self, staff_client, pictures) -> None:
        url = reverse("datadesk:stamp_image", args=[999999])

        assert staff_client.get(url).status_code == 404

    def test_a_revisit_gets_a_304(self, staff_client, pictures) -> None:
        url = reverse("datadesk:stamp_image", args=[pictures["with"].pk])
        first = staff_client.get(url)

        second = staff_client.get(url, headers={"If-None-Match": first["ETag"]})

        assert second.status_code == 304

    def test_anonymous_callers_are_sent_to_the_login(self, mounted, pictures) -> None:
        url = reverse("datadesk:stamp_image", args=[pictures["with"].pk])

        assert Client().get(url).status_code == 302


@pytest.mark.django_db
class TestRowsCarryThePicture:
    """The grid is told, so it never builds a URL."""

    def test_a_stamp_with_picture_reports_it(self, pictures) -> None:
        rows = stamp_rows(issue_queryset().get(pk=pictures["issue"].pk))

        flags = {row["fesofi"]: row["has_image"] for row in rows}

        assert flags == {"1234": True, "9999": False}


class TestPalette:
    """Tones are data, not interface: they must not depend on the process."""

    @pytest.mark.parametrize(
        ("name", "tone"),
        (
            ("Carmín", "red"),
            ("Carmesí", "red"),
            ("Azul", "blue"),
            ("Azul verdoso", "blue"),
            ("Verde oliva", "green"),
            ("Sepia", "brown"),
            ("Castaño rojizo", "brown"),
            ("Ocre", "amber"),
            ("Oro", "amber"),
            ("Multicolor", "grey"),
            ("Cuatricomía", "grey"),
            ("Negro", "grey"),
            ("Violeta", "purple"),
            ("Naranja", "orange"),
        ),
    )
    def test_known_names_map_to_their_family(self, name: str, tone: str) -> None:
        assert tone_for(name) == tone

    def test_accents_and_case_do_not_matter(self) -> None:
        assert tone_for("carmin") == tone_for("CARMÍN")

    def test_an_unknown_name_is_stable(self) -> None:
        assert tone_for("Verdeazulado inventado") == tone_for("Verdeazulado inventado")

    def test_every_tone_is_one_of_the_palette(self) -> None:
        for name in ("", "X", "Multicolor extraño", "Ç"):
            assert tone_for(name) in TONES


class TestPlaceholder:
    """The picture used when a stamp has none ships with DataDesk.

    It is a copy of ``frontend/assets/no_stamp.webp``: the mount only covers the
    ``stamps`` folder, so the placeholder is served as a static file of the app.
    """

    def test_the_placeholder_exists_and_is_a_webp(self) -> None:
        found = finders.find("datadesk/no_stamp.webp")

        assert found is not None
        assert Path(found).read_bytes()[:4] == b"RIFF"
