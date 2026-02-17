# Test data for AI Manager API testing (No Database)
from typing import Dict, Any

import pytest

@pytest.fixture
def series_extraction_request_payload_ok() -> Dict[str, Any]:
    """Valid research request payload for testing."""
    return {
        "name": "Castillos",
        "date": "2007-09-10"
    }

# @pytest.fixture
# def series_extraction_request_payload_minimal() -> Dict[str, Any]:
#     """Minimal valid research request payload (optional field omitted)."""
#     return {
#         "issue_name": "Navidad",
#         "issue_date": "1978-12-22"
#     }

@pytest.fixture
def series_extraction_request_payload_invalid() -> Dict[str, Any]:
    """Invalid research request payload for testing validation."""
    return {
        "name": "",  # Empty required field
        "date": "invalid-date",  # Invalid date format
    }

@pytest.fixture
def series_extraction_response_data() -> Dict[str, Any]:
    """Mock AI service response data for testing."""
    return {
        "issue_name": "Castillos",
        "description": "Castillos de España series",
        "issue_date": "2007-09-10",
        "artist": "José Luis López",
        "printer": "FNMT",
        "print_type": "Offset",
        "perforation": "13 1/4 x 13",
        "paper_type": "Glossy",
        "stamp_type": "Sello",
        "notes": "Special commemorative series",
        "total_printed": 100000,
        "market_value_mnh": 15.50,
        "market_value_used": 8.75,
        "stamps": [
            {
                "edifil_code": "4349",
                "face_value": "5 PTA",
                "description": "Alcázar de Segovia",
                "amount_printed": 50000,
                "color": "Red",
                "market_value_mnh": 2.50,
                "market_value_used": 1.25
            }
        ]
    }
    
@pytest.fixture
def series_extraction_cleaned_data() -> Dict[str, Any]:
    """Mock scraper service cleaned data for testing."""
    return {
        "serie_info": {
            "título serie": "Castillos",
            "fecha de emisión": "2007-09-10"
        },
    }
    