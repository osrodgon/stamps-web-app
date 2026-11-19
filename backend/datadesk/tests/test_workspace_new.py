"""S11 acceptance: the dry ``mode=new`` workspace.

Nothing is written anywhere: the form is not submitted, the rows live in the
browser, and the only data that leaves the database is the country and year of
the last series. The tests check the contract the page ships — which fields are
prefilled, what the row generator is told, what ``mode=new`` hides — and the
access rules, which are the same as the rest of DataDesk.
"""
import json

import pytest
from django.test import Client
from django.utils import timezone

from artists_api.models import Artist
from colors_api.models import Color
from countries_api.models import Country
from issues_api.models import Issue
from paper_types_api.models import PaperType
from print_types_api.models import PrintType
from printers_api.models import Printer
from stamp_types_api.models import StampType
from stamps_api.models import Stamp
from years_api.models import Year

NEW_URL = "/datadesk/issues/new/"


@pytest.fixture
def series(db) -> Issue:
    """The series a new one continues: the last id, not the newest year.

    The first row created carries the later year on purpose, so ordering by
    ``-id`` and ordering by year give different answers.
    """
    spain = Country.objects.create(name="España")
    Issue.objects.create(year=Year.objects.create(year=1990), name="Vieja")
    return Issue.objects.create(
        year=Year.objects.create(year=1987), name="Última", country=spain
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


def form_values(response) -> dict:
    """Returns the values the series form was rendered with."""
    return {
        field["name"]: field["value"]
        for field in response.context["form_fields"]
        if field["value"] != ""
    }


def config_of(response) -> dict:
    """Returns the grid configuration the page ships."""
    content = response.content.decode()
    blob = content.split('id="stamp-config" type="application/json">')[1]
    return json.loads(blob.split("</script>")[0])


@pytest.mark.django_db
class TestNewSeriesPage:
    """The new-series screen is the same template in its dry mode."""

    def test_renders_for_staff(self, staff_client, series) -> None:
        response = staff_client.get(NEW_URL)

        assert response.status_code == 200
        assert response.context["mode"] == "new"

    def test_ships_no_stamp_rows(self, staff_client, series) -> None:
        config = config_of(staff_client.get(NEW_URL))

        assert config["mode"] == "new"
        assert config["data"] == []

    def test_the_counter_starts_at_zero(self, staff_client, series) -> None:
        response = staff_client.get(NEW_URL)

        assert response.context["stamp_count"] == 0

    def test_the_route_does_not_fall_into_the_detail_view(
        self, staff_client, series
    ) -> None:
        assert staff_client.get(NEW_URL).status_code == 200
        assert staff_client.get("/datadesk/issues/not-a-number/").status_code == 404

    def test_it_hides_what_only_an_existing_series_can_do(
        self, staff_client, series
    ) -> None:
        content = staff_client.get(NEW_URL).content.decode()

        assert "Clone" not in content
        assert "Delete" not in content
        assert "Use last issue" in content

    def test_it_says_what_the_shortcut_does(self, staff_client, series) -> None:
        content = staff_client.get(NEW_URL).content.decode()

        assert "Shift+Enter creates the series." in content
        assert 'id="create-button"' in content


@pytest.mark.django_db
class TestTheFormWrites:
    """S16: the screen posts what it shows, and offers the loop afterwards."""

    def test_the_create_endpoint_and_the_loop_url_are_sent(
        self, staff_client, series
    ) -> None:
        config = config_of(staff_client.get(NEW_URL))

        assert config["createUrl"] == "/datadesk/issues/create"
        assert config["newUrl"] == "/datadesk/issues/new/"

    def test_the_new_controls_are_in_the_page(self, staff_client, series) -> None:
        content = staff_client.get(NEW_URL).content.decode()

        for element in (
            "fill-series",
            "fast-row",
            "create-button",
            "create-status",
            "created-bar",
            "created-text",
            "created-open",
            "created-again",
        ):
            assert f'id="{element}"' in content, element

        assert 'id="fast-row" checked' in content
        assert 'id="created-bar" hidden' in content

    def test_the_element_ids_are_sent(self, staff_client, series) -> None:
        config = config_of(staff_client.get(NEW_URL))

        assert config["fillButton"] == "fill-series"
        assert config["fastToggle"] == "fast-row"
        assert config["createButton"] == "create-button"
        assert config["createdBar"] == "created-bar"

    def test_the_fast_row_columns_come_from_the_server(
        self, staff_client, series
    ) -> None:
        config = config_of(staff_client.get(NEW_URL))

        assert config["fastRow"] == {
            "fields": ["edifil", "fesofi", "face_value", "colors"],
            "on": True,
        }

    def test_the_colours_travel_with_their_tone(self, staff_client, series) -> None:
        Color.objects.create(name="Rojo Carmín")

        colours = config_of(staff_client.get(NEW_URL))["colours"]

        assert colours == [
            {"value": Color.objects.get().pk, "label": "Rojo Carmín", "tone": "red"}
        ]

    def test_the_texts_come_from_the_server(self, staff_client, series) -> None:
        texts = config_of(staff_client.get(NEW_URL))["texts"]

        assert set(texts) == {
            "saved",
            "rejected",
            "saving",
            "fillNeedsFirst",
            "fillImpossible",
            "createAnother",
            "rowRefused",
            "removeRow",
            "yearFromDate",
        }
        assert texts["createAnother"] == "Create another in %(year)s"
        assert "%(column)s" in texts["fillImpossible"]
        assert texts["removeRow"] == "Remove this row"

    def test_fill_series_numbers_both_catalogues(
        self, staff_client, series
    ) -> None:
        columns = config_of(staff_client.get(NEW_URL))["fillColumns"]

        assert columns == [
            {"field": "edifil", "label": "Edifil"},
            {"field": "fesofi", "label": "Fesofi"},
        ]

    def test_a_refused_field_can_be_named_in_the_users_language(
        self, staff_client, series
    ) -> None:
        labels = config_of(staff_client.get(NEW_URL))["fieldLabels"]

        assert labels["issue"]["name"] == "Name"
        assert labels["issue"]["year"] == "Year"

    def test_a_payload_shaped_like_the_form_is_created(
        self, staff_client, series
    ) -> None:
        """The browser sends the form's strings; the writer has to take them."""
        spain = series.country
        response = staff_client.post(
            "/datadesk/issues/create",
            data=json.dumps(
                {
                    "issue": {
                        "year": str(series.year.year),
                        "name": "Serie nueva",
                        "country": str(spain.pk),
                        "stamp_type": str(
                            StampType.objects.create(name="Conmemorativo").pk
                        ),
                        "perforation": "13 1/4",
                        "total_printed": "500000",
                        "market_value_mnh": "12.50",
                    },
                    "stamps": [
                        {
                            "name": "Serie nueva",
                            "face_value": "6 Pta",
                            "edifil_code": f"27{index}",
                            "colors": [
                                Color.objects.get_or_create(name="Rojo")[0].pk
                            ],
                        }
                        for index in range(3)
                    ],
                }
            ),
            content_type="application/json",
        )

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True

        created = Issue.objects.get(name="Serie nueva")
        assert created.year.year == series.year.year
        assert created.stamps.count() == 3
        assert created.stamps.first().colors.count() == 1

    def test_the_row_control_uses_the_server_bounds(self, staff_client, series) -> None:
        content = staff_client.get(NEW_URL).content.decode()

        assert 'id="row-count"' in content
        assert 'min="1"' in content
        assert 'max="100"' in content
        assert 'value="4"' in content

    def test_the_workbench_links_to_it(self, staff_client, series) -> None:
        content = staff_client.get("/datadesk/issues/").content.decode()

        assert 'href="/datadesk/issues/new/"' in content
        assert "New series" in content


@pytest.mark.django_db
class TestPrefill:
    """Only the country and the year travel from one series to the next."""

    def test_the_last_series_is_the_newest_row(self, staff_client, series) -> None:
        response = staff_client.get(NEW_URL)

        assert response.context["prefill"]["year"] == series.year.year
        assert response.context["prefill"]["country"] == {
            "value": series.country_id,
            "label": "España",
        }
        # The other row is from a later year, so "last" is the last id.
        assert Issue.objects.get(name="Vieja").year.year > series.year.year

    def test_nothing_else_is_copied(self, staff_client, series) -> None:
        prefill = staff_client.get(NEW_URL).context["prefill"]

        assert set(prefill) == {"year", "country"}

    def test_an_issue_without_country_only_prefills_the_year(
        self, staff_client, db
    ) -> None:
        Issue.objects.create(year=Year.objects.create(year=1920), name="Sin país")

        prefill = staff_client.get(NEW_URL).context["prefill"]

        assert prefill == {"year": 1920}

    def test_the_form_shows_the_prefilled_country(self, staff_client, series) -> None:
        """The field is typed: it shows the name and carries the id beside it."""
        content = staff_client.get(NEW_URL).content.decode()

        assert f'data-value="{series.country_id}"' in content
        assert 'value="España"' in content

    def test_a_fresh_database_has_nothing_to_copy(self, staff_client, db) -> None:
        response = staff_client.get(NEW_URL)

        assert response.context["prefill"] is None
        assert "Use last issue" not in response.content.decode()

    def test_the_prefill_travels_to_the_browser(self, staff_client, series) -> None:
        config = config_of(staff_client.get(NEW_URL))

        assert config["prefill"]["year"] == series.year.year
        assert config["prefill"]["country"] == {
            "value": series.country_id,
            "label": "España",
        }

    def test_every_field_of_the_series_is_in_the_form(
        self, staff_client, series
    ) -> None:
        content = staff_client.get(NEW_URL).content.decode()

        for name in (
            "year",
            "date",
            "name",
            "country",
            "stamp_type",
            "print_type",
            "printer",
            "artist",
            "paper_type",
            "perforation",
            "total_printed",
            "market_value_mnh",
            "market_value_used",
            "description",
            "note",
        ):
            assert f'id="field-{name}"' in content, name


@pytest.mark.django_db
class TestYearField:
    """The year is typed, not chosen: a series is often a new year."""

    def test_the_year_is_a_number_with_suggestions(
        self, staff_client, series
    ) -> None:
        content = staff_client.get(NEW_URL).content.decode()

        assert 'id="field-year"' in content
        assert 'type="number"' in content
        assert 'list="year-options"' in content
        assert '<select class="dd-input" id="field-year"' not in content

    def test_the_field_carries_the_number_not_the_row_id(
        self, staff_client, series
    ) -> None:
        """There is no year row to point at until the series is saved."""
        config = config_of(staff_client.get(NEW_URL))

        assert config["prefill"]["year"] == 1987
        assert config["prefill"]["year"] != series.year_id

    def test_existing_years_are_only_suggestions(self, staff_client, series) -> None:
        content = staff_client.get(NEW_URL).content.decode()

        assert '<datalist id="year-options">' in content
        assert '<option value="1987"></option>' in content
        assert '<option value="1990"></option>' in content

    def test_the_bounds_keep_typos_out(self, staff_client, series) -> None:
        content = staff_client.get(NEW_URL).content.decode()

        assert 'min="1800"' in content
        assert f'max="{timezone.now().year + 2}"' in content

    def test_the_notice_for_a_year_that_does_not_exist_ships_hidden(
        self, staff_client, series
    ) -> None:
        content = staff_client.get(NEW_URL).content.decode()

        assert 'id="year-new-hint"' in content
        assert "hidden" in content
        assert "it will be created when the series is saved" in content


@pytest.mark.django_db
class TestRowGenerator:
    """What the script is told about the rows it invents."""

    def test_the_bounds_and_the_default_are_sent(self, staff_client, series) -> None:
        config = config_of(staff_client.get(NEW_URL))

        assert config["rows"] == {"default": 4, "min": 1, "max": 100}

    def test_the_element_ids_are_sent(self, staff_client, series) -> None:
        config = config_of(staff_client.get(NEW_URL))

        assert config["nameInput"] == "field-name"
        assert config["rowsInput"] == "row-count"
        assert config["countBadge"] == "stamp-count"

    def test_the_row_prefix_cannot_collide_with_a_real_id(
        self, staff_client, series
    ) -> None:
        config = config_of(staff_client.get(NEW_URL))

        assert config["rowIdPrefix"] == "new-"
        assert not config["rowIdPrefix"].isdigit()

    def test_the_placeholder_says_there_are_no_rows_yet(
        self, staff_client, series
    ) -> None:
        config = config_of(staff_client.get(NEW_URL))

        assert config["emptyText"] == "No stamp rows yet."


@pytest.mark.django_db
class TestEditModeIsUnchanged:
    """The new mode must not leak into the read-only one."""

    def test_the_detail_page_keeps_its_mode_and_strip(
        self, staff_client, series
    ) -> None:
        response = staff_client.get(f"/datadesk/issues/{series.pk}/")
        config = config_of(response)

        assert response.context["mode"] == "edit"
        assert config["mode"] == "edit"
        assert "rows" not in config
        assert response.context["form_fields"]

    def test_the_new_series_page_has_no_change_set(self, staff_client, series) -> None:
        response = staff_client.get(NEW_URL)
        config = config_of(response)

        assert "recovery-bar" not in response.content.decode()
        assert "undo-button" not in response.content.decode()
        assert "storageKey" not in config
        assert "plurals" not in config

    def test_the_detail_page_has_no_new_series_controls(
        self, staff_client, series
    ) -> None:
        content = staff_client.get(f"/datadesk/issues/{series.pk}/").content.decode()

        for element in (
            "use-last-issue",
            "row-count",
            "fill-series",
            "fast-row",
            "create-button",
            "created-bar",
        ):
            assert f'id="{element}"' not in content, element

        assert "colours" not in config_of(
            staff_client.get(f"/datadesk/issues/{series.pk}/")
        )


@pytest.mark.django_db
class TestAccess:
    """The new series follows the same gate as the rest of DataDesk."""

    def test_anonymous_browsers_go_to_the_login(self, mounted, series) -> None:
        response = Client().get(NEW_URL)

        assert response.status_code == 302
        assert "/datadesk/login/" in response["Location"]

    def test_non_staff_users_are_refused(
        self, mounted, series, django_user_model
    ) -> None:
        django_user_model.objects.create_user(username="pepe", password="s3cret-pass")
        client = Client()
        client.login(username="pepe", password="s3cret-pass")

        assert client.get(NEW_URL).status_code == 403


@pytest.mark.django_db
class TestTheLoop:
    """`?from=<id>` is how "Create another" keeps the metadata.

    The loop is a server-rendered page, not a draft: nothing is restored from
    the browser, which is what lets S11 keep its "no drafts" rule.
    """

    @pytest.fixture
    def full_series(self, db) -> Issue:
        """A series with every field a loop could carry filled in."""
        return Issue.objects.create(
            year=Year.objects.create(year=1987),
            date="1987-05-12",
            name="Málaga",
            country=Country.objects.create(name="España"),
            stamp_type=StampType.objects.create(name="Conmemorativo"),
            print_type=PrintType.objects.create(name="Offset"),
            printer=Printer.objects.create(name="FNMT"),
            artist=Artist.objects.create(name="Anónimo"),
            paper_type=PaperType.objects.create(name="Estucado"),
            perforation="13 1/4",
            total_printed=500_000,
            market_value_mnh="12.50",
            market_value_used="3.00",
            description="Una serie",
            note="Una nota",
        )

    def test_the_classification_and_the_year_are_kept(
        self, staff_client, full_series
    ) -> None:
        prefill = form_values(staff_client.get(NEW_URL, {"from": full_series.pk}))

        assert prefill == {
            "country": full_series.country_id,
            "year": 1987,
            "stamp_type": full_series.stamp_type_id,
            "print_type": full_series.print_type_id,
            "printer": full_series.printer_id,
            "artist": full_series.artist_id,
            "paper_type": full_series.paper_type_id,
            "perforation": "13 1/4",
        }

    def test_what_identifies_the_series_is_cleared(
        self, staff_client, full_series
    ) -> None:
        """The name and date identify a series; the figures belong to its set."""
        prefill = form_values(staff_client.get(NEW_URL, {"from": full_series.pk}))

        for field in (
            "name",
            "date",
            "total_printed",
            "market_value_mnh",
            "market_value_used",
            "description",
            "note",
        ):
            assert field not in prefill, field

    def test_the_form_shows_the_repeated_values(
        self, staff_client, full_series
    ) -> None:
        content = staff_client.get(NEW_URL, {"from": full_series.pk}).content.decode()

        assert f'data-value="{full_series.country_id}"' in content
        assert 'value="13 1/4"' in content
        assert 'value="Málaga"' not in content

    def test_an_unknown_source_falls_back_to_the_last_issue(
        self, staff_client, full_series
    ) -> None:
        prefill = form_values(staff_client.get(NEW_URL, {"from": 999_999}))

        assert set(prefill) == {"year", "country"}

    def test_a_source_that_is_not_a_number_is_ignored(
        self, staff_client, full_series
    ) -> None:
        prefill = form_values(staff_client.get(NEW_URL, {"from": "abc"}))

        assert set(prefill) == {"year", "country"}

    def test_the_button_still_means_the_last_issue(
        self, staff_client, full_series
    ) -> None:
        """`?from=` fills the form; it does not redefine the prefill button."""
        config = config_of(staff_client.get(NEW_URL, {"from": full_series.pk}))

        assert set(config["prefill"]) == {"year", "country"}

    def test_the_loop_page_starts_with_empty_rows(
        self, staff_client, full_series
    ) -> None:
        config = config_of(staff_client.get(NEW_URL, {"from": full_series.pk}))

        assert config["data"] == []
        assert config["rows"]["default"] == 4


@pytest.mark.django_db
class TestTheDate:
    """The date is what decides the year, so it starts filled when it can."""

    def test_a_current_year_series_starts_dated(self, staff_client, db) -> None:
        today = timezone.localdate()
        Issue.objects.create(
            year=Year.objects.create(year=today.year), name="De este año"
        )

        values = form_values(staff_client.get(NEW_URL))

        assert values["date"] == today.isoformat()
        assert values["year"] == today.year

    def test_an_older_series_keeps_the_date_empty(self, staff_client, db) -> None:
        """Inventing a day in 1987 is worse than leaving it blank."""
        Issue.objects.create(year=Year.objects.create(year=1987), name="Antigua")

        values = form_values(staff_client.get(NEW_URL))

        assert "date" not in values
        assert values["year"] == 1987

    def test_the_loop_dates_a_current_year_series_and_not_an_older_one(
        self, staff_client, db
    ) -> None:
        today = timezone.localdate()
        current = Issue.objects.create(
            year=Year.objects.create(year=today.year), name="Reciente"
        )
        old = Issue.objects.create(year=Year.objects.create(year=1987), name="Vieja")

        assert (
            form_values(staff_client.get(NEW_URL, {"from": current.pk}))["date"]
            == today.isoformat()
        )
        assert "date" not in form_values(staff_client.get(NEW_URL, {"from": old.pk}))

    def test_the_date_field_carries_the_bounds(self, staff_client, series) -> None:
        """Typing 1700 into the date must be refused by the browser too."""
        content = staff_client.get(NEW_URL).content.decode()

        assert 'id="field-date"' in content
        assert 'min="1800-01-01"' in content
        assert f'max="{timezone.localdate().year + 2}-12-31"' in content

    def test_a_fresh_database_starts_dated(self, staff_client, db) -> None:
        values = form_values(staff_client.get(NEW_URL))

        assert values["date"] == timezone.localdate().isoformat()
