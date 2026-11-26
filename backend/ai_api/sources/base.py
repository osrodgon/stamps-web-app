"""The contract a source adapter implements (plan step A2).

An adapter knows one source: whether it can answer for a subject, how to ask, and
how to turn the answer into `SourceObservation` rows. The adapters themselves —
Fesofi, Colnect, the price sites — arrive in A6 and A3; this step only fixes the
seam so they do not each invent their own HTTP calls.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, List, Union

if TYPE_CHECKING:  # pragma: no cover - typing only
    from ai_api.models import SourceObservation
    from issues_api.models import Issue
    from stamps_api.models import Stamp

    Subject = Union[Issue, Stamp]


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
