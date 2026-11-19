"""Text the page scripts are handed, already translated.

Every interface string in DataDesk comes from the server, translated by Django,
and a script only substitutes the number or the name into the template it was
given. That is what lets the browser stay free of UI text and of a second
translation system.
"""
from django.utils.translation import ngettext


def plural_forms(one: str, other: str) -> dict[str, str]:
    """Returns the two translated forms of a plural, resolved by language.

    ``ngettext`` decides which form belongs to each count, so the browser does
    not need a plural rule and only replaces ``%(count)s``.
    """
    return {"one": str(ngettext(one, other, 1)), "other": str(ngettext(one, other, 2))}
