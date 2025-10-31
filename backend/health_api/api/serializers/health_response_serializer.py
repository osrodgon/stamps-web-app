from rest_framework import serializers

class HealthResponseSerializer(serializers.Serializer):
    status = serializers.CharField(max_length=10)
    database = serializers.CharField(max_length=128)
    backend = serializers.CharField(max_length=128)