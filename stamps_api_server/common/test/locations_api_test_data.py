import pytest

from locations_api.models import Location

@pytest.fixture
def locations_table():
    locations = [
        Location.objects.create(name="Album A"),
        Location.objects.create(name="Album B"),
    ]
    return locations

@pytest.fixture
def location_post_payload_ok():
    return {
        "name": "New Album"
    }

@pytest.fixture
def location_put_payload_ok():
    return {
        "name": "Updated Album"
    }