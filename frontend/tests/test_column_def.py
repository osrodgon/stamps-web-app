"""Unit tests for components/table/column_def.py — formatters and column definitions."""

import pytest

from components.table.column_def import COLUMNS, ColumnDef, fmt_currency, fmt_date, fmt_number
from core.translations import set_language


class TestFmtCurrency:
    """Tests for the fmt_currency locale-aware formatter."""

    def test_english_format_integer(self) -> None:
        assert fmt_currency(1234, "en") == "€1,234.00"

    def test_english_format_decimal(self) -> None:
        assert fmt_currency("1234.56", "en") == "€1,234.56"

    def test_english_format_zero(self) -> None:
        assert fmt_currency(0, "en") == "-"

    def test_english_format_none(self) -> None:
        assert fmt_currency(None, "en") == "-"

    def test_english_format_empty_string(self) -> None:
        assert fmt_currency("", "en") == "-"

    def test_english_large_number(self) -> None:
        assert fmt_currency(1234567.89, "en") == "€1,234,567.89"

    def test_spanish_format_integer(self) -> None:
        assert fmt_currency(1234, "es") == "€1.234,00"

    def test_spanish_format_decimal(self) -> None:
        assert fmt_currency("1234.56", "es") == "€1.234,56"

    def test_spanish_format_zero(self) -> None:
        assert fmt_currency(0, "es") == "-"

    def test_spanish_format_none(self) -> None:
        assert fmt_currency(None, "es") == "-"

    def test_spanish_format_empty_string(self) -> None:
        assert fmt_currency("", "es") == "-"

    def test_spanish_large_number(self) -> None:
        assert fmt_currency(1234567.89, "es") == "€1.234.567,89"


class TestFmtNumber:
    """Tests for the fmt_number locale-aware formatter."""

    def test_english_format_small(self) -> None:
        assert fmt_number(123, "en") == "123"

    def test_english_format_thousands(self) -> None:
        assert fmt_number(1234, "en") == "1,234"

    def test_english_format_millions(self) -> None:
        assert fmt_number(1234567, "en") == "1,234,567"

    def test_english_format_zero(self) -> None:
        assert fmt_number(0, "en") == "-"

    def test_english_format_none(self) -> None:
        assert fmt_number(None, "en") == "-"

    def test_english_format_empty_string(self) -> None:
        assert fmt_number("", "en") == "-"

    def test_english_format_string_number(self) -> None:
        assert fmt_number("500000", "en") == "500,000"

    def test_spanish_format_small(self) -> None:
        assert fmt_number(123, "es") == "123"

    def test_spanish_format_thousands(self) -> None:
        assert fmt_number(1234, "es") == "1.234"

    def test_spanish_format_millions(self) -> None:
        assert fmt_number(1234567, "es") == "1.234.567"

    def test_spanish_format_zero(self) -> None:
        assert fmt_number(0, "es") == "-"

    def test_spanish_format_none(self) -> None:
        assert fmt_number(None, "es") == "-"

    def test_spanish_format_empty_string(self) -> None:
        assert fmt_number("", "es") == "-"

    def test_spanish_format_string_number(self) -> None:
        assert fmt_number("500000", "es") == "500.000"


