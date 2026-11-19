"""What a deletion takes with it.

Deleting a series cascades twice: its stamps go, and every ``CollectionItem``
pointing at one of those stamps goes too. Those items belong to users'
collections, not to the catalogue, and DataDesk cannot put them back — S21's
revert restores the series and its stamps, never who had them. That is why a
deletion is preceded by a number instead of a sentence: "3 collection items in 2
collections" is a decision, "are you sure?" is not.
"""

from dataclasses import dataclass

from django.db.models import Count
from django.utils.translation import gettext_lazy as _

from collection_items_api.models import CollectionItem
from issues_api.models import Issue
from stamps_api.models import Stamp


@dataclass(frozen=True)
class Dependencies:
    """How much a series drags with it when it is deleted.

    Attributes:
        stamps: Stamps of the series (the series' own rows).
        items: ``CollectionItem`` rows pointing at one of those stamps.
        collections: User collections those items belong to.
    """

    stamps: int
    items: int
    collections: int

    @property
    def collected(self) -> bool:
        """Whether a user collection holds any of the stamps."""
        return self.items > 0

    def as_dict(self) -> dict[str, int]:
        """Returns the three counts in the shape the page reads them."""
        return {
            "stamps": self.stamps,
            "items": self.items,
            "collections": self.collections,
        }


def series_dependencies(issue: Issue) -> Dependencies:
    """Counts the stamps, collection items and collections of one series.

    Two queries: the stamps of the series and one aggregate over the junction
    table. ``distinct`` is what turns items into collections — the same
    collection usually holds several stamps of a series, and counting rows would
    report one collection three times.
    """
    totals = CollectionItem.objects.filter(stamp__issue=issue).aggregate(
        items=Count("pk"), collections=Count("collection_id", distinct=True)
    )
    return Dependencies(
        stamps=issue.stamps.count(),
        items=totals["items"],
        collections=totals["collections"],
    )


def dependency_warning(dependencies: Dependencies) -> str:
    """Returns the sentence shown above the numbers.

    Three cases, three different decisions: nothing to delete, a series nobody
    collected, or stamps sitting in somebody's albums. The counts are not written
    into the sentence — they are listed next to it — so no plural rule lives
    here.
    """
    if dependencies.stamps == 0:
        return str(_("This series has no stamps."))
    if not dependencies.collected:
        return str(_("No user collection holds these stamps."))
    return str(_("These stamps are in user collections, which lose them too."))


@dataclass(frozen=True)
class StampDependencies:
    """What deleting one stamp takes with it.

    Attributes:
        items: ``CollectionItem`` rows pointing at the stamp.
        collections: User collections those items belong to.
        siblings: Other stamps of the same series, so the dialog can warn when
            this is the last one.
    """

    items: int
    collections: int
    siblings: int

    @property
    def collected(self) -> bool:
        """Whether a user collection holds the stamp."""
        return self.items > 0

    @property
    def last_of_series(self) -> bool:
        """Whether the series is left with no stamps at all."""
        return self.siblings == 0

    def as_dict(self) -> dict[str, int]:
        """Returns the counts in the shape the page reads them."""
        return {
            "items": self.items,
            "collections": self.collections,
            "siblings": self.siblings,
        }


def stamp_dependencies(stamp: Stamp) -> StampDependencies:
    """Counts the collection items of one stamp and its siblings.

    Two queries: the aggregate over the junction table and a count of the other
    stamps of the series. The second one is not bookkeeping: deleting the last
    stamp leaves a series with no stamps, which is a state the dashboard reports
    as a gap, so the dialog has to say it out loud.
    """
    totals = CollectionItem.objects.filter(stamp=stamp).aggregate(
        items=Count("pk"), collections=Count("collection_id", distinct=True)
    )
    siblings = (
        Stamp.objects.filter(issue_id=stamp.issue_id).exclude(pk=stamp.pk).count()
    )
    return StampDependencies(
        items=totals["items"],
        collections=totals["collections"],
        siblings=siblings,
    )


def stamp_warning(dependencies: StampDependencies) -> str:
    """Returns the sentence the stamp dialog shows above the numbers.

    Four cases, and the two axes are independent: whether anybody holds the
    stamp, and whether it is the last of its series. The counts are listed next
    to the sentence, so nothing plural is written into it.
    """
    if dependencies.last_of_series and dependencies.collected:
        return str(_("It is the last stamp of the series, and its collections go too."))
    if dependencies.last_of_series:
        return str(_("It is the last stamp of the series: the series is left empty."))
    if dependencies.collected:
        return str(_("This stamp is in user collections, which lose it too."))
    return str(_("No user collection holds this stamp."))
