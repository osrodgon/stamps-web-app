"""A clock for one request, so it answers instead of hanging (plan step A8).

The pipeline is a chain of network calls, and one slow source must not decide how
long the whole request takes. A `Budget` hands out the time that is left, and the
caller stops asking when there is none — a partial answer with its reasons is more
useful than a request that never returns.

A budget is a clock, not a counter: one slow page and one fast page cost the same
count and very different seconds.
"""

from __future__ import annotations

import time
from dataclasses import dataclass


class BudgetExpired(Exception):
    """Raised when there is no time left to ask another source."""


@dataclass
class Budget:
    """How much time a request may spend, measured from its start."""

    total: float = 25.0
    per_call: float = 8.0

    def __post_init__(self) -> None:
        """Start the clock."""
        self._started = time.monotonic()

    @property
    def elapsed(self) -> float:
        """Seconds spent since the budget started."""
        return time.monotonic() - self._started

    @property
    def remaining(self) -> float:
        """Seconds left, never negative."""
        return max(0.0, self.total - self.elapsed)

    @property
    def expired(self) -> bool:
        """True when there is no time left."""
        return self.remaining <= 0

    def timeout_for(self, call_timeout: float) -> float:
        """The timeout to use for one call: the call's, never more than is left.

        Raises:
            BudgetExpired: when there is no time left at all.
        """
        remaining = self.remaining
        if remaining <= 0:
            raise BudgetExpired(f"No time left in the {self.total:g}s budget.")
        return max(0.5, min(call_timeout, self.per_call, remaining))
