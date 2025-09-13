import pytest
from colors_api.models import Color

@pytest.fixture
def colors_table():
    """
    Fixture to create a list of Color objects for testing.
    """
    colors = [
        Color.objects.create(name="Red"),
        Color.objects.create(name="Green"),
        Color.objects.create(name="Blue"),
    ]
    return colors

@pytest.fixture
def color_post_payload_ok():
    """
    Fixture for a valid color creation payload.
    """
    return {"name": "Yellow"}

@pytest.fixture
def color_put_payload_ok():
    """
    Fixture for a valid color update payload.
    """
    return {"name": "Orange"}