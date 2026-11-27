"""The body and the answer of the bulk add of collection items (plan step C1).

One scope per request: the ids of some stamps, a series, or a year. The serializer is
strict about the key that goes with the scope — a body carrying `issue` and `ids` is a
body that does not know what it is asking for — and `GenericSerializer` keeps refusing
any field that is not in the contract.
"""

from rest_framework import serializers

from common.api.serializers.generic_serializer import GenericSerializer


class CollectionItemsBulkSerializer(GenericSerializer, serializers.Serializer):
    """The body of `POST /collections/<pk>/items/bulk/`."""

    SCOPES = ("stamp", "issue", "year")

    #: The key each scope reads, and the only one it accepts.
    KEYS = {"stamp": "ids", "issue": "issue", "year": "year"}

    scope = serializers.ChoiceField(
        choices=SCOPES,
        help_text="`stamp` for the ids in the body, `issue` for a whole series, "
        "`year` for every stamp of a year of the catalogue.",
    )
    ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=False,
        help_text="The stamps to add, when the scope is `stamp`.",
    )
    issue = serializers.IntegerField(
        required=False,
        help_text="The series whose stamps are added, when the scope is `issue`.",
    )
    year = serializers.IntegerField(
        required=False,
        help_text="The year whose stamps are added, when the scope is `year`.",
    )

    def validate(self, data: dict) -> dict:
        """Check that the body carries exactly the key its scope needs.

        Args:
            data: the validated fields.

        Returns:
            The same data, once the scope and its key agree.

        Raises:
            ValidationError: when the key of the scope is missing or another
                scope's key came along.
        """
        data = super().validate(data)
        scope = data["scope"]
        needed = self.KEYS[scope]

        present = {
            key
            for key in self.KEYS.values()
            if data.get(key) not in (None, [])
        }
        if needed not in present:
            raise serializers.ValidationError(
                {needed: f"This field is required when the scope is '{scope}'."}
            )

        for key in present - {needed}:
            raise serializers.ValidationError(
                {key: f"This field is not allowed when the scope is '{scope}'."}
            )

        return data


class CollectionItemsBulkResponseSerializer(serializers.Serializer):
    """What the bulk add answers."""

    created = serializers.IntegerField(
        help_text="How many copies were created."
    )
    skipped = serializers.IntegerField(
        help_text="How many stamps of the scope were already in the collection."
    )
    total = serializers.IntegerField(
        help_text="How many stamps the scope resolved to; created + skipped."
    )
