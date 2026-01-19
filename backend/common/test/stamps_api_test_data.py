import pytest
from issues_api.models import Issue
from stamps_api.models import Stamp
from colors_api.models import Color

@pytest.fixture
def stamps_table(db, issues_table, colors_table):
    """Pytest fixture for a table with two stamps."""
    stamp1 = Stamp.objects.create(
        issue=issues_table[0],
        edifil_code="E-1980-001",
        face_value="10 Ptas",
        name="Rey Juan Carlos I",
        description="Scott-1234",
        image="/static/images/stamp1.jpg",
        market_value=5.75
    )
    stamp1.colors.set([colors_table[0], colors_table[1]])

    stamp2 = Stamp.objects.create(
        issue=issues_table[1],
        edifil_code="F-1985-001",
        face_value="5 Francs",
        name="Ciclismo",
        description="Scott-5678",
        image="/static/images/stamp2.jpg",
        market_value=8.50
    )
    stamp2.colors.set([colors_table[0]])
    return [stamp1, stamp2]

@pytest.fixture
def stamp_post_payload_ok(issues_table, colors_table):
    """Pytest fixture for a valid stamp post payload."""
    return {
        'issue': issues_table[0].id, 
        'edifil_code': 'NEW-2024-001', 
        'name': 'New Stamp', 
        'colors': [colors_table[0].id],
        'face_value': '1.00'
    }

@pytest.fixture
def stamp_put_payload_ok():
    """Pytest fixture for a valid stamp put payload."""
    return {
        'name': 'Stamp Updated'
        }