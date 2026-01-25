REQUEST_FAILED = "Request failed"

LOGIN_RESPONSE_200_SUCCESS = {
    "data": {
        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ",
        "payload": {
            "user_id": 1,
            "username": "testuser",
            "email": "test@email.com",
            "first_name": "Test",
            "last_name": "User",
            "is_admin": True,
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
        "payload": {
            "user_id": 1,
            "username": "testuser",
            "email": "test@email.com",
            "first_name": "Test",
            "last_name": "User",
            "is_admin": True,
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
SIGNUP_RESPONSE_201_SUCCESS = {
    "success": True,
    "message": "User created successfully",
    "errors": None,
    "data": {
        "id": 2,
        "username": "newuser",
        "email": "new@email.com"
    }
}

SIGNUP_RESPONSE_400_FAIL = {
    "success": False,
    "message": REQUEST_FAILED,
    "errors": [
        {
            "field": "username",
            "message": "A user with that username already exists.",
            "code": "unique"
        }
    ],
    "data": None
}
