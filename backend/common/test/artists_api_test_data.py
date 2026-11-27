import pytest
from artists_api.models import Artist

@pytest.fixture
def artists_table():
    """
    Fixture to create a list of Artist objects for testing.
    """
    artists = [
        Artist.objects.create(name="Artist One"),
        Artist.objects.create(name="Artist Two"),
        Artist.objects.create(name="Artist Three"),
    ]
    return artists

@pytest.fixture
def artist_post_payload_ok():
    """
    Fixture for a valid artist creation payload.
    """
    return {"name": "Artist Four"}

@pytest.fixture
def artist_put_payload_ok():
    """
    Fixture for a valid artist update payload.
    """
    return {"name": "Artist Five"}