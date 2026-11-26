from rest_framework import serializers

from common.api.serializers.generic_serializer import GenericSerializer
from collection_items_api.models import CollectionItem


class CollectionItemsUpdateSerializer(GenericSerializer, serializers.ModelSerializer):
    """Updates the fields that describe the user's own copy of a stamp.

    This is the write half of "Your copy" (plan step A1). `collection` and
    `stamp` are deliberately absent: they identify the row, so letting a request
    change them would be a way to move an item into somebody else's collection.
    `GenericSerializer` rejects any field not listed here, which is what makes the
    whitelist real instead of a convention.

    All six fields are optional because an item can be saved with only some of
    them filled in; the view updates partially.
    """

    class Meta:
        model = CollectionItem
        fields = [
            'condition_type',
            'quantity',
            'price_paid',
            'acquisition_date',
            'location',
            'note',
        ]
