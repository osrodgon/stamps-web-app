"""The contract a source adapter implements (plan step A2).

An adapter knows one source: whether it can answer for a subject, how to ask, and
how to turn the answer into `SourceObservation` rows. The adapters themselves —
Fesofi, Colnect, the price sites — arrive in A6 and A3; this step only fixes the
seam so they do not each invent their own HTTP calls.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

if TYPE_CHECKING:  # pragma: no cover - typing only
    from ai_api.models import SourceObservation
    from issues_api.models import Issue
    from stamps_api.models import Stamp

    Subject = Union[Issue, Stamp]


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


class SourceAdapter(ABC):
    """One external source of prices or catalogue facts.

    Attributes:
        name: identifier of the source, the same string `SourceObservation.source`
            stores.
    """

    name: str = ""

    @abstractmethod
    def supports(self, subject: "Subject") -> bool:
        """Return True when this source can answer for the subject.

        The subject is a series or a stamp; an adapter that only prices complete
        series returns False for a stamp instead of guessing.
        """

    @abstractmethod
    def fetch(self, subject: "Subject") -> List["SourceObservation"]:
        """Ask the source and return the observations it supports.

        The rows are **not** saved: the caller decides what to keep, so a failed
        run cannot leave half a series written. An empty list means "the source
        answered and had nothing", which is a gap, not an error.
        """
