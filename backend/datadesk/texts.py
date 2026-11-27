"""Text the page scripts are handed, already translated.

Every interface string in DataDesk comes from the server, translated by Django,
and a script only substitutes the number or the name into the template it was
given. That is what lets the browser stay free of UI text and of a second
translation system.
"""
from datetime import date

from django.utils import formats
from django.utils.translation import get_language, ngettext


def plural_forms(one: str, other: str) -> dict[str, str]:
    """Returns the two translated forms of a plural, resolved by language.

    ``ngettext`` decides which form belongs to each count, so the browser does
    not need a plural rule and only replaces ``%(count)s``.
    """
    return {"one": str(ngettext(one, other, 1)), "other": str(ngettext(one, other, 2))}

SEPARATORS: dict[str, dict[str, str]] = {
    "es": {"thousand": ".", "decimal": ","},
    "en": {"thousand": ",", "decimal": "."},
}
"""How DataDesk writes a number, by language.

Django's Spanish uses a no-break space for the thousands; it is correct and it is
also unreadable in a 13px cell, where a market value reads as money — and money is
written ``37.500,00`` here. A language this table does not know falls back to
Django's own pair, so adding a language needs nothing.
"""


def separators() -> dict[str, str]:
    """Returns the separators of the active language for the page scripts."""
    language = (get_language() or "en")[:2]
    known = SEPARATORS.get(language)
    if known is not None:
        return known
    return {
        "thousand": formats.get_format("THOUSAND_SEPARATOR"),
        "decimal": formats.get_format("DECIMAL_SEPARATOR"),
    }


DATE_TEMPLATES: dict[str, str] = {
    "es": "%(day)s %(month)s %(year)s",
    "en": "%(month)s %(day)s, %(year)s",
}
"""Where the parts of a date go: ``1 dic 1853`` against ``Dec 1, 1853``.

The date field and the grid read the same table, so the same day cannot be
written two ways on two screens.
"""


def date_template() -> str:
    """Returns the date template of the active language."""
    return DATE_TEMPLATES.get((get_language() or "en")[:2], DATE_TEMPLATES["en"])


def month_abbreviations() -> list[str]:
    """Returns the twelve month abbreviations the active language uses.

    They come from Django's own date formatting (the ``M`` token), which is the
    same source ``date_text`` reads, so the picker's month list and the written
    date cannot disagree. Spanish writes months in lowercase and Django
    capitalises the abbreviation, hence the ``lower()``.
    """
    names = [
        formats.date_format(date(2000, index, 1), "M") for index in range(1, 13)
    ]
    if (get_language() or "en").startswith("es"):
        return [name.lower() for name in names]
    return names


def date_text(value: date | None) -> str:
    """Returns a date the way the active language writes it in a cell.

    ``1 dic 1853`` in Spanish and ``Dec 1, 1853`` in English: the month by name,
    because ``01/12/1853`` is one day in each language and the point of writing
    it this way is that nobody has to stop and think which.
    """
    if value is None:
        return ""
    return date_template() % {
        "day": str(value.day),
        "month": month_abbreviations()[value.month - 1],
        "year": str(value.year),
    }
