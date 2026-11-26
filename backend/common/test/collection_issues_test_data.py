"""Fixtures for the series of a collection (plan step B1).

Two series of the first collection with their figures, a third the user holds nothing
of (it must not appear) and a fourth whose only stamp has no picture code.
"""

from datetime import date

import pytest

from collection_items_api.models import CollectionItem
from issues_api.models import Issue
from stamps_api.models import Stamp
from years_api.models import Year


@pytest.fixture
def collection_issues_catalogue(db, users_table, collections_table):
    """A small catalogue where the three figures of a series are different."""
    year = Year.objects.create(year=1900)

    first = Issue.objects.create(
        year=year, name="First series", date=date(1900, 1, 1)
    )
    second = Issue.objects.create(
        year=year, name="Second series", date=date(1900, 2, 1)
    )
    nobody_has = Issue.objects.create(
        year=year, name="Nobody has this", date=date(1900, 3, 1)
    )
    aardvark = Issue.objects.create(
        year=year, name="Aardvark", date=date(1900, 4, 1)
    )
    no_picture = Issue.objects.create(
        year=year, name="No picture", date=date(1900, 5, 1)
    )

    a1 = Stamp.objects.create(
        issue=first,
        name="A1",
        face_value="1",
        fesofi_code="F-A1",
        market_value_mnh="10.00",
    )
    a2 = Stamp.objects.create(
        issue=first,
        name="A2",
        face_value="1",
        fesofi_code=None,
        market_value_mnh="20.00",
    )
    b1 = Stamp.objects.create(
        issue=second,
        name="B1",
        face_value="1",
        fesofi_code="F-B1",
        market_value_mnh="5.00",
    )
    z1 = Stamp.objects.create(
        issue=aardvark,
        name="Z1",
        face_value="1",
        fesofi_code="F-Z1",
        market_value_mnh="2.00",
    )
    n1 = Stamp.objects.create(
        issue=no_picture,
        name="N1",
        face_value="1",
        fesofi_code=None,
        market_value_mnh=None,
    )
    Stamp.objects.create(
        issue=nobody_has, name="C1", face_value="1", fesofi_code="F-C1"
    )

    collection = collections_table[0]
    CollectionItem.objects.create(
        collection=collection, stamp=a1, price_paid="7.50", quantity=2
    )
    CollectionItem.objects.create(
        collection=collection, stamp=a2, price_paid="2.50"
    )
    CollectionItem.objects.create(
        collection=collection, stamp=b1, price_paid="1.00"
    )
    CollectionItem.objects.create(
        collection=collection, stamp=z1, price_paid="0.50"
    )
    CollectionItem.objects.create(
        collection=collection, stamp=n1, price_paid=None
    )

    return {
        "collection": collection,
        "user": users_table[0],
        "year": year.year,
        "first": first,
        "second": second,
        "aardvark": aardvark,
        "no_picture": no_picture,
        "nobody_has": nobody_has,
    }
