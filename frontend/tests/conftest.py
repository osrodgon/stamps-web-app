"""Shared fixtures for frontend unit tests."""

import pytest


@pytest.fixture
def valid_email() -> str:
    """Return a valid email address for testing."""
    return "user@example.com"


@pytest.fixture
def invalid_email() -> str:
    """Return an invalid email address for testing."""
    return "invalid-email"


@pytest.fixture
def strong_password() -> str:
    """Return a password that meets all strength requirements."""
    return "SecurePass1!"


@pytest.fixture
def weak_password() -> str:
    """Return a password that fails strength requirements."""
    return "weak"
