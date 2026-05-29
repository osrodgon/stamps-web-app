"""Unit tests for core/utils.py — pure validation functions."""

import datetime
import zoneinfo
from unittest.mock import AsyncMock, MagicMock, patch

from core.utils import (
    get_client_timezone,
    get_local_today,
    is_strong_password,
    is_valid_email,
    to_local_date,
)


class TestIsValidEmail:
    """Tests for the is_valid_email validation function."""

    def test_valid_standard_email(self) -> None:
        assert is_valid_email("user@example.com") is True

    def test_valid_email_with_dots(self) -> None:
        assert is_valid_email("first.last@example.com") is True

    def test_valid_email_with_plus(self) -> None:
        assert is_valid_email("user+tag@example.com") is True

    def test_valid_email_with_underscores(self) -> None:
        assert is_valid_email("user_name@example.com") is True

    def test_valid_email_with_hyphens_in_domain(self) -> None:
        assert is_valid_email("user@my-domain.com") is True

    def test_valid_email_with_subdomain(self) -> None:
        assert is_valid_email("user@mail.example.com") is True

    def test_valid_email_with_numbers(self) -> None:
        assert is_valid_email("user123@example456.com") is True

    def test_valid_email_with_whitespace_stripped(self) -> None:
        assert is_valid_email("  user@example.com  ") is True

    def test_invalid_missing_at_symbol(self) -> None:
        assert is_valid_email("userexample.com") is False

    def test_invalid_missing_domain(self) -> None:
        assert is_valid_email("user@") is False

    def test_invalid_missing_local_part(self) -> None:
        assert is_valid_email("@example.com") is False

    def test_invalid_missing_tld(self) -> None:
        assert is_valid_email("user@example") is False

    def test_invalid_empty_string(self) -> None:
        assert is_valid_email("") is False

    def test_invalid_spaces_only(self) -> None:
        assert is_valid_email("   ") is False

    def test_invalid_multiple_at_symbols(self) -> None:
        assert is_valid_email("user@@example.com") is False


class TestIsStrongPassword:
    """Tests for the is_strong_password validation function."""

    def test_valid_password(self) -> None:
        assert is_strong_password("SecurePass1!") is True

    def test_valid_password_with_special_char_at(self) -> None:
        assert is_strong_password("TestPass1@") is True

    def test_valid_password_with_special_char_hash(self) -> None:
        assert is_strong_password("TestPass1#") is True

    def test_valid_password_with_underscore(self) -> None:
        assert is_strong_password("TestPass1_") is True

    def test_invalid_too_short(self) -> None:
        assert is_strong_password("Ab1!") is False

    def test_invalid_exactly_7_chars(self) -> None:
        assert is_strong_password("Ab1!xyz") is False

    def test_invalid_no_uppercase(self) -> None:
        assert is_strong_password("securepass1!") is False

    def test_invalid_no_lowercase(self) -> None:
        assert is_strong_password("SECUREPASS1!") is False

    def test_invalid_no_digit(self) -> None:
        assert is_strong_password("SecurePass!") is False

    def test_invalid_no_special_char(self) -> None:
        assert is_strong_password("SecurePass1") is False

    def test_invalid_empty_string(self) -> None:
        assert is_strong_password("") is False

    def test_invalid_all_spaces(self) -> None:
        assert is_strong_password("        ") is False

    def test_valid_minimum_length(self) -> None:
        assert is_strong_password("Abcdefg1!") is True

    def test_valid_long_password(self) -> None:
        assert is_strong_password("VeryLongAndSecurePassword123!") is True


