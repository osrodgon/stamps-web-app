REQUEST_FAILED = "Request failed"

LOGIN_RESPONSE_200_SUCCESS = {
    "data": {
        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ",
        "user": {
            "id": 1,
            "username": "testuser",
            "email": "test@email.com",
            "first_name": "Test",
            "last_name": "User",
            "registration_date": "2025-12-02T21:32:04.607Z",
            "is_active": True
        }
    },
    "success": True,
    "errors": None,
    "message": "Login successful"
}

LOGIN_RESPONSE_200_SUCCESS_MISSING_TOKEN = {
    "data": {
        "token": None,
        "user": {
            "id": 1,
            "username": "testuser",
            "email": "test@email.com",
            "first_name": "Test",
            "last_name": "User",
            "registration_date": "2025-12-02T21:32:04.607Z",
            "is_active": True
        }
    },
    "success": True,
    "errors": None,
    "message": "Login successful"
}

LOGIN_RESPONSE_400_BAD_REQUEST = {
    "success": False,
    "message": REQUEST_FAILED,
    "errors": [
        {
        "field": "password",
        "message": "This field is required.",
        "code": "required"
        }
    ],
    "data": None
}

LOGIN_RESPONSE_401_UNAUTHORIZED = {
    "success": False,
    "message": REQUEST_FAILED,
    "errors": [
        {
        "field": None,
        "message": "Login failed username and/or password do not match.",
        "code": "other"
        }
    ],
    "data": None
}

LOGIN_RESPONSE_500_SERVER_ERROR = {
    "success": False,
    "message": REQUEST_FAILED,
    "errors": [
        {
        "field": 'detail',
        "message": "Database connection lost.",
        "code": "connection_lost"
        }
    ],
    "data": None
}