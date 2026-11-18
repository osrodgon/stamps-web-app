"""Reference tables DataDesk may edit.

One entry per lookup: the model behind it, the column that identifies a row, a
translated label, whether the value is numeric, and the relations that point at
it. The last piece is what S19 uses to count usage and to move references when
two lookups are merged.
"""
from dataclasses import dataclass, field

from django.db import models
from django.utils.translation import gettext_lazy as _

from artists_api.models import Artist
from colors_api.models import Color
from countries_api.models import Country
from paper_types_api.models import PaperType
from print_types_api.models import PrintType
from printers_api.models import Printer
from stamp_types_api.models import StampType
from years_api.models import Year


@dataclass(frozen=True)
class Lookup:
    """Describes one editable reference table.

    Attributes:
        model: The model behind the lookup.
        label: Translated name shown in menus and screens.
        name_field: Column that identifies a row (``year`` for years).
        numeric: Whether the value sorts and compares as a number.
        refs: ``(model_label, field_name)`` pairs pointing at this lookup.
    """

    model: type[models.Model]
    label: str
    name_field: str = "name"
    numeric: bool = False
    refs: tuple[tuple[str, str], ...] = field(default_factory=tuple)


LOOKUPS: dict[str, Lookup] = {
    "year": Lookup(
        model=Year,
        label=_("Year"),
        name_field="year",
        numeric=True,
        refs=(("issues_api.Issue", "year"),),
    ),
    "country": Lookup(
        model=Country,
        label=_("Country"),
        refs=(("issues_api.Issue", "country"),),
    ),
    "color": Lookup(
        model=Color,
        label=_("Color"),
        refs=(("stamps_api.Stamp", "colors"),),
    ),
    "artist": Lookup(
        model=Artist,
        label=_("Artist"),
        refs=(("issues_api.Issue", "artist"),),
    ),
    "printer": Lookup(
        model=Printer,
        label=_("Printer"),
        refs=(("issues_api.Issue", "printer"),),
    ),
    "paper_type": Lookup(
        model=PaperType,
        label=_("Paper type"),
        refs=(("issues_api.Issue", "paper_type"),),
    ),
    "print_type": Lookup(
        model=PrintType,
        label=_("Print type"),
        refs=(("issues_api.Issue", "print_type"),),
    ),
    "stamp_type": Lookup(
        model=StampType,
        label=_("Stamp type"),
        refs=(("issues_api.Issue", "stamp_type"),),
    ),
}
"""The 8 lookups DataDesk can create and merge.

``ConditionType`` is deliberately absent: it is admin-only and out of scope.
"""


def get_lookup(key: str) -> Lookup:
    """Returns the lookup registered under ``key``.

    Raises:
        KeyError: If the key is not a known lookup.
    """
    return LOOKUPS[key]
