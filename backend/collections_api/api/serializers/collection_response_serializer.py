from rest_framework import serializers
from collections_api.models import Collection

class CollectionResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Collection
        fields = ['id', 'user', 'name']