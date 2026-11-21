"""S8 acceptance: the workbench endpoint and its filters."""
import json

import pytest
from django.core.cache import cache
from django.test import Client

from artists_api.models import Artist
from colors_api.models import Color
from countries_api.models import Country
from issues_api.models import Issue
from paper_types_api.models import PaperType
from print_types_api.models import PrintType
from printers_api.models import Printer
from stamp_types_api.models import StampType
from stamps_api.models import Stamp
from datadesk.service import DEFAULT_PAGE_SIZE, IssueFilters, page_of_issue
from years_api.models import Year

GRID_URL = "/datadesk/grid/issues"
PAGE_URL = "/datadesk/issues/"


@pytest.fixture
def grid_dataset(db, tmp_path, settings) -> dict:
    """Four issues covering every filter and every gap.

    The "without image" queue reads the mounted picture folder, not
    ``Stamp.image``: one stamp gets a file there, so the queue has a row that is
    complete and rows that are not.
    """
    pictures = tmp_path / "stamps"
    (pictures / "1980").mkdir(parents=True)
    (pictures / "1980" / "1234.webp").write_bytes(b"RIFF\x00\x00\x00\x00WEBPVP8 ")
    settings.DATADESK_STAMP_IMAGES = pictures
    cache.clear()

    year_1980 = Year.objects.create(year=1980)
    year_1990 = Year.objects.create(year=1990)
    spain = Country.objects.create(name="España")
    stamp_type = StampType.objects.create(name="Conmemorativo")
    color = Color.objects.create(name="Carmín")
    blue = Color.objects.create(name="Azul")
    printer = Printer.objects.create(name="Imprenta Nacional")
    artist = Artist.objects.create(name="Murillo")
    paper = PaperType.objects.create(name="Satinado")
    print_type = PrintType.objects.create(name="Offset")

    alfa = Issue.objects.create(
        year=year_1980,
        date="1980-05-12",
        name="Alfa",
        country=spain,
        stamp_type=stamp_type,
        printer=printer,
        artist=artist,
        paper_type=paper,
        print_type=print_type,
        market_value_mnh="5.75",
        market_value_used="3.50",
    )
    beta = Issue.objects.create(year=year_1990, date="1990-01-01", name="Beta")
    gamma = Issue.objects.create(year=year_1990, name="Gamma")
    delta = Issue.objects.create(
        year=year_1980, date="1980-11-11", name="Delta", country=spain
    )

    with_color = Stamp.objects.create(
        issue=alfa,
        face_value="15 Ptas",
        name="Con color",
        image="stamps/a.jpg",
        fesofi_code="1234",
    )
    # Two colours on one stamp: a join on colours would count the stamp twice,
    # which is exactly what the colour filter must not do.
    with_color.colors.set([color, blue])
    Stamp.objects.create(issue=beta, face_value="5 Ptas", name="Sin color")
    Stamp.objects.create(issue=delta, face_value="", name="Sin facial")

    return {"alfa": alfa, "beta": beta, "gamma": gamma, "delta": delta}


@pytest.fixture
def staff_client(mounted, django_user_model) -> Client:
    """A logged-in staff client."""
    django_user_model.objects.create_user(
        username="curator", password="s3cret-pass", is_staff=True
    )
    client = Client()
    client.login(username="curator", password="s3cret-pass")
    return client


def names(response) -> list[str]:
    """Returns the issue names of a grid response."""
    return [row["name"] for row in response.json()["data"]]


@pytest.mark.django_db
class TestGridContainers:
    """Shape of the JSON Tabulator consumes."""

    def test_returns_the_expected_envelope(self, staff_client, grid_dataset) -> None:
        payload = staff_client.get(GRID_URL).json()

        assert payload["total"] == 4
        assert payload["last_page"] == 1
        assert len(payload["data"]) == 4

    def test_decimals_travel_as_strings(self, staff_client, grid_dataset) -> None:
        row = staff_client.get(GRID_URL, {"q": "Alfa"}).json()["data"][0]

        assert row["mnh"] == "5.75"
        assert row["used"] == "3.50"

    def test_anonymous_callers_are_refused(self, mounted) -> None:
        response = Client().get(GRID_URL, headers={"Accept": "application/json"})

        assert response.status_code == 401


