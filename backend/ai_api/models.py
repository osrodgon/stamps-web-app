"""Data kept from the external sources that support a valuation (plan step A1).

A `SourceObservation` is one price seen in one place: what it is, how much, in
which condition, when it was seen and the raw payload it came from. Nothing in
here is inferred — the valuation built on top of these rows (A7) only aggregates
them, and a figure without an observation has no way of being written.
"""

from __future__ import annotations

import hashlib
from decimal import Decimal
from typing import Any

from django.db import models
from django.db.models import Q
from django.utils import timezone


class SourceObservation(models.Model):
    """One price seen in one external source, with the evidence behind it."""

    class Source(models.TextChoices):
        """Where the observation came from.

        The catalogue, the shop and the search are what the pipeline can produce;
        TodoColeccion and manual are what a stored observation may name when it was
        read from a listing or typed in. Colnect and eBay are out of the plan
        (2026-11-26) and no code produces them.
        """

        FESOFI = "fesofi", "Fesofi"
        FILATELIA = "filatelia", "Filatelia.online"
        SEARCH = "search", "Allowed-site search"
        TODOCOLECCION = "todocoleccion", "TodoColeccion"
        MANUAL = "manual", "Manual"

    class Kind(models.TextChoices):
        """What the price is, which is not the same as what it is worth."""

        CATALOG = "catalog", "Catalogue value"
        ASK = "ask", "Asking price"
        SOLD = "sold", "Sold price"
        AUCTION_HAMMER = "auction_hammer", "Auction hammer"

    class Condition(models.TextChoices):
        """Condition of the piece the price refers to."""

        MNH = "mnh", "Mint never hinged"
        MH = "mh", "Mint hinged"
        USED = "used", "Used"
        CTO = "cto", "Cancelled to order"
        UNKNOWN = "unknown", "Unknown"

    source = models.CharField(
        max_length=32,
        choices=Source.choices,
        db_index=True,
        verbose_name="source",
    )
    external_id = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="external id",
        help_text="Identifier of the item in the source, when it has one.",
    )
    url = models.URLField(
        max_length=500,
        blank=True,
        verbose_name="url",
        help_text="Page the observation can be checked against.",
    )
    issue = models.ForeignKey(
        "issues_api.Issue",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="observations",
        verbose_name="issue",
    )
    stamp = models.ForeignKey(
        "stamps_api.Stamp",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="observations",
        verbose_name="stamp",
    )
    kind = models.CharField(max_length=16, choices=Kind.choices, verbose_name="kind")
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="price",
    )
    currency = models.CharField(
        max_length=3,
        default="EUR",
        verbose_name="currency",
    )
    condition = models.CharField(
        max_length=16,
        choices=Condition.choices,
        default=Condition.UNKNOWN,
        verbose_name="condition",
    )
    observed_at = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        verbose_name="observed at",
        help_text="When this price was seen, not when the sale happened.",
    )
    raw = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="raw",
        help_text="Source payload this row was read from, for re-checking it.",
    )
    raw_hash = models.CharField(
        max_length=64,
        unique=True,
        editable=False,
        verbose_name="raw hash",
        help_text="Identity of the observation, so the same price is not stored twice.",
    )

    class Meta:
        verbose_name = "source observation"
        verbose_name_plural = "source observations"
        ordering = ["-observed_at", "-id"]
        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(stamp__isnull=False, issue__isnull=True)
                    | Q(stamp__isnull=True, issue__isnull=False)
                ),
                name="ai_api_observation_exactly_one_subject",
            )
        ]

    def __str__(self) -> str:
        """Return the source, the price and the subject, for logs and admin."""
        subject = (
            f"stamp {self.stamp_id}" if self.stamp_id else f"issue {self.issue_id}"
        )
        return f"{self.source} {self.kind} {self.price} {self.currency} ({subject})"

    def build_hash(self) -> str:
        """Return the stable identity of this observation.

        The subject and the payload's facts are in, the timestamp is not: seeing
        the same item at the same price twice must not create a second row, while
        a different price must be kept as history.
        """
        subject = (
            f"stamp:{self.stamp_id}" if self.stamp_id else f"issue:{self.issue_id}"
        )
        price = Decimal(self.price).quantize(Decimal("0.01"))
        parts = [
            str(self.source),
            str(self.external_id or ""),
            subject,
            str(self.kind),
            str(self.condition),
            str(price),
            str(self.currency),
        ]
        return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Store the observation, computing its identity when it is missing."""
        if not self.raw_hash:
            self.raw_hash = self.build_hash()
        super().save(*args, **kwargs)
