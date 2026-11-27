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
import zoneinfo

import jwt

from settings import DEFAULT_TIMEZONE, TIMEZONE


_CLIENT_TIMEZONE: str | None = None


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


async def _read_client_timezone() -> str | None:
    """Read the client timezone from SharedPreferences.

    Returns the IANA timezone string (e.g. ``"Europe/Madrid"``) or
    ``None`` if not found.
    """
    import flet as ft  # noqa: PLC0415

    prefs = ft.SharedPreferences()
    raw = await prefs.get(TIMEZONE)
    if raw and isinstance(raw, str):
        global _CLIENT_TIMEZONE
        _CLIENT_TIMEZONE = raw
        return raw
    return None


def get_client_timezone() -> str:
    """Return the active client timezone or the default.

    Returns:
        An IANA timezone name, falling back to ``DEFAULT_TIMEZONE``.
    """
    return _CLIENT_TIMEZONE or DEFAULT_TIMEZONE


def get_local_today() -> datetime.date:
    """Return today's date in the client's timezone.

    Returns:
        The current date in the detected client timezone (or the
        ``DEFAULT_TIMEZONE`` fallback if no client timezone is available).
    """
    tz_name: str = _CLIENT_TIMEZONE or DEFAULT_TIMEZONE
    tz = zoneinfo.ZoneInfo(tz_name)
    return datetime.datetime.now(tz).date()


def to_local_date(utc_dt: datetime.datetime, tz_name: str) -> datetime.date:
    """Convert a UTC-normalised datetime to a date in the given timezone.

    Flutter's DatePicker normalises the selected date to a UTC
    ``datetime`` before sending it to Python.  This function reverses
    that normalisation so the date matches what the user selected.

    Args:
        utc_dt: The UTC datetime to convert.
        tz_name: IANA timezone name (e.g. ``"America/New_York"``).

    Returns:
        The local date in the target timezone.
    """
    if utc_dt.tzinfo is None:
        utc_dt = utc_dt.replace(tzinfo=datetime.timezone.utc)
    return utc_dt.astimezone(zoneinfo.ZoneInfo(tz_name)).date()