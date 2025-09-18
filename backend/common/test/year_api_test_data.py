import pytest
from years_api.models import Year

@pytest.fixture
def years_table() -> list[Year]:
    return[
        Year.objects.create(
            year=2022
        ),
        Year.objects.create(
            year=2023
        )
    ]
    
@pytest.fixture
def year_post_payload_ok() -> dict:
    return{
        "year": 2024
    }
    
@pytest.fixture
def year_put_payload_ok() -> dict:
    return{
        "year": 2025
    }
    