class TestReadClientTimezone:
    """Tests for the _read_client_timezone function."""

    async def test_sets_client_timezone_from_prefs(self) -> None:
        from core import utils
        utils._CLIENT_TIMEZONE = None
        mock_prefs = MagicMock()
        mock_prefs.get = AsyncMock(return_value="America/New_York")
        with patch("flet.SharedPreferences", return_value=mock_prefs):
            result = await utils._read_client_timezone()
        assert result == "America/New_York"
        assert utils._CLIENT_TIMEZONE == "America/New_York"

    async def test_ignores_none_value(self) -> None:
        from core import utils
        utils._CLIENT_TIMEZONE = "Europe/Madrid"
        mock_prefs = MagicMock()
        mock_prefs.get = AsyncMock(return_value=None)
        with patch("flet.SharedPreferences", return_value=mock_prefs):
            result = await utils._read_client_timezone()
        assert result is None
        assert utils._CLIENT_TIMEZONE == "Europe/Madrid"

    async def test_ignores_non_string_value(self) -> None:
        from core import utils
        utils._CLIENT_TIMEZONE = "Europe/Madrid"
        mock_prefs = MagicMock()
        mock_prefs.get = AsyncMock(return_value=123)
        with patch("flet.SharedPreferences", return_value=mock_prefs):
            result = await utils._read_client_timezone()
        assert result is None
        assert utils._CLIENT_TIMEZONE == "Europe/Madrid"

    async def test_ignores_string_without_slash(self) -> None:
        from core import utils
        utils._CLIENT_TIMEZONE = "Europe/Madrid"
        mock_prefs = MagicMock()
        mock_prefs.get = AsyncMock(return_value="invalid")
        with patch("flet.SharedPreferences", return_value=mock_prefs):
            result = await utils._read_client_timezone()
        assert result is None


class TestGetClientTimezone:
    """Tests for the get_client_timezone function."""

    def test_returns_stored_timezone(self) -> None:
        from core import utils
        utils._CLIENT_TIMEZONE = "Asia/Tokyo"
        assert get_client_timezone() == "Asia/Tokyo"

    def test_falls_back_to_default_when_none(self) -> None:
        from core import utils
        utils._CLIENT_TIMEZONE = None
        assert get_client_timezone() == "UTC"


class TestGetLocalToday:
    """Tests for the get_local_today function."""

    def test_returns_date_in_client_timezone(self) -> None:
        from core import utils
        utils._CLIENT_TIMEZONE = "Asia/Tokyo"
        expected = datetime.datetime.now(zoneinfo.ZoneInfo("Asia/Tokyo")).date()
        assert get_local_today() == expected

    def test_falls_back_to_default_when_none(self) -> None:
        from core import utils
        utils._CLIENT_TIMEZONE = None
        expected = datetime.datetime.now(zoneinfo.ZoneInfo("UTC")).date()
        assert get_local_today() == expected

    def test_returns_date_object(self) -> None:
        from core import utils
        utils._CLIENT_TIMEZONE = "Europe/Madrid"
        assert isinstance(get_local_today(), datetime.date)


class TestToLocalDate:
    """Tests for the to_local_date conversion function."""

    def test_same_day_same_date(self) -> None:
        utc_dt = datetime.datetime(2024, 6, 15, 12, 0, 0, tzinfo=datetime.timezone.utc)
        result = to_local_date(utc_dt, "America/New_York")
        assert result == datetime.date(2024, 6, 15)

    def test_crosses_date_boundary_forward(self) -> None:
        utc_dt = datetime.datetime(2024, 6, 15, 20, 0, 0, tzinfo=datetime.timezone.utc)
        result = to_local_date(utc_dt, "Asia/Tokyo")
        assert result == datetime.date(2024, 6, 16)

    def test_crosses_date_boundary_backward(self) -> None:
        utc_dt = datetime.datetime(2024, 6, 16, 3, 0, 0, tzinfo=datetime.timezone.utc)
        result = to_local_date(utc_dt, "America/New_York")
        assert result == datetime.date(2024, 6, 15)

    def test_handles_naive_datetime_as_utc(self) -> None:
        utc_dt = datetime.datetime(2024, 6, 15, 22, 0, 0)
        result = to_local_date(utc_dt, "America/New_York")
        assert result == datetime.date(2024, 6, 15)

    def test_handles_negative_offset(self) -> None:
        utc_dt = datetime.datetime(2024, 6, 15, 11, 0, 0, tzinfo=datetime.timezone.utc)
        result = to_local_date(utc_dt, "Pacific/Honolulu")
        assert result == datetime.date(2024, 6, 15)

    def test_handles_positive_offset(self) -> None:
        utc_dt = datetime.datetime(2024, 6, 15, 22, 0, 0, tzinfo=datetime.timezone.utc)
        result = to_local_date(utc_dt, "Pacific/Auckland")
        assert result == datetime.date(2024, 6, 16)
