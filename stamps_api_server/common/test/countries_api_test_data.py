import pytest
from countries_api.models import Country

@pytest.fixture
def countries_table(db):
    """Pytest fixture for a table with two countries."""
    country1 = Country.objects.create(name="Utopia")
    country2 = Country.objects.create(name="El Dorado")
    return [country1, country2]

@pytest.fixture
def country_post_payload_ok():
    """Pytest fixture for a valid country post payload."""
    return {'name': 'Atlantis'}

@pytest.fixture
def country_put_payload_ok():
    """Pytest fixture for a valid country put payload."""
    return {'name': 'Utopia Updated'}