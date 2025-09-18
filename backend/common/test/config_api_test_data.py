import pytest
from config_api.models import Config

@pytest.fixture
def config_table() -> list[Config]:
    return[
        Config.objects.create(
            property="app.theme",
            value="dark"
        ),
        Config.objects.create(
            property="app.language",
            value="en"
        )
    ]
    
@pytest.fixture
def config_post_payload_ok() -> dict:
    return{
        "property": "app.version",
        "value": "1.0.0"
    }

@pytest.fixture
def config_put_payload_ok() -> dict:
    return{
        "value": "1.0.1"
    }