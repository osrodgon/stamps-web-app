import re
from rest_framework import serializers

class ResearchResponseSerializer(serializers.Serializer):
    """
    Serializer for AI research response data.

    This serializer formats the AI research results for client-facing responses,
    following the exact structure required for stamp series research.
    """
    confidence_score = serializers.IntegerField(
        min_value=0,
        max_value=100,
        help_text="Confidence score of the research (0-100)"
    )
    confidence_score_reasons = serializers.ListField(
        child=serializers.CharField(),
        help_text="List of reasons for the confidence score"
    )
    description = serializers.CharField(
        allow_blank=True,
        help_text="Historical description or 'n/a'"
    )
    issue_date = serializers.DateField(
        allow_null=True,
        help_text="Issue date in YYYY-MM-DD format or null"
    )
    artist = serializers.CharField(
        allow_blank=True,
        help_text="Artist/engraver name or 'n/a'"
    )
    printer = serializers.CharField(
        allow_blank=True,
        help_text="Printer name or 'n/a'"
    )
    print_type = serializers.CharField(
        allow_blank=True,
        help_text="Printing technique or 'n/a'"
    )
    perforation = serializers.CharField(
        allow_blank=True,
        help_text="Perforation measurement or 'n/a'"
    )
    paper_type = serializers.CharField(
        allow_blank=True,
        help_text="Paper type or 'n/a'"
    )
    stamp_type = serializers.CharField(
        allow_blank=True,
        help_text="Format: Sello, Hoja Bloque, Carné... or 'n/a'"
    )
    notes = serializers.CharField(
        allow_blank=True,
        help_text="Relevant notes or 'n/a'"
    )
    total_printed = serializers.IntegerField(
        allow_null=True,
        help_text="Total printed quantity or null"
    )
    market_value_mnh = serializers.FloatField(
        allow_null=True,
        help_text="Market value in mint condition (float or null)"
    )
    market_value_used = serializers.FloatField(
        allow_null=True,
        help_text="Market value in used condition (float or null)"
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
        
        return representation
        
    class Meta:
        fields = [
            'confidence_score',
            'confidence_score_reasons',
            'description',
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
            'stamps'
        ]