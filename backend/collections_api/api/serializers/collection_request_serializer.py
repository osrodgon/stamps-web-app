from rest_framework import serializers
from common.api.serializers.generic_serializer import GenericSerializer
from collections_api.models import Collection
from users_api.models import UserCollection

class CollectionRequestSerializer(GenericSerializer, serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=UserCollection.objects.all(), required=False)
    api_key_name = serializers.CharField(required=False)
    
    class Meta:
        model = Collection
        fields = ['user', 'name','api_key_name']
        read_only_fields = ['user']
        