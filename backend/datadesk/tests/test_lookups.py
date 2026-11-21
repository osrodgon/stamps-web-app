"""S19 acceptance: the reference tables screen, and merging two rows safely.

The screen is one template for eight lookups, so the tests are written against
the registry rather than per table: what is checked is the contract every lookup
shares — the usage count, the duplicate name, the merge that moves references and
the delete that only works on a row nobody points at — plus the two shapes that
are genuinely different, the colours (a stamp may hold both) and the years
(``CASCADE``, so a merge must move series instead of taking them along).
"""

import json
import re

import pytest
from django.conf import settings
from django.db import connection
from django.utils import timezone
from django.test import Client
from django.test.utils import CaptureQueriesContext

from artists_api.models import Artist
from colors_api.models import Color
from countries_api.models import Country
from datadesk.lookups import (
    create_next_years,
    delete_lookup,
    lookup_page,
    merge_lookups,
    rename_lookup,
)
from datadesk.models import DataDeskChange
from datadesk.write import WriteError
from issues_api.models import Issue
from stamps_api.models import Stamp
from years_api.models import Year

TABLE_URL = "/datadesk/lookups/{key}/"
ROWS_URL = "/datadesk/lookups/{key}/rows"
CREATE_URL = "/datadesk/lookups/{key}/create"
RENAME_URL = "/datadesk/lookups/{key}/rename"
DELETE_URL = "/datadesk/lookups/{key}/delete"
MERGE_URL = "/datadesk/lookups/merge"
NEXT_YEARS_URL = "/datadesk/lookups/years/next"
INDEX_URL = "/datadesk/lookups/"
JSON = "application/json"


@pytest.fixture
def writer(db, django_user_model):
    """The user the service is called as."""
    return django_user_model.objects.create_user(
        username="writer", password="s3cret-pass", is_staff=True
    )


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
    """Two artists: one used by a series, one that nobody has."""
    return [
        Artist.objects.create(name="Murillo"),
        Artist.objects.create(name="Murillo y su taller"),
    ]


@pytest.fixture
def series(db, artists) -> Issue:
    """One series pointing at the first artist."""
    return Issue.objects.create(
        year=Year.objects.create(year=1987),
        name="Exposición de Málaga",
        artist=artists[0],
    )


def post(client: Client, url: str, body) -> object:
    """Posts a JSON body the way the screen's script does."""
    return client.post(url, data=json.dumps(body), content_type=JSON)


@pytest.mark.django_db
class TestTheGrid:
    """Usage is annotated, so a page of rows costs a page of queries."""

    def test_counts_the_references_of_each_row(self, artists, series) -> None:
        rows = {row["name"]: row["usage"] for row in lookup_page("artist").rows}

        assert rows == {"Murillo": 1, "Murillo y su taller": 0}

    def test_the_page_costs_two_queries(self, artists, series) -> None:
        """One count for the pagination and one for the rows, never one per row."""
        with CaptureQueriesContext(connection) as captured:
            lookup_page("artist")

        assert len(captured.captured_queries) == 2

    def test_colours_are_counted_through_the_stamps(self, db) -> None:
        red = Color.objects.create(name="Rojo")
        stamp = Stamp.objects.create(issue=issue_with_year(), name="A", face_value="1")
        stamp.colors.set([red])

        rows = {row["name"]: row["usage"] for row in lookup_page("color").rows}

        assert rows["Rojo"] == 1

    def test_the_search_filters_and_keeps_the_count(self, artists) -> None:
        page = lookup_page("artist", "taller")

        assert [row["name"] for row in page.rows] == ["Murillo y su taller"]
        assert page.total == 1

    def test_the_page_is_clamped(self, artists) -> None:
        page = lookup_page("artist", page=99)

        assert page.page == 1
        assert page.last_page == 1

    def test_the_rows_are_sorted_by_their_name(self, db) -> None:
        for name in ("Zamora", "Abel", "Molina"):
            Artist.objects.create(name=name)

        assert [row["name"] for row in lookup_page("artist").rows] == [
            "Abel",
            "Molina",
            "Zamora",
        ]


