import pytest
from collection_items_api.models import CollectionItem
from collections_api.models import Collection
from stamps_api.models import Stamp
from issues_api.models import Issue
from colors_api.models import Color

@pytest.fixture
def collection_items_table(db, collections_table, stamps_table, issues_table, colors_table):
    """
    Fixture to populate the database with a set of collection items for testing.
    It links the first collection with the first two stamps.
    """
    items = [
        CollectionItem.objects.create(collection=collections_table[0], stamp=stamps_table[0]),
        CollectionItem.objects.create(collection=collections_table[1], stamp=stamps_table[1]),
    ]
    return items


@pytest.fixture
def collection_item_post_payload_ok(collections_table, stamps_table):
    """
    Provides a valid payload for creating a new collection item.
    Uses the second collection and the third stamp to avoid unique constraint conflicts.
    """
    return {"collection": collections_table[1].id, "stamp": stamps_table[0].id}

@pytest.fixture
def collection_item_put_payload_ok(stamps_table):
    return {
        "stamp": stamps_table[0].id
    }