@pytest.mark.django_db
class TestPagination:
    """Server-side paging with Tabulator's `last_page` shape."""

    def test_last_page_matches_the_page_size(self, staff_client, grid_dataset) -> None:
        payload = staff_client.get(GRID_URL, {"size": 2}).json()

        assert payload["last_page"] == 2
        assert len(payload["data"]) == 2

    def test_second_page_returns_the_rest(self, staff_client, grid_dataset) -> None:
        first = names(staff_client.get(GRID_URL, {"size": 3}))
        second = names(staff_client.get(GRID_URL, {"size": 3, "page": 2}))

        assert len(first) == 3
        assert len(second) == 1
        assert set(first) | set(second) == {"Alfa", "Beta", "Gamma", "Delta"}

    def test_a_page_beyond_the_end_clamps(self, staff_client, grid_dataset) -> None:
        payload = staff_client.get(GRID_URL, {"size": 2, "page": 99}).json()

        assert payload["page"] == 2
        assert len(payload["data"]) == 2


@pytest.mark.django_db
class TestOrdering:
    """Sorting stays inside the whitelist."""

    def test_default_order_is_chronological(self, staff_client, grid_dataset) -> None:
        assert names(staff_client.get(GRID_URL)) == ["Alfa", "Delta", "Beta", "Gamma"]

    def test_sorting_by_name(self, staff_client, grid_dataset) -> None:
        response = staff_client.get(
            GRID_URL, {"sort[0][field]": "name", "sort[0][dir]": "desc"}
        )

        assert names(response) == ["Gamma", "Delta", "Beta", "Alfa"]

    def test_unknown_sort_field_falls_back_to_the_default(
        self, staff_client, grid_dataset
    ) -> None:
        response = staff_client.get(
            GRID_URL,
            {"sort[0][field]": "description; drop table", "sort[0][dir]": "asc"},
        )

        assert names(response) == ["Alfa", "Delta", "Beta", "Gamma"]


@pytest.mark.django_db
class TestFilters:
    """Each filter, and the "needs attention" selector."""

    def test_year_range(self, staff_client, grid_dataset) -> None:
        response = staff_client.get(GRID_URL, {"year_min": 1990})

        assert set(names(response)) == {"Beta", "Gamma"}

    def test_name_search(self, staff_client, grid_dataset) -> None:
        response = staff_client.get(GRID_URL, {"q": "amm"})

        assert names(response) == ["Gamma"]

    def test_country(self, staff_client, grid_dataset) -> None:
        spain = Country.objects.get(name="España")

        response = staff_client.get(GRID_URL, {"country": spain.pk})

        assert set(names(response)) == {"Alfa", "Delta"}

    def test_stamp_type(self, staff_client, grid_dataset) -> None:
        stamp_type = StampType.objects.get(name="Conmemorativo")

        response = staff_client.get(GRID_URL, {"stamp_type": stamp_type.pk})

        assert names(response) == ["Alfa"]

    @pytest.mark.parametrize(
        ("attention", "expected"),
        (
            ("no_country", {"Beta", "Gamma"}),
            ("no_date", {"Gamma"}),
            ("no_stamps", {"Gamma"}),
            ("stamps_without_colors", {"Beta", "Delta"}),
            ("stamps_without_face_value", {"Delta"}),
            ("stamps_without_image", {"Beta", "Delta"}),
        ),
    )
    def test_attention_filters(
        self, staff_client, grid_dataset, attention: str, expected: set[str]
    ) -> None:
        response = staff_client.get(GRID_URL, {"attention": attention})

        assert set(names(response)) == expected

    def test_unknown_attention_is_ignored(self, staff_client, grid_dataset) -> None:
        response = staff_client.get(GRID_URL, {"attention": "whatever"})

        assert response.json()["total"] == 4

    def test_filters_combine(self, staff_client, grid_dataset) -> None:
        spain = Country.objects.get(name="España")

        response = staff_client.get(
            GRID_URL, {"country": spain.pk, "year_min": 1980, "year_max": 1985}
        )

        assert set(names(response)) == {"Alfa", "Delta"}

    def test_no_results_is_an_empty_page(self, staff_client, grid_dataset) -> None:
        payload = staff_client.get(GRID_URL, {"q": "nothing matches this"}).json()

        assert payload["total"] == 0
        assert payload["data"] == []
        assert payload["last_page"] == 1


