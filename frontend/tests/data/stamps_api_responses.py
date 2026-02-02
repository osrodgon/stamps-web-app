"""
Test data for StampsService API responses.
"""

# Years API response
YEARS_RESPONSE_200_SUCCESS = {
    "success": True,
    "data": [
        {"year": 1850},
        {"year": 1851},
        {"year": 1852},
        {"year": 1950},
        {"year": 1951},
        {"year": 2020},
        {"year": 2021},
        {"year": 2022},
        {"year": 2023},
        {"year": 2024}
    ]
}

# Issues API response
ISSUES_RESPONSE_200_SUCCESS = {
    "success": True,
    "data": [
        {
            "id": 1,
            "country": "Spain",
            "date": "1950-01-01",
            "name": "Test Series 1",
            "perforation": "12.5",
            "stamp_type": "Definitive",
            "print_type": "Lithography",
            "total_printed": 100000,
            "market_value": 25.50,
            "description": "Test description",
            "note": "Test note"
        },
        {
            "id": 2,
            "country": "France",
            "date": "1951-03-15",
            "name": "Test Series 2",
            "perforation": "14",
            "stamp_type": "Commemorative",
            "print_type": "Engraving",
            "total_printed": 50000,
            "market_value": 15.75,
            "description": "Another test description",
            "note": "Another test note"
        }
    ]
}

# Print Types API response
PRINT_TYPES_RESPONSE_200_SUCCESS = {
    "success": True,
    "data": [
        {"name": "Lithography"},
        {"name": "Engraving"},
        {"name": "Photogravure"},
        {"name": "Offset"},
        {"name": "Letterpress"}
    ]
}

# Stamp Types API response
STAMP_TYPES_RESPONSE_200_SUCCESS = {
    "success": True,
    "data": [
        {"name": "Definitive"},
        {"name": "Commemorative"},
        {"name": "Postage Due"},
        {"name": "Airmail"},
        {"name": "Revenue"}
    ]
}

# Stamps API response
STAMPS_RESPONSE_200_SUCCESS = {
    "success": True,
    "data": [
        {
            "id": 101,
            "issue_id": 1,
            "name": "Stamp 1",
            "edifil_code": "1234",
            "face_value": "0.05",
            "market_value": 12.50,
            "colors": ["Red", "Blue"],
            "image": "stamps/101.jpg"
        },
        {
            "id": 102,
            "issue_id": 1,
            "name": "Stamp 2",
            "edifil_code": "1235",
            "face_value": "0.10",
            "market_value": 8.25,
            "colors": ["Green"],
            "image": "stamps/102.jpg"
        },
        {
            "id": 103,
            "issue_id": 1,
            "name": "Stamp 3",
            "edifil_code": "1236",
            "face_value": "0.25",
            "market_value": 25.00,
            "colors": ["Purple", "Yellow"],
            "image": "stamps/103.jpg"
        }
    ]
}