@pytest.mark.django_db
class TestTheSeriesBehindARow:
    """S30: the usage number is a door, and the number is the one behind it."""

    def test_every_row_carries_its_series_and_their_link(self, artists, series) -> None:
        row = next(r for r in lookup_page("artist").rows if r["name"] == "Murillo")

        assert row["series"] == 1
        assert row["filter_url"] == f"/datadesk/issues/?artist={row['id']}"

    def test_a_colour_counts_series_and_not_stamps(self, db) -> None:
        """The usage column counts stamps; the grid behind it counts series."""
        red = Color.objects.create(name="Rojo")
        record = issue_with_year()
        for name in ("A", "B"):
            stamp = Stamp.objects.create(issue=record, name=name, face_value="1")
            stamp.colors.set([red])

        row = lookup_page("color").rows[0]

        assert row["usage"] == 2
        assert row["series"] == 1

    def test_a_year_links_its_own_range(self, db) -> None:
        issue_with_year()

        row = lookup_page("year").rows[0]

        assert row["filter_url"] == "/datadesk/issues/?year_min=1987&year_max=1987"

    def test_a_rename_answers_the_row_with_its_link(self, artists, series, staff_client) -> None:
        artist = artists[1]

        body = post(
            staff_client,
            RENAME_URL.format(key="artist"),
            {"id": artist.pk, "name": "Taller de Murillo"},
        ).json()

        assert body["data"]["series"] == 0
        assert body["data"]["filter_url"].endswith(f"?artist={artist.pk}")

    def test_nobody_has_a_dead_link_at_zero(self, artists, series) -> None:
        row = next(
            r for r in lookup_page("artist").rows if r["name"] == "Murillo y su taller"
        )

        assert row["series"] == 0


@pytest.mark.django_db
class TestRenaming:
    """A taken name is the offer to merge, not a failure."""

    def test_the_name_changes_and_is_audited(self, artists, writer) -> None:
        row = rename_lookup("artist", artists[1].pk, "  Taller de Murillo  ", writer)

        assert row["name"] == "Taller de Murillo"
        artists[1].refresh_from_db()
        assert artists[1].name == "Taller de Murillo"
        change = DataDeskChange.objects.get(operation="update")
        assert change.before["name"] == "Murillo y su taller"
        assert change.after["name"] == "Taller de Murillo"

    def test_a_duplicate_answers_the_id_of_the_other_row(self, artists, writer) -> None:
        with pytest.raises(WriteError) as refused:
            rename_lookup("artist", artists[1].pk, "Murillo", writer)

        assert refused.value.status == 409
        assert refused.value.extra["error"] == "duplicate_name"
        assert refused.value.extra["existing_id"] == artists[0].pk
        artists[1].refresh_from_db()
        assert artists[1].name == "Murillo y su taller"

    def test_writing_the_same_name_is_not_a_change(self, artists, writer) -> None:
        rename_lookup("artist", artists[0].pk, "Murillo", writer)

        assert DataDeskChange.objects.count() == 0

    def test_an_empty_name_is_refused(self, artists, writer) -> None:
        with pytest.raises(WriteError) as refused:
            rename_lookup("artist", artists[0].pk, "   ", writer)

        assert refused.value.status == 400

    def test_a_year_is_a_number(self, db) -> None:
        year = Year.objects.create(year=1987)

        with pytest.raises(WriteError):
            rename_lookup("year", year.pk, "mil novecientos", _nobody())

        assert rename_lookup("year", year.pk, "1988", _nobody())["name"] == "1988"

    def test_an_unknown_row_is_a_404(self, db, writer) -> None:
        with pytest.raises(WriteError) as refused:
            rename_lookup("artist", 9999, "Nadie", writer)

        assert refused.value.status == 404


@pytest.mark.django_db
class TestDeleting:
    """Only a row nobody points at can go."""

    def test_an_unused_row_is_deleted_and_audited(self, artists, writer) -> None:
        delete_lookup("artist", artists[1].pk, writer)

        assert not Artist.objects.filter(pk=artists[1].pk).exists()
        assert DataDeskChange.objects.get(operation="delete").object_id == artists[1].pk

    def test_a_row_in_use_is_refused_with_its_count(
        self, artists, series, writer
    ) -> None:
        with pytest.raises(WriteError) as refused:
            delete_lookup("artist", artists[0].pk, writer)

        assert refused.value.status == 409
        assert refused.value.extra["usage"] == 1
        assert Artist.objects.filter(pk=artists[0].pk).exists()


