import pytest
from collections_api.models import Collection

@pytest.fixture
def collections_table(db):
    """
    Fixture to populate the database with a set of collections for testing.
    """
    test_user = "test_user"
    
    collections = [
        Collection.objects.create(name="My Stamp Collection", user=test_user),
        Collection.objects.create(name="European Stamps", user=test_user),
        Collection.objects.create(name="19th Century Stamps", user=test_user),
    ]
    return collections

@pytest.fixture
def collection_post_payload_ok():
    return {"name": "New Test Collection"}

@pytest.fixture
def collection_put_payload_ok():
    return {"name": "Updated Collection Name"}