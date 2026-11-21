"""S10 acceptance: the read-only issue workspace."""
import json

import pytest
from django.core.cache import cache
from django.db import connection
from django.test import Client
from django.test.utils import CaptureQueriesContext

from colors_api.models import Color
from countries_api.models import Country
from issues_api.models import Issue
from stamps_api.models import Stamp
from years_api.models import Year

PAGE_URL = "/datadesk/issues/{pk}/"


@pytest.fixture
def issue(db, tmp_path, settings) -> Issue:
    """A series with two stamps, one of them with a picture.

    The first one also gets a picture in a temporary images folder, so the row
    and the workspace page can be checked against something real.
    """
    root = tmp_path / "stamps"
    (root / "1987").mkdir(parents=True)
    (root / "1987" / "1234.webp").write_bytes(b"RIFF\x00\x00\x00\x00WEBPVP8 ")
    settings.DATADESK_STAMP_IMAGES = root
    cache.clear()

    year = Year.objects.create(year=1987)
    spain = Country.objects.create(name="España")
    carmine = Color.objects.create(name="Carmín")
    blue = Color.objects.create(name="Azul")

    record = Issue.objects.create(
        year=year,
        date="1987-05-12",
        name="Exposición de Málaga",
        country=spain,
        description="Serie conmemorativa",
        total_printed=500000,
        market_value_mnh="1.20",
        market_value_used="0.80",
    )

    with_picture = Stamp.objects.create(
        issue=record,
        edifil_code="2744",
        fesofi_code="1234",
        name="Exposición de Málaga",
        face_value="15 Ptas",
        description="Serie conmemorativa",
        total_printed=500000,
        market_value_mnh="1.20",
        market_value_used="0.80",
        image="stamps/a.jpg",
    )
    with_picture.colors.set([carmine])

    own = Stamp.objects.create(
        issue=record,
        edifil_code="2745",
        fesofi_code="1235",
        name="Bandera nacional",
        face_value="5 Ptas",
        total_printed=750000,
        market_value_mnh="1.20",
        market_value_used="0.95",
    )
    own.colors.set([blue])

    return record


@pytest.fixture
def staff_client(mounted, django_user_model) -> Client:
    """A logged-in staff client."""
    django_user_model.objects.create_user(
        username="curator", password="s3cret-pass", is_staff=True
    )
    client = Client()
    client.login(username="curator", password="s3cret-pass")
    return client


def config_of(response) -> dict:
    """Returns the grid configuration the page ships."""
    content = response.content.decode()
    blob = content.split('id="stamp-config" type="application/json">')[1]
    return json.loads(blob.split("</script>")[0])


@pytest.mark.django_db
class TestWorkspacePage:
    """The page renders the series and its stamps."""

    def test_renders_the_issue_and_its_stamps(self, staff_client, issue) -> None:
        response = staff_client.get(PAGE_URL.format(pk=issue.pk))
        content = response.content.decode()

        assert response.status_code == 200
        assert "Exposición de Málaga" in content
        assert "2744" in content
        assert "2745" in content

    def test_shows_the_metadata_strip(self, staff_client, issue) -> None:
        content = staff_client.get(PAGE_URL.format(pk=issue.pk)).content.decode()

        assert "España" in content
        assert "1987" in content
        assert "Serie conmemorativa" in content

    def test_stamp_count_matches_the_rows(self, staff_client, issue) -> None:
        response = staff_client.get(PAGE_URL.format(pk=issue.pk))

        assert response.context["stamp_count"] == 2

    def test_an_issue_without_stamps_renders(self, staff_client, db) -> None:
        empty = Issue.objects.create(year=Year.objects.create(year=1900), name="Vacía")

        response = staff_client.get(PAGE_URL.format(pk=empty.pk))

        assert response.status_code == 200
        assert response.context["stamp_count"] == 0

    def test_a_missing_issue_is_a_404(self, staff_client, db) -> None:
        response = staff_client.get(PAGE_URL.format(pk=999999))

        assert response.status_code == 404

    def test_nothing_in_the_strip_is_marked_as_inherited(
        self, staff_client, issue
    ) -> None:
        """Series values describe the set: no stamp inherits them."""
        response = staff_client.get(PAGE_URL.format(pk=issue.pk))

        assert not any(
            field.get("inheritable") for field in response.context["form_fields"]
        )

    def test_the_grid_carries_the_columns_translated(self, staff_client, issue) -> None:
        config = config_of(staff_client.get(PAGE_URL.format(pk=issue.pk)))
        titles = [column["title"] for column in config["columns"]]

        assert "Edifil" in titles
        assert "Colors" in titles
        assert "Total printed" in titles
        assert config["issuesUrl"] == "/datadesk/issues/"

    def test_the_description_is_a_hidden_column(self, staff_client, issue) -> None:
        """Prose in a 13px cell is an ellipsis: the pane owns the widget and the
        column exists only so the value travels with the row."""
        config = config_of(staff_client.get(PAGE_URL.format(pk=issue.pk)))
        column = next(
            item for item in config["columns"] if item["field"] == "description"
        )

        assert column["hidden"] is True
        assert column["patch"] == "description"
        assert column["title"] == "Stamp description"
        assert config["fieldLabels"]["stamp"]["description"] == "Stamp description"

    def test_the_preview_pane_ships_with_the_page(self, staff_client, issue) -> None:
        content = staff_client.get(PAGE_URL.format(pk=issue.pk)).content.decode()

        assert 'id="stamp-preview"' in content
        assert 'id="preview-image"' in content
        assert 'id="preview-description"' in content
        assert "Select a stamp to see its picture and description." in content

    def test_the_placeholder_picture_is_shipped(self, staff_client, issue) -> None:
        config = config_of(staff_client.get(PAGE_URL.format(pk=issue.pk)))

        assert config["fallbackImage"] == "/static/datadesk/no_stamp.webp"


