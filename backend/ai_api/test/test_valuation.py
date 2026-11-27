"""Tests for the valuation (plan step A7).

Pure arithmetic over observations: no network, no database, no model.
"""

from datetime import datetime
from decimal import Decimal

import pytest

from ai_api.sources.base import Observation
from ai_api.valuation import MINIMUM_SAMPLE, TRIM_FROM, value


def observation(price, condition="used", currency="EUR", source="filatelia"):
    """One price, with the defaults most tests want."""
    return Observation(
        source=source,
        price=Decimal(str(price)),
        condition=condition,
        currency=currency,
        url="https://filatelia.online/tienda/sello/",
        observed_at=datetime(2026, 11, 26),
    )


class TestSample:
    """Below three prices there is no estimate, and it says why."""

    def test_no_observations_is_a_gap(self):
        estimate = value([])

        assert estimate.estimate is None
        assert estimate.sample_size == 0
        assert "at least" in estimate.gap

    def test_two_prices_are_not_enough(self):
        estimate = value([observation(10), observation(12)])

        assert estimate.estimate is None
        assert estimate.sample_size == 2
        assert "at least" in estimate.gap

    def test_three_prices_are_enough(self):
        estimate = value([observation(10), observation(12), observation(14)])

        assert estimate.estimate == Decimal("12.00")
        assert estimate.sample_size == 3
        assert estimate.gap is None


class TestTrimmedMean:
    """The extremes do not move the estimate."""

    def test_the_highest_and_lowest_are_dropped(self):
        prices = [observation(1), observation(10), observation(12), observation(14)]

        # 1 and 14 go; 10 and 12 stay.
        assert value(prices).estimate == Decimal("11.00")

    def test_an_outlier_does_not_move_it(self):
        normal = [observation(p) for p in (10, 11, 12)]
        with_outlier = normal + [observation(500)]

        # The 500 and the 10 go; the plain mean would have been 133.25.
        assert value(with_outlier).estimate == Decimal("11.50")

    def test_the_range_travels_with_the_estimate(self):
        estimate = value([observation(p) for p in (10, 11, 12)])

        assert estimate.minimum == Decimal("10")
        assert estimate.maximum == Decimal("12")


class TestConditions:
    """Mint never becomes used, or the other way round."""

    def test_only_the_asked_condition_is_averaged(self):
        prices = [
            observation(10, condition="used"),
            observation(12, condition="used"),
            observation(14, condition="used"),
            observation(100, condition="mnh"),
        ]

        assert value(prices, condition="used").estimate == Decimal("12.00")

    def test_a_condition_with_few_prices_is_a_gap(self):
        prices = [observation(10, condition="used"), observation(100, condition="mnh")]

        estimate = value(prices, condition="mnh")

        assert estimate.estimate is None
        assert "in mnh" in estimate.gap

    def test_all_conditions_together_when_none_asked(self):
        prices = [
            observation(10, condition="used"),
            observation(12, condition="used"),
            observation(14, condition="mnh"),
        ]

        assert value(prices).estimate == Decimal("12.00")


class TestCurrencies:
    """No rate is invented."""

    def test_another_currency_is_left_out(self):
        prices = [
            observation(10),
            observation(12),
            observation(14),
            observation(100, currency="GBP"),
        ]

        estimate = value(prices)

        assert estimate.estimate == Decimal("12.00")
        assert estimate.sample_size == 3
        assert "GBP" not in (estimate.gap or "")
        assert "another currency" in (estimate.gap or "")

    def test_only_another_currency_is_a_gap(self):
        estimate = value([observation(10, currency="GBP")])

        assert estimate.estimate is None
        assert "at least" in estimate.gap


class TestEvidence:
    """The estimate says who said it and how much of it there is."""

    def test_the_sources_are_listed_once(self):
        prices = [
            observation(10, source="filatelia"),
            observation(12, source="filatelia"),
            observation(14, source="search"),
        ]

        assert value(prices).sources == ["filatelia", "search"]

    def test_it_says_when_it_was_computed(self):
        estimate = value([observation(p) for p in (10, 11, 12)])

        assert estimate.as_of is not None
        assert estimate.method == "trimmed_mean"


class TestConstants:
    """The numbers the rules are written with are the ones documented."""

    def test_minimum_sample_is_three(self):
        assert MINIMUM_SAMPLE == 3

    def test_trimming_needs_four(self):
        assert TRIM_FROM == 4
