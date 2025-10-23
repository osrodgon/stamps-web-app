import pytest
from issues_api.models import Issue

@pytest.fixture
def issues_table(db, years_table, countries_table, stamp_types_table, paper_types_table):
    """Pytest fixture for a table with two issues."""
    issue1 = Issue.objects.create(
        year=years_table[0],
        date="1980-05-15",
        name="Nacimiento de la monarquía",
        description="Emisión conmemorativa del inicio del reinado de Juan Carlos I.",
        total_printed=1000000,
        market_value=5.75,
        stamp_type=stamp_types_table[0],
        paper_type=paper_types_table[0],
        country=countries_table[0],
        note="Primera emisión del año",
        perforation="12.5"
    )

    issue2 = Issue.objects.create(
        year=years_table[1],
        date="1985-02-20",
        name="Juegos Olímpicos",
        description="Emisión dedicada a los Juegos Olímpicos de Los Ángeles 1984.",
        total_printed=2500000,
        market_value=8.50,
        stamp_type=stamp_types_table[1],
        paper_type=paper_types_table[1],
        country=countries_table[1],
        note="Serie completa de 4 sellos",
        perforation="13"
    )
    return [issue1, issue2]

@pytest.fixture
def issue_post_payload_ok(years_table, countries_table, stamp_types_table, paper_types_table):
    """Pytest fixture for a valid issue post payload."""
    return {
        'date': '2024-01-01',
        'name': 'New Issue 2024',
        'year': years_table[0].id,
        'country': countries_table[0].id,
        'stamp_type': stamp_types_table[0].id,
        'paper_type': paper_types_table[0].id,
    }

@pytest.fixture
def issue_put_payload_ok(years_table, countries_table):
    """Pytest fixture for a valid issue put payload."""
    return {
        'name': 'Issue Updated',
        'date': '2025-01-01',
        'year': years_table[1].id,
        'country': countries_table[1].id
        }