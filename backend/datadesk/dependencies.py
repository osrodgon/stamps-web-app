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
