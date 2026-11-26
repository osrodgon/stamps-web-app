"""Fixtures for the collections overview counters (plan step A2).

Two owned stamps, one of them with a picture code and one without, plus a stamp of
the same series the user does not own: that is the smallest data set where
`series`, `stamps` and `total` are three different numbers.

The series and the stamps are created here instead of reusing the generic fixtures:
the counter test needs its own catalogue (two series of two stamps each), and
borrowing the shared one would tie these numbers to data that other tests change.
"""

import pytest

from collection_items_api.models import CollectionItem
from issues_api.models import Issue
from stamps_api.models import Stamp
from years_api.models import Year


@pytest.fixture
def overview_catalogue(db, users_table, collections_table):
    """The first collection of the first user, with counters that differ.

    - `owned` (with a picture code) and `owned_without_code` are in different
      series, so `series` is 2 and `stamps` is 2.
    - `not_owned` is another stamp of the first series, so `total` is 4.
    - `owned` carries `quantity = 2`: copies do not count twice.
    """
    year = Year.objects.create(year=1888)
    first = Issue.objects.create(year=year, name="First series")
    second = Issue.objects.create(year=year, name="Second series")

    owned = Stamp.objects.create(
        issue=first, name="Owned", face_value="1", fesofi_code="F-OWNED"
    )
    not_owned = Stamp.objects.create(
        issue=first, name="Not owned", face_value="2", fesofi_code="F-NOT-OWNED"
    )
    owned_without_code = Stamp.objects.create(
        issue=second, name="No picture", face_value="3", fesofi_code=None
    )
    other = Stamp.objects.create(
        issue=second, name="Other", face_value="4", fesofi_code="F-OTHER"
    )

    collection = collections_table[0]
    CollectionItem.objects.create(collection=collection, stamp=owned, quantity=2)
    CollectionItem.objects.create(collection=collection, stamp=owned_without_code)

    return {
        "collection": collection,
        "user": users_table[0],
        "first_issue": first,
        "owned": owned,
        "not_owned": not_owned,
        "owned_without_code": owned_without_code,
        "other": other,
        "year": year.year,
    }
