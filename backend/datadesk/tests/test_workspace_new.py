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

from countries_api.models import Country
from issues_api.models import Issue
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

    def test_it_says_nothing_is_saved(self, staff_client, series) -> None:
        content = staff_client.get(NEW_URL).content.decode()

        assert "Nothing is saved yet" in content
        assert "Shift+Enter does not save yet" in content

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
        assert response.context["prefill"]["country"] == series.country_id
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

    def test_the_form_marks_the_prefilled_country(self, staff_client, series) -> None:
        content = staff_client.get(NEW_URL).content.decode()

        assert f'<option value="{series.country_id}" selected>' in content

    def test_a_fresh_database_has_nothing_to_copy(self, staff_client, db) -> None:
        response = staff_client.get(NEW_URL)

        assert response.context["prefill"] is None
        assert "Use last issue" not in response.content.decode()

    def test_the_prefill_travels_to_the_browser(self, staff_client, series) -> None:
        config = config_of(staff_client.get(NEW_URL))

        assert config["prefill"]["year"] == series.year.year
        assert config["prefill"]["country"] == series.country_id

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

    def test_the_detail_page_has_no_new_series_controls(
        self, staff_client, series
    ) -> None:
        content = staff_client.get(f"/datadesk/issues/{series.pk}/").content.decode()

        assert "Use last issue" not in content
        assert 'id="row-count"' not in content


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
