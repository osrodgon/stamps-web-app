import pytest

from print_types_api.models import PrintType

@pytest.fixture
def print_types_table():
    print_types = [
        PrintType.objects.create(name="Glossy"),
        PrintType.objects.create(name="Matte"),
    ]
    return print_types

@pytest.fixture
def print_type_post_payload_ok():
    return {"name": "Canvas"}

@pytest.fixture
def print_type_put_payload_ok():
    return {"name": "Updated Print Type"}