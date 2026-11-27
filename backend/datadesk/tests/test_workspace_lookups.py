"""S18 acceptance: a reference row typed on the spot, and the search behind it.

The strip used to render a ``<select>`` with every row of every lookup, which
means the page shipped the whole artist and colour tables with each series and a
field could only offer what was already there. Now the field is typed: the page
ships the selected name, the search endpoint proposes rows as the user types, and
the + button creates the one nobody had.

These tests cover the server side of that contract — the search, the create with
its tone, the configuration the page needs — because the round trip that a person
sees is the browser's, and the throwaway jsdom harness is where it is exercised.
"""

import json

import pytest
from django.test import Client

from artists_api.models import Artist
from colors_api.models import Color
from countries_api.models import Country
from datadesk.service import LOOKUP_SEARCH_LIMIT, search_lookups
from issues_api.models import Issue
from years_api.models import Year

SEARCH_URL = "/datadesk/lookups/{key}/search"
CREATE_URL = "/datadesk/lookups/{key}/create"
PAGE_URL = "/datadesk/issues/{pk}/"
NEW_URL = "/datadesk/issues/new/"
JSON = "application/json"


@pytest.fixture
def staff_client(mounted, django_user_model) -> Client:
    """A logged-in staff client."""
    django_user_model.objects.create_user(
        username="curator", password="s3cret-pass", is_staff=True
    )
    client = Client()
    client.login(username="curator", password="s3cret-pass")
    return client


@pytest.fixture
def artists(db) -> list[Artist]:
    """Three artists, one of them the sort of name people get wrong."""
    return [
        Artist.objects.create(name="Anónimo"),
        Artist.objects.create(name="Bartolomé"),
        Artist.objects.create(name="Bartolomé Esteban Murillo"),
    ]


@pytest.fixture
def issue(db, artists) -> Issue:
    """One series with a country and an artist, the shortest useful case."""
    return Issue.objects.create(
        year=Year.objects.create(year=1987),
        name="Exposición de Málaga",
        country=Country.objects.create(name="España"),
        artist=artists[1],
    )


def config_of(response) -> dict:
    """Returns the grid configuration the page ships."""
    content = response.content.decode()
    blob = content.split('id="stamp-config" type="application/json">')[1]
    return json.loads(blob.split("</script>")[0])


def get(client: Client, url: str, params=None) -> list[dict]:
    """Returns the rows of a search response."""
    body = client.get(url, params or {}).json()
    assert body["success"] is True
    return body["data"]["results"]


@pytest.mark.django_db
class TestTheSearch:
    """What the field suggests while the user types."""

    def test_matches_a_fragment_anywhere_in_the_name(self, artists) -> None:
        assert [row["label"] for row in search_lookups("artist", "murillo")] == [
            "Bartolomé Esteban Murillo"
        ]

    def test_is_sorted_by_the_column_the_row_is_called_by(self, artists) -> None:
        labels = [row["label"] for row in search_lookups("artist", "bartolomé")]

        assert labels == ["Bartolomé", "Bartolomé Esteban Murillo"]

    def test_an_empty_query_proposes_the_first_rows(self, artists) -> None:
        """Opening the field must offer something, not nothing."""
        assert len(search_lookups("artist", "")) == 3

    def test_the_answer_is_short_on_purpose(self, db) -> None:
        Color.objects.bulk_create(
            [Color(name=f"Color {index:03d}") for index in range(120)]
        )

        rows = search_lookups("color", "")

        assert len(rows) == LOOKUP_SEARCH_LIMIT

    def test_a_number_lookup_searches_as_text(self, db) -> None:
        for year in (1987, 1990, 2024):
            Year.objects.create(year=year)

        assert [row["label"] for row in search_lookups("year", "199")] == ["1990"]

    def test_an_unknown_lookup_is_a_404(self, staff_client) -> None:
        response = staff_client.get(SEARCH_URL.format(key="planet"))

        assert response.status_code == 404

    def test_the_endpoint_answers_the_rows(self, staff_client, artists) -> None:
        rows = get(staff_client, SEARCH_URL.format(key="artist"), {"q": "bart"})

        assert [row["label"] for row in rows] == [
            "Bartolomé",
            "Bartolomé Esteban Murillo",
        ]
        assert all(isinstance(row["value"], int) for row in rows)

    def test_anonymous_gets_a_401(self, mounted, artists) -> None:
        response = Client(HTTP_ACCEPT=JSON).get(SEARCH_URL.format(key="artist"))

        assert response.status_code == 401

    def test_a_non_staff_user_gets_a_403(
        self, mounted, django_user_model, artists
    ) -> None:
        django_user_model.objects.create_user(
            username="visitor", password="s3cret-pass", is_staff=False
        )
        client = Client()
        client.login(username="visitor", password="s3cret-pass")

        response = client.get(SEARCH_URL.format(key="artist"))

        assert response.status_code == 403


