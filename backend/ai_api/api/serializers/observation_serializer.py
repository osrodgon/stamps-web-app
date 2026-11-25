"""Serializers for the evidence behind a valuation (plan step A1).

Three small pieces: where a price was seen (`ObservationSerializer`), what was
tried and how it went (`SourceReportSerializer`), what could not be found
(`GapSerializer`) and the aggregate built from the observations
(`ValuationSerializer`). The aggregate carries its own sample size and method so
a client can tell a figure backed by ten sales from one backed by two.
"""

from __future__ import annotations

from django.utils import timezone
from rest_framework import serializers

from ai_api.models import SourceObservation


class ObservationSerializer(serializers.Serializer):
    """One price seen in one source, with the page it can be checked against.

    The stored `raw` payload is deliberately left out of the response: it can be
    a whole scraped page, and it is for auditing, not for clients.
    """

    source = serializers.ChoiceField(
        choices=SourceObservation.Source.choices,
        help_text="Source the price was seen in.",
    )
    external_id = serializers.CharField(
        allow_blank=True,
        required=False,
        default="",
        help_text="Identifier of the item in the source, when it has one.",
    )
    url = serializers.URLField(
        allow_blank=True,
        required=False,
        default="",
        help_text="Page the price can be checked against.",
    )
    issue = serializers.IntegerField(
        allow_null=True,
        required=False,
        default=None,
        help_text="Series the observation refers to, when it is a series price.",
    )
    stamp = serializers.IntegerField(
        allow_null=True,
        required=False,
        default=None,
        help_text="Stamp the observation refers to, when it is a stamp price.",
    )
    kind = serializers.ChoiceField(
        choices=SourceObservation.Kind.choices,
        help_text="Catalogue value, asking price, sale or auction hammer.",
    )
    price = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        coerce_to_string=False,
        help_text="Amount, in `currency`.",
    )
    currency = serializers.CharField(
        max_length=3,
        required=False,
        default="EUR",
        help_text="ISO 4217 code of the amount.",
    )
    condition = serializers.ChoiceField(
        choices=SourceObservation.Condition.choices,
        required=False,
        default=SourceObservation.Condition.UNKNOWN,
        help_text="Condition of the piece the price refers to.",
    )
    observed_at = serializers.DateTimeField(
        required=False,
        default=timezone.now,
        help_text="When the price was seen, not when the sale happened.",
    )


class SourceReportSerializer(serializers.Serializer):
    """What happened with one source during the extraction."""

    source = serializers.ChoiceField(
        choices=SourceObservation.Source.choices,
        help_text="Source that was consulted.",
    )
    status = serializers.ChoiceField(
        choices=["ok", "empty", "error", "skipped"],
        help_text="Answered, answered with nothing, failed, or was not tried.",
    )
    url = serializers.URLField(
        allow_blank=True,
        required=False,
        default="",
        help_text="Page consulted, when there is a single one.",
    )
    fetched_at = serializers.DateTimeField(
        allow_null=True,
        required=False,
        default=None,
        help_text="When it was consulted.",
    )


class GapSerializer(serializers.Serializer):
    """Something that could not be filled in, and why."""

    field = serializers.CharField(
        help_text="Name of the field or block that is missing.",
    )
    reason = serializers.CharField(
        allow_blank=True,
        required=False,
        default="",
        help_text="Why it is missing, in plain words.",
    )


class ValuationSerializer(serializers.Serializer):
    """The estimate built from the observations, with its method and its sample.

    The method is a trimmed mean (the extremes are dropped) over the observations
    of the same condition, and it is written down next to the number so the
    figure can be reproduced. `sample_size` below the minimum means the estimate
    should not be trusted, which is why it travels with the number.
    """

    estimate = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        coerce_to_string=False,
        allow_null=True,
        help_text="Value the observations support, or null when they do not.",
    )
    min = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        coerce_to_string=False,
        allow_null=True,
        required=False,
        default=None,
        help_text="Lowest observation kept, or null.",
    )
    max = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        coerce_to_string=False,
        allow_null=True,
        required=False,
        default=None,
        help_text="Highest observation kept, or null.",
    )
    currency = serializers.CharField(
        max_length=3,
        required=False,
        default="EUR",
        help_text="ISO 4217 code of the estimate.",
    )
    sample_size = serializers.IntegerField(
        required=False,
        default=0,
        help_text="How many observations the estimate was built from.",
    )
    method = serializers.CharField(
        required=False,
        default="trimmed_mean",
        help_text="How the estimate was computed.",
    )
    sources = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list,
        help_text="Sources the observations came from.",
    )
    as_of = serializers.DateTimeField(
        allow_null=True,
        required=False,
        default=None,
        help_text="When the estimate was computed.",
    )
