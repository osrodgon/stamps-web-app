import pytest
from collection_items_api.models import CollectionItem
from datetime import date

@pytest.fixture
def collection_items_table(db, collections_table, stamps_table, locations_table, condition_types_table):
    """
    Fixture to populate the database with a set of collection items for testing.
    It links the first collection with the first two stamps.
    """
    items = [
        CollectionItem.objects.create(
            collection=collections_table[0], 
            stamp=stamps_table[0], 
            location=locations_table[0],
            condition_type=condition_types_table[0],
            price_paid="1.50",
            acquisition_date=date(2023, 10, 1),
            note="First day cover."
        ),
        CollectionItem.objects.create(
            collection=collections_table[1], 
            stamp=stamps_table[1], 
            location=locations_table[1],
            condition_type=condition_types_table[1],
            price_paid="2.00",
            acquisition_date=date(2024, 1, 15)
        ),
    ]
    return items


@pytest.fixture
def collection_item_post_payload_ok(collections_table, stamps_table, locations_table, condition_types_table):
    """
    Provides a valid payload for creating a new collection item.
    Uses the second collection and the third stamp to avoid unique constraint conflicts.
    """
    return {
        "collection": collections_table[1].id, 
        "stamp": stamps_table[1].id, 
        "location": locations_table[0].id,
        "condition_type": condition_types_table[0].id,
        "price_paid": "3.50",
        "acquisition_date": "2024-02-20",
        "note": "New item note.",
        "quantity": 2
    }

@pytest.fixture
def collection_item_put_payload_ok():
    return {"price_paid": "1.75", "note": "Updated note about condition."}