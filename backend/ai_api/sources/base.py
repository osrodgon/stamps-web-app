"""What a source hands the pipeline: one price with its evidence (plan step A2).

The sources themselves are `fesofi.py` (identity and catalogue facts),
`filatelia.py` (shop prices) and `search_prices.py` (allowed-site search). They do
not share a base class — they answer different questions — but they all speak
`Observation`, which is the shape the response and `SourceObservation` store.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class Observation:
    """One price seen in one place, with the page behind it.

    It is the same information `SourceObservation` stores, kept free of Django so
    it can be produced, priced and tested without a database. The model is what
    persists it once there is a `Stamp` or an `Issue` to attach it to.
    """

    source: str
    price: Decimal
    kind: str = "ask"
    currency: str = "EUR"
    condition: str = "unknown"
    url: str = ""
    external_id: str = ""
    subject_code: str = ""
    observed_at: Optional[datetime] = None
    raw: Dict[str, Any] = field(default_factory=dict)
