import pytest

from paper_types_api.models import PaperType

@pytest.fixture
def paper_types_table():
    paper_types = [
        PaperType.objects.create(name="Glossy"),
        PaperType.objects.create(name="Matte"),
    ]
    return paper_types

@pytest.fixture
def paper_type_post_payload_ok():
    return {"name": "Canvas"}

@pytest.fixture
def paper_type_put_payload_ok():
    return {"name": "Updated Paper Type"}