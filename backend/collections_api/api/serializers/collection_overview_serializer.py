"""The shape of one card of the collections overview (plan step A2).

It is not the `Collection` row: the card carries what the collection holds, not who
owns it, because the token already says that. The counters and the covers come from
`CollectionOverviewService`, which is why this serializer declares fields instead of
wrapping the model.
"""

from rest_framework import serializers


class CollectionCoverSerializer(serializers.Serializer):
    """One stamp of the collage: the year and the code that name its picture."""

    year = serializers.IntegerField(
        help_text="Emission year of the stamp, half of the picture's path."
    )
    code = serializers.CharField(
        help_text="Fesofi code of the stamp, the file name of the picture."
    )


class CollectionOverviewSerializer(serializers.Serializer):
    """A collection as the overview card reads it."""

    id = serializers.IntegerField(help_text="The collection's id.")
    name = serializers.CharField(help_text="The collection's name.")
    series = serializers.IntegerField(
        help_text="How many distinct series the user holds something from."
    )
    stamps = serializers.IntegerField(
        help_text="How many distinct stamps the user owns; copies do not count twice."
    )
    total = serializers.IntegerField(
        help_text="How many stamps those series have: the progress bar's denominator."
    )
    covers = CollectionCoverSerializer(
        many=True,
        help_text="Up to twelve stamps with a picture code, in a stable order.",
    )