@pytest.mark.django_db
class TestTheCreateAnswersWhatTheCellNeeds:
    """The cell paints a chip and selects an id, so both have to come back."""

    def test_a_colour_comes_back_with_its_tone(self, staff_client) -> None:
        body = staff_client.post(
            CREATE_URL.format(key="color"),
            data=json.dumps({"value": "Rojo Carmín"}),
            content_type=JSON,
        ).json()

        assert body["success"] is True
        assert body["data"]["name"] == "Rojo Carmín"
        assert body["data"]["tone"]

    def test_a_non_colour_has_no_tone(self, staff_client) -> None:
        body = staff_client.post(
            CREATE_URL.format(key="artist"),
            data=json.dumps({"value": "Pepito"}),
            content_type=JSON,
        ).json()

        assert "tone" not in body["data"]

    def test_a_duplicate_is_answered_with_the_existing_row(
        self, staff_client, artists
    ) -> None:
        """Creating twice must not fail: the field only wants the id."""
        body = staff_client.post(
            CREATE_URL.format(key="artist"),
            data=json.dumps({"value": "Anónimo"}),
            content_type=JSON,
        ).json()

        assert body["success"] is True
        assert body["data"]["created"] is False
        assert body["data"]["id"] == artists[0].pk


@pytest.mark.django_db
class TestTheFieldIsTyped:
    """The strip no longer renders a select for a reference field."""

    def test_the_page_renders_an_input_with_a_datalist(
        self, staff_client, issue
    ) -> None:
        content = staff_client.get(PAGE_URL.format(pk=issue.pk)).content.decode()

        assert 'id="field-country"' in content
        assert 'data-lookup="country"' in content
        assert 'list="lookup-country"' in content
        assert '<datalist id="lookup-country">' in content
        assert '<select class="dd-input" id="field-country"' not in content

    def test_the_selected_name_is_what_the_box_shows(self, staff_client, issue) -> None:
        content = staff_client.get(PAGE_URL.format(pk=issue.pk)).content.decode()

        assert 'value="España"' in content
        assert f'data-value="{issue.country_id}"' in content

    def test_every_reference_field_can_create_a_row(self, staff_client, issue) -> None:
        content = staff_client.get(PAGE_URL.format(pk=issue.pk)).content.decode()

        for field in (
            "country",
            "stamp_type",
            "print_type",
            "printer",
            "artist",
            "paper_type",
        ):
            assert f'data-create-for="{field}"' in content

    def test_the_create_button_starts_hidden(self, staff_client, issue) -> None:
        """A permanent button would invite a duplicate of what is already set."""
        content = staff_client.get(PAGE_URL.format(pk=issue.pk)).content.decode()

        assert 'data-create-for="artist" hidden' in content

    def test_new_mode_is_typed_too(self, staff_client, issue) -> None:
        content = staff_client.get(NEW_URL).content.decode()

        assert 'data-lookup="country"' in content
        assert "<select" not in content
        assert 'id="field-country"' in content


@pytest.mark.django_db
class TestTheConfigCarriesTheEndpoints:
    """The script holds no URL and no interface text, so both travel."""

    def test_the_search_and_create_urls(self, staff_client, issue) -> None:
        lookups = config_of(staff_client.get(PAGE_URL.format(pk=issue.pk)))["lookups"]

        assert set(lookups) == {
            "country",
            "stamp_type",
            "print_type",
            "printer",
            "artist",
            "paper_type",
            "color",
        }
        assert lookups["artist"]["search"] == SEARCH_URL.format(key="artist")
        assert lookups["artist"]["create"] == CREATE_URL.format(key="artist")

    def test_the_labels_are_translated(self, staff_client, issue) -> None:
        client = staff_client
        client.cookies["django_language"] = "es"

        labels = config_of(client.get(PAGE_URL.format(pk=issue.pk)))["lookupLabels"]

        assert labels["artist"] == "Artista"

    def test_the_texts_come_from_the_server(self, staff_client, issue) -> None:
        texts = config_of(staff_client.get(PAGE_URL.format(pk=issue.pk)))["lookupText"]

        assert set(texts) == {
            "create",
            "created",
            "failed",
            "unresolved",
            "remove",
            "newRows",
            "savedRow",
        }
        assert texts["create"] == '+ Create "%(name)s"'
        assert "%(name)s" in texts["unresolved"]
        # The pane's colour chips say what their × does, and they name it.
        assert texts["remove"] == "Remove %(name)s"

    def test_the_review_panel_has_a_group_for_them(self, staff_client, issue) -> None:
        texts = config_of(staff_client.get(PAGE_URL.format(pk=issue.pk)))["lookupText"]

        assert texts["newRows"] == "New reference rows"
        assert texts["savedRow"] == "Saved now: reference rows are reused."
