import pytest
from collections_api.models import Collection

@pytest.fixture
def collections_table(db, users_table):
    """
    Fixture to populate the database with a set of collections for testing.
    """
    test_user = "test_user"
    
    collections = [
        Collection.objects.create(name="My Stamp Collection", api_key_name=test_user, user=users_table[0]),
        Collection.objects.create(name="European Stamps", api_key_name=test_user, user=users_table[1]),
        Collection.objects.create(name="19th Century Stamps", api_key_name=test_user, user=users_table[0]),
    ]
    return collections

@pytest.fixture
def collection_post_payload_ok():
    return {"name": "New Test Collection"}

@pytest.fixture
def collection_put_payload_ok():
    return {"name": "Updated Collection Name"}