"""Unit tests for core/utils.py — pure validation functions."""

from core.utils import is_strong_password, is_valid_email


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