@pytest.mark.django_db
class TestMergingForeignKeys:
    """Move the references, delete the source, keep one name."""

    def test_the_references_move_and_the_source_goes(
        self, artists, series, writer
    ) -> None:
        result = merge_lookups("artist", artists[1].pk, artists[0].pk, "a", writer)

        series.refresh_from_db()
        assert series.artist_id == artists[0].pk
        assert not Artist.objects.filter(pk=artists[1].pk).exists()
        assert result.moved == 0
        assert result.target == {"id": artists[0].pk, "name": "Murillo"}

    def test_a_used_source_reports_how_many_it_moved(self, db, writer) -> None:
        source = Artist.objects.create(name="Murillo (taller)")
        target = Artist.objects.create(name="Murillo")
        for index in range(3):
            Issue.objects.create(
                year=Year.objects.create(year=1980 + index),
                name=f"Serie {index}",
                artist=source,
            )

        result = merge_lookups("artist", source.pk, target.pk, "a", writer)

        assert result.moved == 3
        assert Issue.objects.filter(artist=target).count() == 3

    def test_the_series_timestamp_moves_with_the_reference(self, db, writer) -> None:
        """``auto_now`` does not fire on ``update()``: S12's conflict check would
        otherwise keep comparing against a row that changed."""
        source = Artist.objects.create(name="Viejo")
        target = Artist.objects.create(name="Nuevo")
        issue = Issue.objects.create(
            year=Year.objects.create(year=1987), name="Serie", artist=source
        )
        before = Issue.objects.get(pk=issue.pk).updated_at

        merge_lookups("artist", source.pk, target.pk, "a", writer)

        assert Issue.objects.get(pk=issue.pk).updated_at > before

    def test_keeping_the_source_name_renames_the_survivor(self, db, writer) -> None:
        source = Artist.objects.create(name="El bueno")
        target = Artist.objects.create(name="El malo")

        result = merge_lookups("artist", source.pk, target.pk, "b", writer)

        target.refresh_from_db()
        assert target.name == "El bueno"
        assert result.target["name"] == "El bueno"
        assert not Artist.objects.filter(pk=source.pk).exists()

    def test_the_merge_is_one_audit_row_with_both_counts(self, db, writer) -> None:
        source = Artist.objects.create(name="Origen")
        target = Artist.objects.create(name="Destino")
        Issue.objects.create(
            year=Year.objects.create(year=1987), name="Serie", artist=source
        )

        result = merge_lookups("artist", source.pk, target.pk, "a", writer)

        change = DataDeskChange.objects.get(operation="merge")
        assert change.commit_id == result.commit_id
        assert change.object_id == source.pk
        assert change.before == {"lookup": "Origen", "refs": 1}
        assert change.after == {"lookup": "Destino", "refs": 1}

    def test_a_row_cannot_be_merged_into_itself(self, artists, writer) -> None:
        with pytest.raises(WriteError):
            merge_lookups("artist", artists[0].pk, artists[0].pk, "a", writer)

    def test_an_unknown_row_is_a_404(self, artists, writer) -> None:
        with pytest.raises(WriteError) as refused:
            merge_lookups("artist", 9999, artists[0].pk, "a", writer)

        assert refused.value.status == 404


@pytest.mark.django_db
class TestMergingColours:
    """A stamp can hold both colours: the junction table has to agree."""

    def test_a_stamp_with_both_ends_with_one_row(self, db, writer) -> None:
        red = Color.objects.create(name="Rojo")
        crimson = Color.objects.create(name="Rojo Carmín")
        stamp = Stamp.objects.create(issue=issue_with_year(), name="A", face_value="1")
        stamp.colors.set([red, crimson])
        through = Stamp.colors.through

        merge_lookups("color", crimson.pk, red.pk, "a", writer)

        assert through.objects.filter(stamp=stamp).count() == 1
        assert list(stamp.colors.values_list("pk", flat=True)) == [red.pk]
        assert not Color.objects.filter(pk=crimson.pk).exists()

    def test_a_stamp_with_only_the_source_gains_the_target(self, db, writer) -> None:
        red = Color.objects.create(name="Rojo")
        crimson = Color.objects.create(name="Rojo Carmín")
        stamp = Stamp.objects.create(issue=issue_with_year(), name="A", face_value="1")
        stamp.colors.set([crimson])

        result = merge_lookups("color", crimson.pk, red.pk, "a", writer)

        assert result.moved == 1
        stamp.refresh_from_db()
        assert list(stamp.colors.values_list("pk", flat=True)) == [red.pk]

    def test_the_stamp_timestamp_moves_with_its_colours(self, db, writer) -> None:
        red = Color.objects.create(name="Rojo")
        crimson = Color.objects.create(name="Rojo Carmín")
        stamp = Stamp.objects.create(issue=issue_with_year(), name="A", face_value="1")
        stamp.colors.set([crimson])
        before = Stamp.objects.get(pk=stamp.pk).updated_at

        merge_lookups("color", crimson.pk, red.pk, "a", writer)

        assert Stamp.objects.get(pk=stamp.pk).updated_at > before


