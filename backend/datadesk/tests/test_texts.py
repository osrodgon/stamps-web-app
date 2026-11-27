"""How a value is written: month names and thousands separators (S34).

The formatting is the language's, and the server decides it: a number reads
``37.500,00`` here and ``37,500.00`` there, and a date says its month by name so
nobody has to work out whether ``01/12`` is December or January.
"""

import datetime

from django.utils import formats, translation

from datadesk.texts import (
    date_template,
    date_text,
    month_abbreviations,
    separators,
)

DAY = datetime.date(1853, 12, 1)


class TestDatesReadAsDates:
    """A date in a cell is prose, not a code."""

    def test_spanish_names_the_month(self) -> None:
        with translation.override("es"):
            assert date_text(DAY) == "1 dic 1853"

    def test_english_names_the_month_too(self) -> None:
        with translation.override("en"):
            assert date_text(DAY) == "Dec 1, 1853"

    def test_the_spanish_month_is_not_capitalised(self) -> None:
        """Django's Spanish abbreviation is; Spanish months are not."""
        with translation.override("es"):
            assert "Dic" not in date_text(DAY)

    def test_a_series_without_a_date_writes_nothing(self) -> None:
        assert date_text(None) == ""


class TestTheMonthList:
    """The picker and the grid read the same abbreviations."""

    def test_twelve_names(self) -> None:
        with translation.override("es"):
            assert len(month_abbreviations()) == 12

    def test_spanish_writes_them_lowercase(self) -> None:
        with translation.override("es"):
            assert month_abbreviations()[11] == "dic"

    def test_english_capitalises_them(self) -> None:
        with translation.override("en"):
            assert month_abbreviations()[11] == "Dec"

    def test_the_field_and_the_cell_share_the_order(self) -> None:
        """The date template and `date_text` cannot drift apart."""
        for language in ("es", "en"):
            with translation.override(language):
                assert date_text(DAY) == date_template() % {
                    "day": "1",
                    "month": month_abbreviations()[11],
                    "year": "1853",
                }


class TestSeparators:
    """The characters the script puts between digits."""

    def test_spanish_groups_with_a_dot(self) -> None:
        with translation.override("es"):
            assert separators() == {"thousand": ".", "decimal": ","}

    def test_english_groups_with_a_comma(self) -> None:
        with translation.override("en"):
            assert separators() == {"thousand": ",", "decimal": "."}

    def test_a_language_without_a_row_falls_back_to_django(self) -> None:
        """Adding a language needs no table: Django already has its separators."""
        with translation.override("fr"):
            assert separators() == {
                "thousand": formats.get_format("THOUSAND_SEPARATOR"),
                "decimal": formats.get_format("DECIMAL_SEPARATOR"),
            }