@pytest.mark.django_db
class TestGapBadge:
    """The badge and the "needs attention" filter tell the same story."""

    def test_badge_matches_the_no_stamps_filter(self, staff_client, grid_dataset) -> None:
        rows = staff_client.get(GRID_URL, {"attention": "no_stamps"}).json()["data"]

        assert rows
        assert all(row["gaps"]["no_stamps"] for row in rows)

    def test_badge_flags_every_gap_of_a_row(self, staff_client, grid_dataset) -> None:
        row = staff_client.get(GRID_URL, {"q": "Gamma"}).json()["data"][0]

        assert row["gaps"] == {
            "no_country": True,
            "no_date": True,
            "no_stamps": True,
        }


@pytest.mark.django_db
class TestWorkbenchPage:
    """The page ships the filters and the grid configuration."""

    def test_renders_the_grid_configuration(self, staff_client) -> None:
        response = staff_client.get(PAGE_URL)

        content = response.content.decode()
        assert response.status_code == 200
        assert "workbench-config" in content
        assert "/datadesk/grid/issues" in content

    def test_filter_values_come_from_the_url(self, staff_client) -> None:
        response = staff_client.get(
            PAGE_URL, {"attention": "no_stamps", "year_min": 1990}
        )

        content = response.content.decode()
        assert 'value="1990"' in content
        assert '<option value="no_stamps" selected>' in content

    def test_columns_are_translated_server_side(self, staff_client) -> None:
        response = staff_client.get(PAGE_URL)

        content = response.content.decode()
        config = json.loads(
            content.split('id="workbench-config" type="application/json">')[1].split(
                "</script>"
            )[0]
        )
        titles = [column["title"] for column in config["columns"]]

        assert "Year" in titles
        assert "Name" in titles

    def test_every_row_carries_the_urls_its_delete_needs(
        self, staff_client, grid_dataset
    ) -> None:
        """The grid pages on the server: the row's URLs travel with the row."""
        row = staff_client.get(GRID_URL).json()["data"][0]

        assert row["dependencies_url"] == f"/datadesk/issues/{row['id']}/dependencies"
        assert row["delete_url"] == f"/datadesk/issues/{row['id']}/delete"

    def test_the_page_carries_the_delete_dialog_and_its_texts(
        self, staff_client, grid_dataset
    ) -> None:
        response = staff_client.get(PAGE_URL)
        config = json.loads(
            response.content.decode()
            .split('id="workbench-config" type="application/json">')[1]
            .split("</script>")[0]
        )
        content = response.content.decode()

        assert 'id="delete-panel"' in content
        assert 'id="delete-confirm"' in content
        assert config["texts"]["deleteSeries"] == "Delete this series"
        assert config["texts"]["confirmYear"] == "Type %(year)s to confirm"
        assert config["texts"]["deleted"] == "The series was deleted."

    def test_every_visible_column_asks_for_a_share_of_the_width(
        self, staff_client
    ) -> None:
        """The grid fits the page instead of scrolling: the columns share it.

        ``fitColumns`` divides evenly unless every column says how much it
        wants, and an even split would leave the name as narrow as the stamp
        count. A column with one possible length (the date) may fix its width
        instead of asking for a share, but it cannot be left to chance.
        """
        response = staff_client.get(PAGE_URL)
        config = json.loads(
            response.content.decode()
            .split('id="workbench-config" type="application/json">')[1]
            .split("</script>")[0]
        )
        grows = {
            column["field"]: column.get("grow") or column.get("width")
            for column in config["columns"]
            if column["visible"]
        }

        assert all(grows.values()), grows
        assert grows["name"] > grows["stamps"]
        assert config["columns"][2]["min"] == 180


