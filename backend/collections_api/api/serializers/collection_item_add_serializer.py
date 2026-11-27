"""Adding a copy of a catalogue stamp to a collection (plan step B2).

The collection comes from the URL, so the body carries only the stamp. The stamp is an
id and the view resolves it: a stamp that does not exist is a 404, not a validation
error, because it is not the payload that is wrong — the catalogue has no such stamp.
"""

from rest_framework import serializers

from common.api.serializers.generic_serializer import GenericSerializer


class CollectionItemAddSerializer(GenericSerializer, serializers.Serializer):
    """The body of `POST /collections/<pk>/items/`."""

    stamp = serializers.IntegerField(
        help_text="Id of the catalogue stamp to add to the collection."
    )
