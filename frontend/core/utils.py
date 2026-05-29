"""
Utility functions for input validation.

This module provides common validation functions used throughout the
application for form input validation, such as email format and
password strength checks.

Example:
    from core.utils import is_valid_email, is_strong_password

    if is_valid_email(user_email):
        # Process valid email
        pass

    if is_strong_password(user_password):
        # Password meets requirements
        pass
"""

import datetime
import re
import jwt


def is_valid_email(email: str) -> bool:
    """
    Validate an email address format.

    Checks whether the given string matches a valid email address pattern.
    The email must contain characters, followed by @, then more characters,
    a dot, and a domain extension.

    Args:
        email (str): The email address to validate.

    Returns:
        bool: True if the email format is valid, False otherwise.

    Example:
        >>> is_valid_email("user@example.com")
        True
        >>> is_valid_email("invalid-email")
        False
    """
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return re.match(pattern, email.strip()) is not None


def is_strong_password(password: str) -> bool:
    """
    Validate password strength requirements.

    Checks whether the password meets the following criteria:
    - At least 8 characters long
    - Contains at least one uppercase letter
    - Contains at least one lowercase letter
    - Contains at least one digit
    - Contains at least one special character ( _!@#$%^&*(),.?":{}|<> )

    Args:
        password (str): The password to validate.

    Returns:
        bool: True if the password meets all requirements, False otherwise.

    Example:
        >>> is_strong_password("SecurePass1!")
        True
        >>> is_strong_password("weak")
        False
    """
    pattern = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])(?=.*[_!@#$%^&*(),.?\":{}|<>]).{8,}$"
    return re.match(pattern, password) is not None

def validate_jwt_token(token: str) -> bool:
    """Check if a JWT token is still valid (not expired).

    Decodes the token without verifying the signature (client-side
    check only).  If the token has an ``exp`` claim that is past
    the current UTC time, returns ``False``.  Returns ``False`` also
    for any malformed token or decoding error.

    Args:
        token: The JWT string to validate.

    Returns:
        True if the token is present and its ``exp`` claim (if any)
        is still in the future, False otherwise.
    """
    if not token:
        return False
    try:
        payload = jwt.decode(
            token,
            options={"verify_signature": False},
            algorithms=["HS256"],
        )
        exp = payload.get("exp")
        curr = int(datetime.datetime.now(datetime.timezone.utc).timestamp())
        if exp is None:
            return True  # no expiry = treat as valid
        return  curr < exp
    except jwt.DecodeError:
        return False
    except Exception:
        return False