@pytest.mark.django_db
class TestFocus:
    """S15: landing back on the workbench with the saved series in view."""

    def test_without_focus_the_grid_starts_on_page_one(self, staff_client) -> None:
        response = staff_client.get(PAGE_URL)
        config = json.loads(
            response.content.decode()
            .split('id="workbench-config" type="application/json">')[1]
            .split("</script>")[0]
        )

        assert config["initialPage"] == 1
        assert config["focus"] is None

    def test_focus_resolves_the_page_the_issue_lives_on(self, staff_client, db) -> None:
        year = Year.objects.create(year=1980)
        for index in range(DEFAULT_PAGE_SIZE + 3):
            Issue.objects.create(year=year, name=f"Serie {index:04d}")

        target = Issue.objects.create(year=year, name="Serie zzz última")

        response = staff_client.get(PAGE_URL, {"focus": target.pk})
        config = json.loads(
            response.content.decode()
            .split('id="workbench-config" type="application/json">')[1]
            .split("</script>")[0]
        )

        assert config["focus"] == target.pk
        assert config["initialPage"] == 2

    def test_focus_with_an_unknown_id_stays_on_page_one(self, staff_client) -> None:
        assert page_of_issue(999_999) == 1

    def test_focus_follows_the_filters(self, staff_client, db) -> None:
        year = Year.objects.create(year=1980)
        for index in range(DEFAULT_PAGE_SIZE + 3):
            Issue.objects.create(year=year, name=f"Serie {index:04d}")

        target = Issue.objects.create(year=year, name="Serie zzz última")

        assert page_of_issue(target.pk) == 2
        assert page_of_issue(target.pk, IssueFilters(q="zzz")) == 1


@pytest.mark.django_db
class TestLookupFilters:
    """The filters that open the series behind a reference row.

    S30: a usage number with no way to see the rows it counts is a number that
    only invites the question.
    """

    def test_the_printer_filter_narrows_the_list(
        self, staff_client, grid_dataset
    ) -> None:
        printer = grid_dataset["alfa"].printer

        assert names(staff_client.get(GRID_URL, {"printer": printer.pk})) == ["Alfa"]

    def test_the_artist_filter_narrows_the_list(
        self, staff_client, grid_dataset
    ) -> None:
        artist = grid_dataset["alfa"].artist

        assert names(staff_client.get(GRID_URL, {"artist": artist.pk})) == ["Alfa"]

    def test_the_paper_filter_narrows_the_list(
        self, staff_client, grid_dataset
    ) -> None:
        paper = grid_dataset["alfa"].paper_type

        assert names(staff_client.get(GRID_URL, {"paper_type": paper.pk})) == ["Alfa"]

    def test_the_print_type_filter_narrows_the_list(
        self, staff_client, grid_dataset
    ) -> None:
        print_type = grid_dataset["alfa"].print_type

        assert (
            names(staff_client.get(GRID_URL, {"print_type": print_type.pk}))
            == ["Alfa"]
        )

    def test_the_colour_filter_is_a_semi_join_and_not_a_join(
        self, staff_client, grid_dataset
    ) -> None:
        """A stamp with two colours must not count as two stamps."""
        carmine = Color.objects.get(name="Carmín")

        payload = staff_client.get(GRID_URL, {"color": carmine.pk}).json()

        assert [row["name"] for row in payload["data"]] == ["Alfa"]
        assert payload["data"][0]["stamps"] == 1

    def test_every_filter_travels_in_the_query(self) -> None:
        filters = IssueFilters(
            printer=1,
            artist=2,
            paper_type=3,
            print_type=4,
            color=5,
        )

        assert filters.to_query() == {
            "printer": 1,
            "artist": 2,
            "paper_type": 3,
            "print_type": 4,
            "color": 5,
        }


