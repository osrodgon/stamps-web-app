"""Turning observations into one number, and saying how (plan step A7).

The estimate is a **trimmed mean**: the lowest and the highest price are dropped
when there are enough of them, because one optimistic seller or one rare
cancellation must not move what a stamp is worth. Below three observations there
is no estimate — a number built on one asking price is worse than no number,
because it looks like information.

Nothing here invents, converts or discounts: it averages what the sources said,
in the currency they said it, and tells the caller how thin the evidence is.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import Iterable, List, Optional

from ai_api.sources.base import Observation


MINIMUM_SAMPLE = 3

# Below this many observations the extremes are not dropped: with three prices,
# throwing two away leaves one, which is not an average.
TRIM_FROM = 4


@dataclass(frozen=True)
class Estimate:
    """What the observations support, with the evidence that supports it."""

    estimate: Optional[Decimal] = None
    minimum: Optional[Decimal] = None
    maximum: Optional[Decimal] = None
    currency: str = "EUR"
    sample_size: int = 0
    method: str = "trimmed_mean"
    sources: List[str] = field(default_factory=list)
    as_of: Optional[datetime] = None
    gap: Optional[str] = None

    @property
    def found(self) -> bool:
        """True when there is a number to show."""
        return self.estimate is not None


def value(
    observations: Iterable[Observation],
    condition: Optional[str] = None,
    currency: str = "EUR",
    minimum_sample: int = MINIMUM_SAMPLE,
) -> Estimate:
    """Estimate the value of one condition from the observations available.

    Args:
        observations: every price the sources returned, of any condition.
        condition: when given, only observations of that condition are averaged.
        currency: only prices already in this currency are used; no rate is
            invented to convert the rest.
        minimum_sample: how many prices are needed before answering.

    Returns:
        An `Estimate`, with `gap` written when there is no answer.
    """
    prices: List[Decimal] = []
    sources: List[str] = []
    other_currency = 0

    for observation in observations:
        if condition is not None and observation.condition != condition:
            continue
        if observation.currency.upper() != currency:
            other_currency += 1
            continue
        prices.append(Decimal(observation.price))
        if observation.source not in sources:
            sources.append(observation.source)

    if other_currency:
        # Mixed currencies are not averaged together, and no rate is invented to
        # convert them: the euros still make an estimate, the rest is said.
        noted = (
            f" {other_currency} price(s) in another currency were left out; no "
            f"rate is invented to convert them."
        )
    else:
        noted = ""

    if len(prices) < minimum_sample:
        where = f" in {condition}" if condition else ""
        return Estimate(
            sample_size=len(prices),
            sources=sorted(sources),
            gap=(
                f"{len(prices)} price(s){where}; at least {minimum_sample} are "
                f"needed to estimate.{noted}"
            ),
        )

    kept = sorted(prices)
    if len(kept) >= TRIM_FROM:
        kept = kept[1:-1]

    total = sum(kept)
    average = (total / len(kept)).quantize(Decimal("0.01"))

    return Estimate(
        estimate=average,
        minimum=min(prices),
        maximum=max(prices),
        currency=currency,
        sample_size=len(prices),
        sources=sorted(sources),
        as_of=datetime.now(timezone.utc),
        gap=noted.strip() or None,
    )
