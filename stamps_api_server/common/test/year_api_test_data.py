import pytest
from years_api.models import Year

@pytest.fixture
def years_table() -> list[Year]:
    return[
        Year.objects.create(
            year=1111
        ),
        Year.objects.create(
            year=2222
        )
    ]
    
@pytest.fixture
def year_post_payload_ok() -> dict:
    return{
        "year": 3333
    }
    
@pytest.fixture
def year_post_payload_not_ok() -> dict:
    return{
        
    }
    
@pytest.fixture
def year_put_payload_ok() -> dict:
    return{
        "year": 4444
    }
    
@pytest.fixture
def year_put_payload_not_ok() -> dict:
    return{
        
    }