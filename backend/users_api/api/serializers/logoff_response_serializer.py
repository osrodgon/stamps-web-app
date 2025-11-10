from rest_framework import serializers

class LogoffResponseSerializer(serializers.Serializer):
    """
    Serializer for the logoff response.

    This serializer defines the structure of the data returned upon a successful logoff.
    """
    message = serializers.CharField(help_text="A message indicating the result of the logoff attempt.")