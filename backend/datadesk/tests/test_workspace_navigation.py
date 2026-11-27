"""S27 acceptance: walking the workbench list from inside a series.

The neighbour is the one in the list the user came from, filters included, and
the arrows are links: the keyboard and the mouse cannot disagree about which
series is next. These tests pin the list, the edges and the fallback.
"""

import pytest
from django.test import Client
from django.utils.formats import number_format

from datadesk.service import IssueFilters, neighbours_of_issue
from issues_api.models import Issue

PAGE_URL = "/datadesk/issues/{pk}/"
WORKBENCH_URL = "/datadesk/issues/"


@pytest.fixture
def staff_client(mounted, django_user_model) -> Client:
    """A logged-in staff client."""
    django_user_model.objects.create_user(
        username="curator", password="s3cret-pass", is_staff=True
    )
    client = Client()
    client.login(username="curator", password="s3cret-pass")
    return client


@pytest.mark.django_db
class TestTheNeighbours:
    """The list, its order and its two ends."""

    def test_the_neighbour_is_the_next_one_in_the_list(self, dataset) -> None:
        complete, no_country, no_date, no_stamps = dataset["issues"]

        middle = neighbours_of_issue(no_country.pk)

        assert middle.previous == complete.pk
        assert middle.next == no_stamps.pk
        assert middle.position == 2
        assert middle.total == 4

    def test_the_first_series_has_no_previous(self, dataset) -> None:
        complete = dataset["issues"][0]

        assert neighbours_of_issue(complete.pk).previous is None

    def test_the_last_series_has_no_next(self, dataset) -> None:
        no_date = dataset["issues"][2]

        assert neighbours_of_issue(no_date.pk).next is None

    def test_the_filters_change_the_list(self, dataset) -> None:
        """Walking the series without a country does not walk the whole table."""
        no_country = dataset["issues"][1]

        alone = neighbours_of_issue(no_country.pk, IssueFilters(attention="no_country"))

        assert alone.previous is None
        assert alone.next is None
        assert alone.total == 1

    def test_a_series_outside_the_filter_is_not_found(self, dataset) -> None:
        complete = dataset["issues"][0]

        missing = neighbours_of_issue(complete.pk, IssueFilters(attention="no_date"))

        assert missing.found is False
        assert missing.previous is None and missing.next is None


@pytest.mark.django_db
class TestTheArrowsOnThePage:
    """What the workspace renders, and the query it carries."""

    def test_the_arrows_point_at_the_neighbours(self, staff_client, dataset) -> None:
        complete, no_country, no_date, no_stamps = dataset["issues"]

        content = staff_client.get(PAGE_URL.format(pk=no_country.pk)).content.decode()

        assert f'href="{PAGE_URL.format(pk=complete.pk)}"' in content
        assert f'href="{PAGE_URL.format(pk=no_stamps.pk)}"' in content

    def test_the_counter_matches_the_list(self, staff_client, dataset) -> None:
        no_country = dataset["issues"][1]

        content = staff_client.get(PAGE_URL.format(pk=no_country.pk)).content.decode()

        assert f"{number_format(2)} / {number_format(4)}" in content

    def test_the_first_series_shows_a_dead_arrow(self, staff_client, dataset) -> None:
        complete = dataset["issues"][0]

        content = staff_client.get(PAGE_URL.format(pk=complete.pk)).content.decode()

        assert "nav-previous" not in content
        assert 'aria-disabled="true"' in content

    def test_the_filters_travel_in_the_arrows_and_the_way_back(
        self, staff_client, dataset
    ) -> None:
        no_stamps = dataset["issues"][3]

        response = staff_client.get(
            PAGE_URL.format(pk=no_stamps.pk), {"attention": "no_stamps"}
        )

        content = response.content.decode()
        assert f'href="{WORKBENCH_URL}?attention=no_stamps"' in content
        # Alone in that filter: no neighbour to walk to, and it says so.
        assert "nav-next" not in content

    def test_a_series_outside_the_filter_falls_back_to_the_whole_list(
        self, staff_client, dataset
    ) -> None:
        """A stale link should not leave the arrows dead."""
        complete = dataset["issues"][0]

        response = staff_client.get(
            PAGE_URL.format(pk=complete.pk), {"attention": "no_date"}
        )

        content = response.content.decode()
        assert "nav-next" in content or "nav-previous" in content

    def test_new_mode_has_no_arrows(self, staff_client, dataset) -> None:
        content = staff_client.get("/datadesk/issues/new/").content.decode()

        assert "nav-previous" not in content
        assert "nav-next" not in content
