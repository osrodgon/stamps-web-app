import pytest
from paper_types_api.models import PaperType

@pytest.fixture
def paper_types_table():
    """
    Fixture to create a list of PaperType objects for testing.
    """
    paper_types = [
        PaperType.objects.create(name="Matte"),
        PaperType.objects.create(name="Glossy"),
        PaperType.objects.create(name="Lustre"),
    ]
    return paper_types

@pytest.fixture
def paper_type_post_payload_ok():
    """
    Fixture for a valid paper type creation payload.
    """
    return {"name": "Silk"}

@pytest.fixture
def paper_type_put_payload_ok():
    """
    Fixture for a valid paper type update payload.
    """
    return {"name": "Satin"}