import pytest

from stamp_types_api.models import StampType

@pytest.fixture
def stamp_types_table():
    stamp_types_list = [
        StampType.objects.create(name='Definitive'),
        StampType.objects.create(name='Commemorative'),
        StampType.objects.create(name='Special')
    ]
    return stamp_types_list

@pytest.fixture
def stamp_type_post_payload_ok():
    return {
        "name": "Postage Due"
    }

@pytest.fixture
def stamp_type_put_payload_ok():
    return {
        "name": "Revenue"
    }
