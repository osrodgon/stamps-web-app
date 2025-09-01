import pytest
from config_api.models import Config

@pytest.fixture
def config_table() -> list[Config]:
    return[
        Config.objects.create(
            property="property1",
            value="value 1"
        ),
        Config.objects.create(
            property="property2",
            value="value 2"
        )
    ]
    
@pytest.fixture
def config_post_payload_ok() -> dict:
    return{
        "property": "property3",
        "value": "value 3"
    }

@pytest.fixture
def config_put_payload_ok() -> dict:
    return{
        "value": "value 4"
    }