@pytest.mark.django_db
class TestFilterChips:
    """Every filter that is on is visible, and removable on its own.

    The chips are painted by the script from the form, so what the server owes
    them is the labels and the container: the rest is one source of truth.
    """

    def test_the_page_ships_the_chip_container(self, staff_client, grid_dataset) -> None:
        content = staff_client.get(PAGE_URL).content.decode()

        assert 'id="workbench-chips"' in content

    def test_every_filter_has_a_label(self, staff_client, grid_dataset) -> None:
        labels = staff_client.get(PAGE_URL).context["config"]["filterLabels"]

        assert labels["country"] == "Country"
        assert labels["color"] == "Color"
        assert labels["attention"] == "Needs attention"
        assert labels["year_min"] == "From year"
        assert labels["q"] == "Name"

    def test_the_chip_texts_are_translated(self, staff_client, grid_dataset) -> None:
        texts = staff_client.get(PAGE_URL).context["config"]["chipsText"]

        assert texts == {
            "title": "Filters",
            "clearAll": "Clear all",
            "remove": "Remove this filter",
        }

    def test_the_page_ships_the_new_selects(self, staff_client, grid_dataset) -> None:
        content = staff_client.get(PAGE_URL).content.decode()

        for name in ("printer", "artist", "paper_type", "print_type", "color"):
            assert f'name="{name}"' in content

    def test_the_grid_is_told_which_filters_exist(
        self, staff_client, grid_dataset
    ) -> None:
        response = staff_client.get(PAGE_URL)

        assert "color" in response.context["config"]["filterNames"]


@pytest.mark.django_db
class TestTheFilterBar:
    """The five filters S30 added stay behind a disclosure.

    Seven selects on screen made the bar four rows tall, and the grid's
    pagination fell below the fold. The two the bar always had stay on screen;
    the rest open by themselves when one of them is doing the filtering.
    """

    def test_the_new_selects_live_behind_a_disclosure(
        self, staff_client, grid_dataset
    ) -> None:
        content = staff_client.get(PAGE_URL).content.decode()
        before, _, after = content.partition('class="dd-more-filters"')

        assert 'name="country"' in before
        assert 'name="stamp_type"' in before
        for name in ("printer", "artist", "paper_type", "print_type", "color"):
            assert f'name="{name}"' in after

    def test_the_disclosure_opens_when_one_of_them_is_set(
        self, staff_client, grid_dataset
    ) -> None:
        closed = staff_client.get(PAGE_URL).context["extra_filters_open"]
        opened = staff_client.get(PAGE_URL, {"printer": 1}).context[
            "extra_filters_open"
        ]

        assert closed is False
        assert opened is True


@pytest.mark.django_db
class TestTheAssetsAreStamped:
    """A browser that kept yesterday's script ran today's page.

    That is what S30 looked like from the outside: the filters were on screen
    but nothing filtered. The stamp changes with the newest DataDesk asset, so
    the URL changes with it.
    """

    def test_the_page_asks_for_a_versioned_script(
        self, staff_client, grid_dataset
    ) -> None:
        content = staff_client.get(PAGE_URL).content.decode()

        assert "datadesk/workbench.js?v=" in content
        assert "datadesk/datadesk.css?v=" in content

    def test_the_stamp_is_not_empty(self) -> None:
        from datadesk.context import asset_version

        assert asset_version() != ""


@pytest.mark.django_db
class TestTheCurrencyIsNamed:
    """The market-value columns carry their unit: the mockup showed the € and
    the grid showed a bare number."""

    def test_the_money_columns_are_marked(self, staff_client, grid_dataset) -> None:
        config = staff_client.get(PAGE_URL).context["config"]
        money = {
            column["field"]: column.get("money")
            for column in config["columns"]
            if column["field"] in ("mnh", "used")
        }

        assert money == {"mnh": True, "used": True}