@pytest.mark.django_db
class TestStampRows:
    """The shape of the rows the grid consumes."""

    def test_colors_travel_with_their_name_and_tone(self, staff_client, issue) -> None:
        rows = config_of(staff_client.get(PAGE_URL.format(pk=issue.pk)))["data"]

        assert rows[0]["colors"] == [{"name": "Carmín", "tone": "red"}]
        assert rows[1]["colors"] == [{"name": "Azul", "tone": "blue"}]

    def test_decimals_travel_as_strings(self, staff_client, issue) -> None:
        rows = config_of(staff_client.get(PAGE_URL.format(pk=issue.pk)))["data"]

        assert rows[0]["mnh"] == "1.20"
        assert rows[0]["used"] == "0.80"

    def test_the_picture_is_a_boolean_and_a_url(self, staff_client, issue) -> None:
        rows = config_of(staff_client.get(PAGE_URL.format(pk=issue.pk)))["data"]

        assert rows[0]["has_image"] is True
        assert rows[0]["image_url"].endswith(f"/datadesk/stamps/{rows[0]['id']}/image")
        assert rows[1]["has_image"] is False
        assert rows[1]["image_url"] is None

    def test_no_value_is_marked_as_inherited(self, staff_client, issue) -> None:
        rows = config_of(staff_client.get(PAGE_URL.format(pk=issue.pk)))["data"]

        assert all("inherited" not in row for row in rows)

    def test_the_description_travels_with_the_row(self, staff_client, issue) -> None:
        rows = config_of(staff_client.get(PAGE_URL.format(pk=issue.pk)))["data"]

        assert rows[0]["description"] == "Serie conmemorativa"
        assert rows[1]["description"] == ""

    def test_the_series_attributes_are_not_repeated_per_row(
        self, staff_client, issue
    ) -> None:
        rows = config_of(staff_client.get(PAGE_URL.format(pk=issue.pk)))["data"]

        for attribute in ("country", "year", "stamp_type", "printer", "artist"):
            assert attribute not in rows[0]


@pytest.mark.django_db
class TestQueryCount:
    """One series does not cost one query per stamp."""

    def test_the_cost_does_not_grow_with_the_stamps(self, staff_client, issue) -> None:
        # Same series shape, a hundred stamps instead of two: the only thing
        # that may change is the size of the stamp query.
        long_issue = Issue.objects.create(
            year=Year.objects.create(year=1951),
            name="Larga",
            country=issue.country,
        )
        for index in range(100):
            Stamp.objects.create(
                issue=long_issue, name=f"Sello {index}", face_value="1 Pta"
            )

        with CaptureQueriesContext(connection) as short:
            short_response = staff_client.get(PAGE_URL.format(pk=issue.pk))
        with CaptureQueriesContext(connection) as long:
            long_response = staff_client.get(PAGE_URL.format(pk=long_issue.pk))

        assert short_response.context["stamp_count"] == 2
        assert long_response.context["stamp_count"] == 100
        assert len(short.captured_queries) == len(long.captured_queries)

    def test_stamps_and_colors_are_one_query_each(self, staff_client, issue) -> None:
        with CaptureQueriesContext(connection) as captured:
            staff_client.get(PAGE_URL.format(pk=issue.pk))

        stamp_queries = [
            query
            for query in captured.captured_queries
            if 'FROM "stamps_api_stamp"' in query["sql"]
        ]
        color_queries = [
            query
            for query in captured.captured_queries
            if 'FROM "colors_api_color"' in query["sql"]
        ]

        assert len(stamp_queries) == 1
        assert len(color_queries) == 1


@pytest.mark.django_db
class TestAccess:
    """The workspace follows the same rules as the rest of DataDesk."""

    def test_anonymous_browsers_go_to_the_login(self, mounted, issue) -> None:
        response = Client().get(PAGE_URL.format(pk=issue.pk))

        assert response.status_code == 302
        assert "/datadesk/login/" in response["Location"]

    def test_non_staff_users_are_refused(
        self, mounted, issue, django_user_model
    ) -> None:
        django_user_model.objects.create_user(username="pepe", password="s3cret-pass")
        client = Client()
        client.login(username="pepe", password="s3cret-pass")

        response = client.get(PAGE_URL.format(pk=issue.pk))

        assert response.status_code == 403
