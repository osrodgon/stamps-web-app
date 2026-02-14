from rest_framework import serializers


class StampDetailSerializer(serializers.Serializer):
    """
    Serializer for individual stamp details within the series extraction response.
    """
    edifil_code = serializers.CharField(
        allow_blank=True,
        help_text="Edifil catalog code or 'n/a'"
    )
    face_value = serializers.CharField(
        allow_blank=True,
        help_text="Exact face value (e.g., '5 PTA')"
    )
    description = serializers.CharField(
        allow_blank=True,
        help_text="Design/motive description or 'n/a'"
    )
    amount_printed = serializers.IntegerField(
        allow_null=True,
        help_text="Individual stamp print run or null"
    )
    color = serializers.CharField(
        allow_blank=True,
        help_text="Color or 'n/a'"
    )
    market_value_mnh = serializers.FloatField(
        allow_null=True,
        help_text="Market value mint condition (float or null)"
    )
    market_value_used = serializers.FloatField(
        allow_null=True,
        help_text="Market value used condition (float or null)"
    )
    
    class Meta:
        fields = [
            'edifil_code',
            'face_value',
            'description',
            'amount_printed',
            'color',
            'market_value_mnh',
            'market_value_used'
        ]