@pytest.mark.django_db
class TestMergingYears:
    """``Year`` is ``CASCADE``: a merge moves the series, it does not eat them."""

    def test_the_series_move_to_the_surviving_year(self, db, writer) -> None:
        source = Year.objects.create(year=1987)
        target = Year.objects.create(year=1988)
        issue = Issue.objects.create(year=source, name="Serie")

        result = merge_lookups("year", source.pk, target.pk, "a", writer)

        issue.refresh_from_db()
        assert issue.year_id == target.pk
        assert result.moved == 1
        assert not Year.objects.filter(pk=source.pk).exists()


@pytest.mark.django_db
class TestTheYearsAction:
    """A year only exists once a series uses it, so the next decade is a click."""

    def test_creates_the_ten_after_the_newest(self, db) -> None:
        Year.objects.create(year=1987)

        created = create_next_years(10)

        assert created == 10
        assert sorted(Year.objects.values_list("year", flat=True))[:2] == [1987, 1988]
        assert Year.objects.filter(year=1997).exists()

    def test_the_count_is_capped(self, db) -> None:
        Year.objects.create(year=2000)

        assert create_next_years(500) == 50


@pytest.mark.django_db
class TestTheEndpoints:
    """The HTTP boundary: gate, shapes and status codes."""

    def test_the_index_lists_the_eight_tables(self, staff_client, artists) -> None:
        content = staff_client.get(INDEX_URL).content.decode()

        for label in ("Year", "Country", "Color", "Artist", "Printer"):
            assert label in content
        assert 'href="/datadesk/lookups/artist/"' in content

    def test_the_table_page_renders_the_grid(self, staff_client, artists) -> None:
        content = staff_client.get(TABLE_URL.format(key="artist")).content.decode()

        assert 'id="lookup-grid"' in content
        assert 'id="merge-button"' in content
        assert 'id="lookup-search"' in content

    def test_the_years_page_offers_the_decade(self, staff_client, db) -> None:
        content = staff_client.get(TABLE_URL.format(key="year")).content.decode()

        assert 'id="next-years"' in content
        other = staff_client.get(TABLE_URL.format(key="artist")).content.decode()
        assert 'id="next-years"' not in other

    def test_every_element_the_script_reads_is_on_the_page(
        self, staff_client, artists
    ) -> None:
        """A renamed id is a page that silently stops working: check the names.

        The years page is the one that renders every control, the optional
        "next ten years" button included.
        """
        content = staff_client.get(TABLE_URL.format(key="year")).content.decode()
        script = (
            settings.BASE_DIR / "datadesk" / "static" / "datadesk" / "lookups.js"
        ).read_text(encoding="utf-8")

        wanted = set(re.findall(r'getElementById\("([^"]+)"\)', script))
        missing = [
            name
            for name in wanted
            if name != "lookup-config" and f'id="{name}"' not in content
        ]

        assert missing == []

    def test_the_page_offers_a_new_row(self, staff_client, artists) -> None:
        content = staff_client.get(TABLE_URL.format(key="artist")).content.decode()

        assert 'id="new-row-button"' in content
        assert 'id="new-row-panel"' in content
        assert 'id="new-row-confirm"' in content
        assert 'type="text"' in content.split('id="new-row-name"')[1][:200]

    def test_the_year_input_is_a_number_with_the_bounds(self, staff_client, db) -> None:
        content = staff_client.get(TABLE_URL.format(key="year")).content.decode()

        assert 'id="new-row-name"' in content
        assert 'type="number"' in content.split('id="new-row-name"')[1][:200]
        assert 'min="1800"' in content
        assert f'max="{timezone.localdate().year + 2}"' in content

    def test_the_create_url_travels_in_the_config(self, staff_client, artists) -> None:
        content = staff_client.get(TABLE_URL.format(key="artist")).content.decode()
        blob = content.split('id="lookup-config" type="application/json">')[1]
        config = json.loads(blob.split("</script>")[0])

        assert config["createUrl"] == CREATE_URL.format(key="artist")
        assert config["texts"]["newRow"] == "New row"
        assert config["texts"]["createRow"] == "Create the row"
        assert config["texts"]["rowCreated"] == "The row was created."
        assert config["texts"]["rowExists"] == "That row already existed."
        assert config["bounds"] == {}

    def test_the_years_carry_their_bounds_in_the_config(self, staff_client, db) -> None:
        content = staff_client.get(TABLE_URL.format(key="year")).content.decode()
        blob = content.split('id="lookup-config" type="application/json">')[1]
        config = json.loads(blob.split("</script>")[0])

        assert config["bounds"] == {
            "min": 1800,
            "max": timezone.localdate().year + 2,
        }

    def test_an_unknown_table_is_a_404(self, staff_client, db) -> None:
        assert staff_client.get(TABLE_URL.format(key="planet")).status_code == 404

    def test_the_config_carries_the_urls_and_the_texts(
        self, staff_client, artists
    ) -> None:
        content = staff_client.get(TABLE_URL.format(key="artist")).content.decode()
        blob = content.split('id="lookup-config" type="application/json">')[1]
        config = json.loads(blob.split("</script>")[0])

        assert config["key"] == "artist"
        assert config["rowsUrl"] == ROWS_URL.format(key="artist")
        assert config["mergeUrl"] == MERGE_URL
        assert config["texts"]["usage"] == "Used by"
        assert config["plurals"]["usage"]["other"] == "Used by %(count)s rows"
        assert config["numeric"] is False

    def test_the_rows_endpoint_answers_tabulators_shape(
        self, staff_client, artists, series
    ) -> None:
        body = staff_client.get(ROWS_URL.format(key="artist")).json()

        assert body["total"] == 2
        assert body["last_page"] == 1
        assert {row["name"] for row in body["data"]} == {
            "Murillo",
            "Murillo y su taller",
        }
        assert body["data"][0]["usage"] == 1

    def test_the_rename_endpoint_answers_409_with_the_id(
        self, staff_client, artists
    ) -> None:
        response = post(
            staff_client,
            RENAME_URL.format(key="artist"),
            {"id": artists[1].pk, "name": "Murillo"},
        )

        body = response.json()
        assert response.status_code == 409
        assert body["error"] == "duplicate_name"
        assert body["existing_id"] == artists[0].pk

    def test_the_delete_endpoint_answers_409_in_use(
        self, staff_client, artists, series
    ) -> None:
        response = post(
            staff_client, DELETE_URL.format(key="artist"), {"id": artists[0].pk}
        )

        body = response.json()
        assert response.status_code == 409
        assert body["error"] == "in_use"
        assert body["usage"] == 1

    def test_the_merge_endpoint_moves_and_reports(
        self, staff_client, artists, series
    ) -> None:
        response = post(
            staff_client,
            MERGE_URL,
            {
                "table": "artist",
                "from_id": artists[1].pk,
                "to_id": artists[0].pk,
                "keep_name_from": "a",
            },
        )

        body = response.json()
        assert response.status_code == 200
        assert body["success"] is True
        assert body["survivor"]["id"] == artists[0].pk
        assert Artist.objects.count() == 1

    def test_the_next_years_endpoint_creates_them(self, staff_client, db) -> None:
        Year.objects.create(year=1987)

        body = post(staff_client, NEXT_YEARS_URL, {"count": 3}).json()

        assert body["created"] == 3
        assert Year.objects.filter(year__in=[1988, 1989, 1990]).count() == 3

    def test_anonymous_gets_a_401_on_the_endpoints(self, mounted, artists) -> None:
        response = post(
            Client(HTTP_ACCEPT=JSON),
            MERGE_URL,
            {"table": "artist", "from_id": 1, "to_id": 2},
        )

        assert response.status_code == 401
        assert Artist.objects.count() == 2

    def test_an_anonymous_browser_is_sent_to_the_login(self, mounted, db) -> None:
        response = Client().get(INDEX_URL)

        assert response.status_code == 302
        assert response["Location"].startswith("/datadesk/login/")


def issue_with_year() -> Issue:
    """A series to hang stamps on, with its own year row."""
    return Issue.objects.create(year=Year.objects.create(year=1987), name="Serie")


def _nobody():
    """An anonymous actor, for the calls that only check the write."""
    return None
