"""Unit tests for core/translations.py — translation system."""

import pytest

from core.translations import Translations, _, get_language, set_language


class TestGetNestedValue:
    """Tests for the _get_nested_value static method."""

    def test_simple_key(self) -> None:
        data = {"key": "value"}
        assert Translations._get_nested_value(data, "key") == "value"

    def test_dot_notation_two_levels(self) -> None:
        data = {"auth": {"sign_in": "Sign In"}}
        assert Translations._get_nested_value(data, "auth.sign_in") == "Sign In"

    def test_dot_notation_three_levels(self) -> None:
        data = {"date": {"months": {"1": "January"}}}
        assert Translations._get_nested_value(data, "date.months.1") == "January"

    def test_missing_key_returns_none(self) -> None:
        data = {"auth": {"sign_in": "Sign In"}}
        assert Translations._get_nested_value(data, "auth.logout") is None

    def test_missing_intermediate_key_returns_none(self) -> None:
        data = {"auth": {"sign_in": "Sign In"}}
        assert Translations._get_nested_value(data, "profile.settings") is None

    def test_key_with_non_dict_intermediate_returns_none(self) -> None:
        data = {"key": "not_a_dict"}
        assert Translations._get_nested_value(data, "key.subkey") is None

    def test_empty_dict_returns_none(self) -> None:
        assert Translations._get_nested_value({}, "any.key") is None

    def test_simple_key_missing(self) -> None:
        data = {"other": "value"}
        assert Translations._get_nested_value(data, "missing") is None


class TestTranslate:
    """Tests for the translate static method."""

    def test_translate_simple_key_english(self) -> None:
        result = Translations.translate("auth.sign_in", language="en")
        assert result == "Sign In"

    def test_translate_simple_key_spanish(self) -> None:
        result = Translations.translate("auth.sign_in", language="es")
        assert result == "Iniciar sesión"

    def test_translate_dot_notation(self) -> None:
        result = Translations.translate("stamps.country", language="en")
        assert result == "Country"

    def test_translate_fallback_to_english(self) -> None:
        result = Translations.translate("ui.of", language="es")
        assert result == "de"

    def test_translate_returns_key_if_not_found(self) -> None:
        result = Translations.translate("nonexistent.key", language="en")
        assert result == "nonexistent.key"

    def test_translate_with_interpolation(self) -> None:
        result = Translations.translate("ui.of", language="en")
        assert result == "of"

    def test_translate_missing_format_key_returns_raw(self) -> None:
        result = Translations.translate("ui.of", language="en", missing_var="test")
        assert result == "of"

    def test_translate_uses_current_language_when_none(self) -> None:
        set_language("en")
        result = Translations.translate("auth.sign_in")
        assert result == "Sign In"

    def test_translate_nested_months(self) -> None:
        result = Translations.translate("date.months.6", language="en")
        assert result == "June"

    def test_translate_nested_months_spanish(self) -> None:
        result = Translations.translate("date.months.6", language="es")
        assert result == "Junio"


class TestUnderscoreFunction:
    """Tests for the _() translation shortcut function."""

    def test_underscore_simple_key(self) -> None:
        set_language("en")
        result = _("auth.sign_in")
        assert result == "Sign In"

    def test_underscore_spanish(self) -> None:
        set_language("es")
        result = _("auth.sign_in")
        assert result == "Iniciar sesión"

    def test_underscore_with_language_override(self) -> None:
        set_language("es")
        result = _("auth.sign_in", _language="en")
        assert result == "Sign In"

    def test_underscore_returns_key_if_missing(self) -> None:
        set_language("en")
        result = _("missing.translation.key")
        assert result == "missing.translation.key"

    def test_underscore_with_interpolation(self) -> None:
        set_language("en")
        result = _("ui.of")
        assert result == "of"


class TestSetGetLanguage:
    """Tests for set_language() and get_language() functions."""

    def test_set_language_english(self) -> None:
        set_language("en")
        assert get_language() == "en"

    def test_set_language_spanish(self) -> None:
        set_language("es")
        assert get_language() == "es"

    def test_set_language_arbitrary_code(self) -> None:
        set_language("fr")
        assert get_language() == "fr"

    def test_get_language_returns_string(self) -> None:
        set_language("en")
        result = get_language()
        assert isinstance(result, str)


class TestTranslationsLoaded:
    """Tests that translations are properly loaded from JSON files."""

    def test_english_translations_loaded(self) -> None:
        assert "en" in Translations.translations

    def test_spanish_translations_loaded(self) -> None:
        assert "es" in Translations.translations

    def test_english_has_auth_section(self) -> None:
        assert "auth" in Translations.translations["en"]

    def test_spanish_has_auth_section(self) -> None:
        assert "auth" in Translations.translations["es"]

    def test_english_has_date_months(self) -> None:
        assert "date" in Translations.translations["en"]
        assert "months" in Translations.translations["en"]["date"]

    def test_spanish_has_date_months(self) -> None:
        assert "date" in Translations.translations["es"]
        assert "months" in Translations.translations["es"]["date"]

    def test_english_months_count(self) -> None:
        months = Translations.translations["en"]["date"]["months"]
        assert len(months) == 12

    def test_spanish_months_count(self) -> None:
        months = Translations.translations["es"]["date"]["months"]
        assert len(months) == 12
