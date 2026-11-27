"""Prices from `filatelia.online` (plan step A7).

A Spanish shop on the same store software as Fesofi, and the only structured price
source left after Colnect: its products carry `Nº Edifil`, `Estado` (condition) and
`Año`, so a code resolves to the asking prices of the stamps it has in stock.

What it gives is an **asking price**, never a sale, and only for the stock it has
that day. That is why an observation says `kind: "ask"` and why the valuation needs
three of them before answering.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional

from ai_api.sources.base import Observation
from ai_api.sources.store import StoreCatalogue
from ai_api.text import condition_of


# The shop's attributes, by id (they are fixed once the store is installed).
EDIFIL_ATTRIBUTE = 45
CONDITION_ATTRIBUTE = 12
YEAR_ATTRIBUTE = 2
EDIFIL_TAXONOMY = "pa_sello-numeracion"
YEAR_TAXONOMY = "pa_sello-ano"

class FilateliaCatalogue(StoreCatalogue):
    """Read the asking prices one shop has for a catalogue code."""

    name = "filatelia"
    root = "https://filatelia.online/wp-json/wc/store/v1"

    def prices(
        self, edifil: str, year: str = "", timeout: Optional[float] = None
    ) -> List[Observation]:
        """Return the prices the shop asks for one Edifil code.

        Args:
            edifil: the catalogue code, e.g. "2867". Empty or unknown is no answer.
            year: the emission year, used as a filter when the code was reused.
            timeout: seconds this call may take, when the caller has a budget.

        Returns:
            One observation per product with a price. An empty list means the shop
            does not stock it, which is a gap, not an error.
        """
        code = (edifil or "").strip()
        if not code:
            return []

        term_id = self._term_id(EDIFIL_ATTRIBUTE, code, timeout)
        if term_id is None:
            self.log.debug(f"{self.name}: no term for edifil {code}")
            return []

        filters = []
        if year:
            year_term = self._term_id(YEAR_ATTRIBUTE, year, timeout)
            if year_term is not None:
                filters.append((YEAR_TAXONOMY, year_term))

        term = {
            "id": term_id,
            "name": code,
            "taxonomy": EDIFIL_TAXONOMY,
            "attribute": EDIFIL_ATTRIBUTE,
        }
        products = self._products(term, filters or None, timeout)

        observations = []
        for product in products:
            price = self._price(product)
            if price is None:
                # A product without a price is not a price of zero.
                continue
            observations.append(self._observation(product, code, price))

        self.log.debug(f"{self.name}: {len(observations)} price(s) for {code}")
        return observations

    def _observation(self, product: dict, code: str, price: float) -> Observation:
        """Turn one product into an observation, condition included."""
        attributes = self._attributes(product)
        return Observation(
            source=self.name,
            price=Decimal(str(price)).quantize(Decimal("0.01")),
            kind="ask",
            currency=self._currency(product),
            condition=self.condition_of(attributes.get(self._normalise("Estado"))),
            url=product.get("permalink") or "",
            external_id=str(product.get("id") or ""),
            subject_code=code,
            observed_at=datetime.now(timezone.utc),
            raw={
                "name": product.get("name"),
                "estado": attributes.get(self._normalise("Estado")),
                "year": attributes.get(self._normalise("Año")),
            },
        )

    @staticmethod
    def condition_of(text: Optional[str]) -> str:
        """Map the shop's wording to the conditions the API speaks."""
        return condition_of(text)
