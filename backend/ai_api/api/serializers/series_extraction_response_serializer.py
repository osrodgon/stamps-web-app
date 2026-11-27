from rest_framework import serializers

from ai_api.api.serializers.observation_serializer import (
    GapSerializer,
    ObservationSerializer,
    SourceReportSerializer,
    ValuationSerializer,
)


class SeriesExtractionResponseSerializer(serializers.Serializer):
    """
    Serializer for AI series extraction response data.

    Two kinds of content live here, and they are not worth the same. The
    catalogue fields are what a source said; the valuations are what those
    sources' prices add up to, and they travel with their observations so a
    client can check them. A price no observation backs is null, not an
    estimate: the prompt no longer asks the model for numbers (plan step A1).
    """
    issue_name = serializers.CharField(
        allow_blank=True,
        help_text="Name of the issue"
    )
    description = serializers.CharField(
        allow_blank=True,
        help_text="Historical description or 'n/a'"
    )
    description_source = serializers.ChoiceField(
        choices=["llm", "fesofi", "manual"],
        required=False,
        default="llm",
        help_text="Where the description text comes from. 'llm' means the model "
                  "wrote it from the catalogue facts and must not be read as a "
                  "catalogue quote."
    )
    issue_date = serializers.DateField(
        allow_null=True,
        help_text="Issue date in YYYY-MM-DD format or null"
    )
    artist = serializers.CharField(
        allow_blank=True,
        allow_null=True,
        help_text="Artist/engraver name or 'n/a'"
    )
    printer = serializers.CharField(
        allow_blank=True,
        allow_null=True,
        help_text="Printer name or 'n/a'"
    )
    print_type = serializers.CharField(
        allow_blank=True,
        allow_null=True,
        help_text="Printing technique or 'n/a'"
    )
    perforation = serializers.CharField(
        allow_blank=True,
        allow_null=True,
        help_text="Perforation measurement or 'n/a'"
    )
    paper_type = serializers.CharField(
        allow_blank=True,
        allow_null=True,
        help_text="Paper type or 'n/a'"
    )
    stamp_type = serializers.CharField(
        allow_blank=True,
        allow_null=True,
        help_text="Format: Sello, Hoja Bloque, Carné... or 'n/a'"
    )
    notes = serializers.CharField(
        allow_blank=True,
        allow_null=True,
        help_text="Relevant notes or 'n/a'"
    )
    total_printed = serializers.IntegerField(
        allow_null=True,
        help_text="Total printed quantity or null"
    )
    market_value_mnh = serializers.FloatField(
        allow_null=True,
        required=False,
        default=None,
        help_text="Deprecated: kept for shape compatibility. Only a valuation "
                  "built from observations may fill it (A7); the endpoint "
                  "returns null until then."
    )
    market_value_used = serializers.FloatField(
        allow_null=True,
        required=False,
        default=None,
        help_text="Deprecated: see market_value_mnh."
    )
    sources = SourceReportSerializer(
        many=True,
        required=False,
        default=list,
        help_text="Sources consulted and what each one answered."
    )
    observations = ObservationSerializer(
        many=True,
        required=False,
        default=list,
        help_text="Prices found, each with the page that supports it."
    )
    valuation = ValuationSerializer(
        required=False,
        allow_null=True,
        default=None,
        help_text="Estimate built from the observations, or null when there "
                  "are not enough."
    )
    partial = serializers.BooleanField(
        required=False,
        default=False,
        help_text="True when the request ran out of budget and returned what it had."
    )
    gaps = GapSerializer(
        many=True,
        required=False,
        default=list,
        help_text="What could not be found, and why."
    )
    stamps = serializers.ListField(
        child=serializers.DictField(),
        help_text="List of individual stamp details"
    )

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        fields_to_check = [
            'description', 'artist', 'printer', 'print_type',
            'perforation', 'paper_type', 'stamp_type', 'notes'
        ]

        for field in fields_to_check:
            if field in representation and representation[field] is None:
                representation[field] = "n/a"

        # Every stamp description is written by the model too, so it carries the
        # same label the series text does.
        for stamp in representation.get('stamps') or []:
            if isinstance(stamp, dict):
                stamp.setdefault('description_source', 'llm')

        return representation

    class Meta:
        fields = [
            'issue_name',
            'description',
            'description_source',
            'issue_date',
            'artist',
            'printer',
            'print_type',
            'perforation',
            'paper_type',
            'stamp_type',
            'notes',
            'total_printed',
            'market_value_mnh',
            'market_value_used',
            'sources',
            'observations',
            'valuation',
            'partial',
            'gaps',
            'stamps'
        ]
