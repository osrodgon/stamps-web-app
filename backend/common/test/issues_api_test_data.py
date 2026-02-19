import pytest
from issues_api.models import Issue

@pytest.fixture
def issues_table(db, years_table, countries_table, stamp_types_table, print_types_table):
    """Pytest fixture for a table with two issues."""
    issue1 = Issue.objects.create(
        year=years_table[0],
        date="1980-05-15",
        name="Nacimiento de la monarquía",
        description="Emisión conmemorativa del inicio del reinado de Juan Carlos I.",
        total_printed=1000000,
        market_value_mnh=5.75,
        stamp_type=stamp_types_table[0],
        print_type=print_types_table[0],
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
        market_value_mnh=8.50,
        stamp_type=stamp_types_table[1],
        print_type=print_types_table[1],
        country=countries_table[1],
        note="Serie completa de 4 sellos",
        perforation="13"
    )
    return [issue1, issue2]

@pytest.fixture
def issue_post_payload_ok(years_table, countries_table, stamp_types_table, print_types_table):
    """Pytest fixture for a valid issue post payload."""
    return {
        'date': '2024-01-01',
        'name': 'New Issue 2024',
        'year': years_table[0].id,
        'country': countries_table[0].id,
        'stamp_type': stamp_types_table[0].id,
        'print_type': print_types_table[0].id,
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

@pytest.fixture
def issue_collection_post_payload_ok():
    """Pytest fixture for a valid issue collection post payload."""
    return {
        'issue_name': 'Olimpiadas Barcelona 1992',
        'description': 'Emisión conmemorativa de los Juegos Olímpicos de Barcelona 1992',
        'issue_date': '1992-07-25',
        'artist': 'Juan García López',
        'printer': 'Fábrica Nacional de Moneda y Timbre',
        'print_type': 'Offset',
        'perforation': '13',
        'paper_type': 'Estucado',
        'stamp_type': 'Definitiva',
        'notes': 'Serie completa de 6 sellos',
        'total_printed': 5000000,
        'market_value_mnh': 12.50,
        'market_value_used': 8.75,
        'stamps': [
            {
                'edifil_code': '1234',
                'fesofi_code': 'F1234',
                'motive': 'Atleta de 100 metros',
                'face_value': '0.10',
                'color': 'rojo',
                'amount_printed': 1000000,
                'market_value_mnh': 15.00,
                'market_value_used': 10.50,
                'description': 'Sello con atleta en posición de salida'
            },
            {
                'edifil_code': '1235',
                'fesofi_code': 'F1235',
                'motive': 'Nadador',
                'face_value': '0.25',
                'color': 'azul, verde',
                'amount_printed': 800000,
                'market_value_mnh': 18.00,
                'market_value_used': 12.60,
                'description': 'Sello con nadador en estilo libre'
            },
            {
                'edifil_code': '1236',
                'fesofi_code': 'F1236',
                'motive': 'Gimnasta',
                'face_value': '0.50',
                'color': 'rojo, amarillo y azul',
                'amount_printed': 600000,
                'market_value_mnh': 22.00,
                'market_value_used': 15.40,
                'description': 'Sello con gimnasta en barra de equilibrio'
            }
        ]
    }

@pytest.fixture
def issue_collection_post_payload_minimal():
    """Pytest fixture for a minimal valid issue collection post payload."""
    return {
        'issue_name': 'Emisión Minimal',
        'issue_date': '2024-01-01',
        'stamps': [
            {
                'edifil_code': 'MIN001',
                'fesofi_code': 'FMIN001',
                'motive': 'Sello Minimal',
                'face_value': '0.05'
            }
        ]
    }

@pytest.fixture
def issue_collection_post_payload_with_defaults():
    """Pytest fixture for issue collection payload using default values."""
    return {
        'issue_name': 'Emisión con Valores por Defecto',
        'issue_date': '2024-06-15',
        'artist': 'n/a',
        'printer': 'n/a',
        'print_type': 'n/a',
        'perforation': 'n/a',
        'paper_type': 'n/a',
        'stamp_type': 'n/a',
        'notes': 'n/a',
        'total_printed': 0,
        'market_value_mnh': 0,
        'market_value_used': 0,
        'stamps': [
            {
                'edifil_code': 'DEF001',
                'fesofi_code': 'FDEF001',
                'motive': 'Sello con Valores por Defecto',
                'face_value': '0.10',
                'color': 'n/a',
                'amount_printed': 0,
                'market_value_mnh': 0,
                'market_value_used': 0,
                'description': 'n/a'
            }
        ]
    }

@pytest.fixture
def issue_collection_post_payload_invalid_required():
    """Pytest fixture for issue collection payload missing required fields."""
    return {
        'description': 'Emisión sin nombre',
        'issue_date': '2024-01-01',
        'stamps': [
            {
                'edifil_code': 'INV001',
                'fesofi_code': 'FINV001',
                'motive': 'Sello Inválido',
                'face_value': '0.10'
            }
        ]
    }

@pytest.fixture
def issue_collection_post_payload_invalid_negative():
    """Pytest fixture for issue collection payload with negative values."""
    return {
        'issue_name': 'Emisión con Valores Negativos',
        'issue_date': '2024-01-01',
        'total_printed': -1000,
        'market_value_mnh': -5.50,
        'market_value_used': -3.25,
        'stamps': [
            {
                'edifil_code': 'NEG001',
                'fesofi_code': 'FNEG001',
                'motive': 'Sello con Valores Negativos',
                'face_value': '0.10',
                'amount_printed': -500,
                'market_value_mnh': -2.00,
                'market_value_used': -1.50
            }
        ]
    }
