"""Tests for the pricing backfill command (plan step A8).

The sources are stubbed: the command's job is walking the catalogue, storing what
comes back and not storing it twice, not talking to the shops.
"""

from decimal import Decimal

import pytest
from django.core.management import call_command

from ai_api.models import SourceObservation
from ai_api.sources.base import Observation
from issues_api.models import Issue
from stamps_api.models import Stamp
from years_api.models import Year


pytestmark = pytest.mark.django_db


@pytest.fixture
def catalogue():
    """One 2007 issue with two coded stamps and one without a code."""
    year, _ = Year.objects.get_or_create(year=2007)
    issue = Issue.objects.create(year=year, name="Castillos")

    Stamp.objects.create(issue=issue, name="Almenar", face_value="2,49", edifil_code="4349")
    Stamp.objects.create(issue=issue, name="Villena", face_value="2,49", edifil_code="4350")
    Stamp.objects.create(issue=issue, name="Sin código", face_value="2,49")
    return issue


def observation(code: str, price: str, condition: str = "mnh") -> Observation:
    """One price, as a source would return it."""
    return Observation(
        source="filatelia",
        price=Decimal(price),
        condition=condition,
        url=f"https://filatelia.online/tienda/{code}/",
        subject_code=code,
    )


class TestDryRun:
    """A dry run asks and reports, and writes nothing."""

    def test_nothing_is_stored(self, catalogue, mocker):
        shop = mocker.patch(
            "ai_api.management.commands.ai_prices_backfill.FilateliaCatalogue"
        )
        shop.return_value.prices.return_value = [observation("4349", "10.00")]

        call_command("ai_prices_backfill", "--dry-run", "--source", "filatelia")

        assert SourceObservation.objects.count() == 0

    def test_it_still_asks(self, catalogue, mocker):
        shop = mocker.patch(
            "ai_api.management.commands.ai_prices_backfill.FilateliaCatalogue"
        )
        shop.return_value.prices.return_value = [observation("4349", "10.00")]

        call_command("ai_prices_backfill", "--dry-run", "--source", "filatelia")

        assert shop.return_value.prices.call_count == 2  # two coded stamps


class TestStoring:
    """What comes back is stored against the stamp it prices."""

    def test_the_observations_are_saved(self, catalogue, mocker):
        shop = mocker.patch(
            "ai_api.management.commands.ai_prices_backfill.FilateliaCatalogue"
        )
        shop.return_value.prices.side_effect = lambda code, year="", timeout=None: [
            observation(code, "10.00"),
            observation(code, "12.00", condition="used"),
        ]

        call_command("ai_prices_backfill", "--source", "filatelia")

        rows = SourceObservation.objects.all()
        assert rows.count() == 4  # two prices for each of the two coded stamps
        assert {row.stamp.edifil_code for row in rows} == {"4349", "4350"}
        assert {row.condition for row in rows} == {"mnh", "used"}

    def test_a_stamp_without_a_code_is_skipped(self, catalogue, mocker):
        shop = mocker.patch(
            "ai_api.management.commands.ai_prices_backfill.FilateliaCatalogue"
        )
        shop.return_value.prices.side_effect = lambda code, year="", timeout=None: [
            observation(code, "10.00")
        ]

        call_command("ai_prices_backfill", "--source", "filatelia")

        assert "Sin código" not in {row.stamp.name for row in SourceObservation.objects.all()}

    def test_running_it_twice_does_not_duplicate(self, catalogue, mocker):
        shop = mocker.patch(
            "ai_api.management.commands.ai_prices_backfill.FilateliaCatalogue"
        )
        shop.return_value.prices.side_effect = lambda code, year="", timeout=None: [
            observation(code, "10.00")
        ]

        call_command("ai_prices_backfill", "--source", "filatelia")
        call_command("ai_prices_backfill", "--source", "filatelia")

        assert SourceObservation.objects.count() == 2

    def test_a_failing_source_does_not_stop_the_run(self, catalogue, mocker):
        shop = mocker.patch(
            "ai_api.management.commands.ai_prices_backfill.FilateliaCatalogue"
        )
        shop.return_value.prices.side_effect = RuntimeError("down")

        call_command("ai_prices_backfill", "--source", "filatelia")

        assert SourceObservation.objects.count() == 0


class TestSelection:
    """The flags narrow what is walked."""

    def test_only_walks_the_issue_asked(self, catalogue, mocker):
        year, _ = Year.objects.get_or_create(year=2008)
        other = Issue.objects.create(year=year, name="Otro")
        Stamp.objects.create(issue=other, name="X", face_value="1", edifil_code="9999")

        shop = mocker.patch(
            "ai_api.management.commands.ai_prices_backfill.FilateliaCatalogue"
        )
        seen = []
        shop.return_value.prices.side_effect = (
            lambda code, year="", timeout=None: seen.append(code) or []
        )

        call_command("ai_prices_backfill", "--source", "filatelia", "--only", str(catalogue.id))

        assert "9999" not in seen
        assert seen == ["4349", "4350"]

    def test_the_stamp_cap_is_respected(self, catalogue, mocker):
        shop = mocker.patch(
            "ai_api.management.commands.ai_prices_backfill.FilateliaCatalogue"
        )
        shop.return_value.prices.return_value = []

        call_command("ai_prices_backfill", "--source", "filatelia", "--stamps", "1")

        assert shop.return_value.prices.call_count == 1