class TestFmtDate:
    """Tests for the fmt_date locale-aware date formatter."""

    def test_valid_date_english(self) -> None:
        set_language("en")
        result = fmt_date("2023-06-15", "en")
        assert result == "15 of June of 2023"

    def test_valid_date_spanish(self) -> None:
        set_language("es")
        result = fmt_date("2023-06-15", "es")
        assert result == "15 de Junio de 2023"

    def test_first_day_of_year(self) -> None:
        set_language("en")
        result = fmt_date("2024-01-01", "en")
        assert result == "1 of January of 2024"

    def test_last_day_of_year(self) -> None:
        set_language("en")
        result = fmt_date("2024-12-31", "en")
        assert result == "31 of December of 2024"

    def test_empty_string_returns_dash(self) -> None:
        assert fmt_date("", "en") == "-"

    def test_none_returns_dash(self) -> None:
        assert fmt_date(None, "en") == "-"

    def test_invalid_date_returns_raw(self) -> None:
        assert fmt_date("not-a-date", "en") == "not-a-date"

    def test_invalid_format_returns_raw(self) -> None:
        assert fmt_date("15/06/2023", "en") == "15/06/2023"

    def test_all_months_english(self) -> None:
        set_language("en")
        months = [
            ("2024-01-01", "January"),
            ("2024-02-01", "February"),
            ("2024-03-01", "March"),
            ("2024-04-01", "April"),
            ("2024-05-01", "May"),
            ("2024-06-01", "June"),
            ("2024-07-01", "July"),
            ("2024-08-01", "August"),
            ("2024-09-01", "September"),
            ("2024-10-01", "October"),
            ("2024-11-01", "November"),
            ("2024-12-01", "December"),
        ]
        for date_str, expected_month in months:
            result = fmt_date(date_str, "en")
            assert expected_month in result

    def test_all_months_spanish(self) -> None:
        set_language("es")
        months = [
            ("2024-01-01", "Enero"),
            ("2024-02-01", "Febrero"),
            ("2024-03-01", "Marzo"),
            ("2024-04-01", "Abril"),
            ("2024-05-01", "Mayo"),
            ("2024-06-01", "Junio"),
            ("2024-07-01", "Julio"),
            ("2024-08-01", "Agosto"),
            ("2024-09-01", "Septiembre"),
            ("2024-10-01", "Octubre"),
            ("2024-11-01", "Noviembre"),
            ("2024-12-01", "Diciembre"),
        ]
        for date_str, expected_month in months:
            result = fmt_date(date_str, "es")
            assert expected_month in result


class TestColumnDef:
    """Tests for the ColumnDef dataclass."""

    def test_basic_column_def(self) -> None:
        col = ColumnDef("stamps.country", "country", width=100)
        assert col.translation_key == "stamps.country"
        assert col.api_key == "country"
        assert col.width == 100

    def test_default_values(self) -> None:
        col = ColumnDef("ui.date", "date")
        assert col.width is None
        assert col.sortable is False
        assert col.fmt is None

    def test_sortable_column(self) -> None:
        col = ColumnDef("ui.date", "date", sortable=True)
        assert col.sortable is True

    def test_column_with_formatter(self) -> None:
        col = ColumnDef("stamps.total_printed", "total_printed", fmt=fmt_number)
        assert col.fmt is fmt_number

    def test_column_with_text_align(self) -> None:
        import flet as ft

        col = ColumnDef("ui.value", "value", text_align=ft.TextAlign.RIGHT)
        assert col.text_align == ft.TextAlign.RIGHT


class TestColumnsList:
    """Tests for the COLUMNS list structure."""

    def test_columns_is_list(self) -> None:
        assert isinstance(COLUMNS, list)

    def test_columns_not_empty(self) -> None:
        assert len(COLUMNS) > 0

    def test_all_items_are_column_def(self) -> None:
        for col in COLUMNS:
            assert isinstance(col, ColumnDef)

    def test_all_columns_have_translation_key(self) -> None:
        for col in COLUMNS:
            assert isinstance(col.translation_key, str)
            assert len(col.translation_key) > 0

    def test_all_columns_have_api_key(self) -> None:
        for col in COLUMNS:
            assert isinstance(col.api_key, str)
            assert len(col.api_key) > 0

    def test_sortable_columns_exist(self) -> None:
        sortable = [col for col in COLUMNS if col.sortable]
        assert len(sortable) >= 1

    def test_columns_with_formatters(self) -> None:
        with_fmt = [col for col in COLUMNS if col.fmt is not None]
        assert len(with_fmt) >= 1

    def test_columns_unique_api_keys(self) -> None:
        api_keys = [col.api_key for col in COLUMNS]
        assert len(api_keys) == len(set(api_keys))

    def test_country_column_exists(self) -> None:
        countries = [col for col in COLUMNS if col.api_key == "country"]
        assert len(countries) == 1
        assert countries[0].width == 100

    def test_date_column_sortable(self) -> None:
        dates = [col for col in COLUMNS if col.api_key == "date"]
        assert len(dates) == 1
        assert dates[0].sortable is True

    def test_total_printed_has_number_formatter(self) -> None:
        cols = [col for col in COLUMNS if col.api_key == "total_printed"]
        assert len(cols) == 1
        assert cols[0].fmt is fmt_number

    def test_market_value_has_currency_formatter(self) -> None:
        cols = [col for col in COLUMNS if col.api_key == "market_value_mnh"]
        assert len(cols) == 1
        assert cols[0].fmt is fmt_currency
