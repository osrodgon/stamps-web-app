from rest_framework import serializers

class HealthResponseSerializer(serializers.Serializer):
    """
    Serializer for the health check response data.

    This serializer defines the structure of the data object returned by
    the health check endpoint, including the status of the overall system,
    the database, and the backend application.
    """
    status = serializers.CharField(max_length=10)
    database = serializers.CharField(max_length=128)
    backend = serializers.CharField(max_length=128)