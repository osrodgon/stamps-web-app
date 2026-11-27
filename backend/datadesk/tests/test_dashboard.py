"""S20 acceptance: the dashboard says what is missing and opens the right grid.

The counters already existed; what this file pins is that each one has exactly
one door and that the door tells the truth. Three queues count stamps and the
workbench only filters series, so those cards carry both numbers and the pair is
checked against the same query the grid uses.
"""

import pytest
from django.conf import settings
from django.core.cache import cache
from django.test import Client
from django.utils.formats import number_format

from colors_api.models import Color
from countries_api.models import Country
from datadesk import service
from datadesk.service import (
    ATTENTION_KEYS,
    ISSUES,
    QUEUES,
    REPORT_KEYS,
    STAMPS,
    IssueFilters,
    QueueCard,
    issue_page,
)
from datadesk.views.dashboard import _number
from issues_api.models import Issue
from stamps_api.models import Stamp
from years_api.models import Year

DASHBOARD_URL = "/datadesk/"
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


@pytest.fixture
def complete(db, tmp_path, settings) -> Issue:
    """A catalogue with nothing missing, picture included."""
    pictures = tmp_path / "stamps"
    (pictures / "1987").mkdir(parents=True)
    (pictures / "1987" / "1234.webp").write_bytes(b"RIFF\x00\x00\x00\x00WEBPVP8 ")
    settings.DATADESK_STAMP_IMAGES = pictures
    cache.clear()

    issue = Issue.objects.create(
        year=Year.objects.create(year=1987),
        date="1987-05-12",
        name="Completa",
        country=Country.objects.create(name="España"),
    )
    stamp = Stamp.objects.create(
        issue=issue, name="Sello", face_value="6 Pta", fesofi_code="1234"
    )
    stamp.colors.set([Color.objects.create(name="Rojo")])
    return issue


def card_of(key: str) -> QueueCard:
    """Returns one card by its report key."""
    return {card.key: card for card in service.dashboard_queues()}[key]


def grid_total(attention: str) -> int:
    """Returns the total the workbench shows for one attention filter."""
    return issue_page(IssueFilters(attention=attention), size=1).total


@pytest.mark.django_db
class TestEveryCounterHasADoor:
    """One table of names, checked both ways."""

    def test_every_report_key_has_exactly_one_queue(self, db) -> None:
        assert sorted(queue.key for queue in QUEUES) == sorted(REPORT_KEYS)
        assert len({queue.key for queue in QUEUES}) == len(QUEUES)

    def test_every_queue_opens_a_real_workbench_filter(self, db) -> None:
        assert {queue.attention for queue in QUEUES} <= set(ATTENTION_KEYS)

    def test_the_units_are_the_two_the_page_knows(self, db) -> None:
        assert {queue.unit for queue in QUEUES} == {ISSUES, STAMPS}

    def test_the_counters_and_their_units(self, db) -> None:
        units = {queue.key: queue.unit for queue in QUEUES}

        assert units["issues_without_country"] == ISSUES
        assert units["stamps_without_image"] == STAMPS


@pytest.mark.django_db
class TestTheNumbers:
    """Each card equals a direct count, and the pair of a stamp card agrees."""

    def test_the_issue_cards_match_their_counter(self, dataset) -> None:
        report = service.missing_data_report()

        for key in (
            "issues_without_country",
            "issues_without_date",
            "issues_without_stamps",
        ):
            assert card_of(key).count == report[key]

    def test_the_stamp_cards_match_their_counter(self, dataset) -> None:
        report = service.missing_data_report()

        for key in (
            "stamps_without_colors",
            "stamps_without_face_value",
            "stamps_without_image",
        ):
            assert card_of(key).count == report[key]

    def test_an_issue_card_is_the_grid_total(self, dataset) -> None:
        for key in ("issues_without_country", "issues_without_date"):
            card = card_of(key)
            assert card.count == grid_total(card.attention)

    def test_a_stamp_card_carries_the_series_the_grid_shows(self, dataset) -> None:
        """The stamps without a picture live in the series the filter returns."""
        card = card_of("stamps_without_image")

        assert card.issues == grid_total(card.attention)
        assert card.issues == 3

    def test_an_issue_card_has_no_second_number(self, dataset) -> None:
        assert card_of("issues_without_country").issues is None

    def test_the_numbers_are_grouped_the_way_the_language_does(self, db) -> None:
        assert _number(2554) == number_format(2554, force_grouping=True)


@pytest.mark.django_db
class TestThePage:
    """The screen itself: cards, links and the empty state."""

    def test_every_card_links_to_its_filter(self, staff_client, dataset) -> None:
        content = staff_client.get(DASHBOARD_URL).content.decode()

        for queue in QUEUES:
            assert f'{WORKBENCH_URL}?attention={queue.attention}"' in content

    def test_the_cards_say_what_they_count(self, staff_client, dataset) -> None:
        content = staff_client.get(DASHBOARD_URL).content.decode()

        assert "Series with no country" in content
        assert "Stamps with no picture" in content
        assert "in 3 series" in content

    def test_the_link_opens_the_filtered_grid(self, staff_client, dataset) -> None:
        card = card_of("issues_without_country")

        response = staff_client.get(f"{WORKBENCH_URL}?attention={card.attention}")

        assert response.context["filters"].attention == card.attention

    def test_a_complete_catalogue_says_so(self, staff_client, complete) -> None:
        content = staff_client.get(DASHBOARD_URL).content.decode()

        assert "Nothing needs attention" in content
        assert "?attention=" not in content

    def test_a_complete_catalogue_still_names_the_queues(
        self, staff_client, complete
    ) -> None:
        """A finished counter is information, not a card pretending to be work."""
        content = staff_client.get(DASHBOARD_URL).content.decode()

        assert "Nothing missing here:" in content
        assert "Series with no country" in content

    def test_the_totals_are_there(self, staff_client, dataset) -> None:
        content = staff_client.get(DASHBOARD_URL).content.decode()

        assert f"{_number(4)} series" in content
        assert f"{_number(4)} stamps" in content

    def test_the_page_offers_the_way_in(self, staff_client, db) -> None:
        content = staff_client.get(DASHBOARD_URL).content.decode()

        assert f'href="{WORKBENCH_URL}"' in content
        assert 'href="/datadesk/issues/new/"' in content
        assert 'href="/datadesk/lookups/"' in content
        assert 'href="/datadesk/activity/"' in content

    def test_spanish_translates_the_cards(
        self, staff_client, dataset, settings
    ) -> None:
        staff_client.cookies[settings.LANGUAGE_COOKIE_NAME] = "es"

        content = staff_client.get(DASHBOARD_URL).content.decode()

        assert "Series sin país" in content
        assert "Sellos sin imagen" in content
        assert "en 3 series" in content

    def test_anonymous_is_sent_to_the_login(self, mounted, db) -> None:
        response = Client().get(DASHBOARD_URL)

        assert response.status_code == 302
        assert response["Location"].startswith("/datadesk/login/")
