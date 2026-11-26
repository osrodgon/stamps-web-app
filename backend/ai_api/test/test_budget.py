"""Tests for the request budget (plan step A8).

The clock is faked, so the tests are about arithmetic and not about sleeping.
"""

import pytest

from ai_api.budget import Budget, BudgetExpired


class Clock:
    """A clock that only moves when the test says so."""

    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


@pytest.fixture
def clock(monkeypatch):
    """Replace `time.monotonic` inside the budget module."""
    fake = Clock()
    monkeypatch.setattr("ai_api.budget.time.monotonic", fake)
    return fake


class TestRemaining:
    """Time left is measured from the start."""

    def test_it_starts_with_the_whole_budget(self, clock):
        budget = Budget(total=25)

        assert budget.remaining == 25
        assert budget.expired is False

    def test_it_counts_down(self, clock):
        budget = Budget(total=25)
        clock.advance(10)

        assert budget.remaining == 15
        assert budget.elapsed == 10

    def test_it_never_goes_negative(self, clock):
        budget = Budget(total=5)
        clock.advance(30)

        assert budget.remaining == 0
        assert budget.expired is True


class TestCallTimeout:
    """One call gets what is left, and only that."""

    def test_a_short_call_keeps_its_timeout(self, clock):
        budget = Budget(total=25, per_call=8)

        assert budget.timeout_for(20) == 8

    def test_the_remaining_time_caps_the_call(self, clock):
        budget = Budget(total=10, per_call=8)
        clock.advance(7)

        assert budget.timeout_for(20) == 3

    def test_an_expired_budget_refuses_to_ask(self, clock):
        budget = Budget(total=1)
        clock.advance(2)

        with pytest.raises(BudgetExpired):
            budget.timeout_for(8)
