import pytest
from rest_framework.test import APIClient

# Mock APIClient
@pytest.fixture()  
def api_client() -> APIClient:   # type: ignore    
    yield APIClient()
