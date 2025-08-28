import pytest
from rest_framework.test import APIClient 

# Mock APIClient
@pytest.fixture()  
def api_client() -> APIClient:   # type: ignore
    """  
    Fixture to provide an API client  
    """  
    yield APIClient()