"""Issue workspace: one series with its stamps, in both modes.

S10 renders what the database holds. S11 adds the dry ``mode=new`` on the same
template: the series form, the row generator that lives entirely in the browser
and the guards that stop the user from losing work that cannot be recovered.
Nothing here writes: the write core arrives in S12.
"""
from dataclasses import dataclass
from typing import Any

from django.db.models import QuerySet
from django.templatetags.static import static
from django.urls import reverse
from django.utils.formats import date_format, number_format
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView, TemplateView

from datadesk.mixins import DataDeskAccessMixin
from datadesk.registry import LOOKUPS
from datadesk.rules import series_year_bounds
from datadesk.service import Issue, issue_queryset, stamp_rows
from years_api.models import Year

STAMP_COLUMNS: tuple[dict[str, Any], ...] = (
    {"field": "edifil", "title": _("Edifil"), "width": 90, "mono": True},
    {"field": "fesofi", "title": _("Fesofi"), "width": 90, "mono": True},
    {"field": "name", "title": _("Name")},
    {"field": "face_value", "title": _("Face value"), "width": 110},
    {"field": "colors", "title": _("Colors"), "width": 220},
    {
        "field": "total_printed",
        "title": _("Total printed"),
        "align": "right",
    },
    {"field": "mnh", "title": _("MNH"), "align": "right", "width": 90},
    {"field": "used", "title": _("Used"), "align": "right", "width": 90},
    {"field": "has_image", "title": _("Image"), "align": "center", "width": 64},
)
"""The stamp's own columns.

Only fields a stamp stores: the eight series attributes (country, year, stamp
type, print type, printer, artist, paper type, perforation) are shown once, in
the strip above, and never repeated per row.
"""

SERIES_FIELDS: tuple[dict[str, Any], ...] = (
    {"name": "year", "label": _("Year"), "kind": "year", "required": True},
    {"name": "date", "label": _("Date"), "kind": "date"},
    {"name": "name", "label": _("Name"), "kind": "text", "required": True,
     "wide": True},
    {"name": "country", "label": _("Country"), "kind": "select",
     "lookup": "country"},
    {"name": "stamp_type", "label": _("Stamp type"), "kind": "select",
     "lookup": "stamp_type"},
    {"name": "print_type", "label": _("Print type"), "kind": "select",
     "lookup": "print_type"},
    {"name": "printer", "label": _("Printer"), "kind": "select",
     "lookup": "printer"},
    {"name": "artist", "label": _("Artist"), "kind": "select",
     "lookup": "artist"},
    {"name": "paper_type", "label": _("Paper type"), "kind": "select",
     "lookup": "paper_type"},
    {"name": "perforation", "label": _("Perforation"), "kind": "text"},
    {"name": "total_printed", "label": _("Total printed"), "kind": "number",
     "step": "1", "min": 0},
    {"name": "market_value_mnh", "label": _("Market value MNH"),
     "kind": "number", "step": "0.01", "min": 0},
    {"name": "market_value_used", "label": _("Market value used"),
     "kind": "number", "step": "0.01", "min": 0},
    {"name": "description", "label": _("Description"), "kind": "textarea",
     "wide": True},
    {"name": "note", "label": _("Note"), "kind": "textarea", "wide": True},
)
"""The series form, in display order (``mode=new`` only).

The order is the strip's: the identity fields first, then the classification,
then the money. ``lookup`` points at ``datadesk.registry`` so the select options
and their labels come from the same place the lookup screens will use.

``year`` is not a lookup select: a series is almost always the first row of a
new year, so the field takes a number and the existing years are only
suggestions. The row is created when the series is saved (``get_or_create``, as
S12 does for every lookup created inline), which is why the form accepts a value
that does not exist yet.
"""

PREFILL_FIELDS: tuple[str, ...] = ("year", "country")
"""The only series fields a new issue copies from the last one.

Country is almost constant and the year is the context of the whole screen, so
both are cheap to verify and expensive to retype. The classification changes
from series to series, the date and the name identify the series, and the print
run and market values belong to a set: copying any of those would write one
series' numbers into another.
"""

DEFAULT_NEW_ROWS = 4
MIN_NEW_ROWS = 1
MAX_NEW_ROWS = 100
NEW_ROW_PREFIX = "new-"
"""Rows of ``mode=new`` exist only in the browser, so their ids are made up.

The real ids are numbers, so a ``new-`` prefix can never collide with one; the
prefix travels in the page configuration so the script holds no convention.
"""


class IssueWorkspaceView(DataDeskAccessMixin, DetailView):
    """Renders one series and its stamps without allowing any edit."""

    template_name = "datadesk/issue_workspace.html"
    context_object_name = "issue"

    def get_queryset(self) -> QuerySet[Issue]:
        """Loads the issue with its lookups and stamp count in one query."""
        return issue_queryset()

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Adds the metadata strip, the stamp rows and the grid configuration."""
        context = super().get_context_data(**kwargs)
        issue: Issue = self.object
        rows = stamp_rows(issue)

        context.update(
            mode="edit",
            metadata=issue_metadata(issue),
            stamp_count=len(rows),
            prefill=None,
            form_fields=[],
            config=workspace_config(rows),
        )
        return context


class IssueNewView(DataDeskAccessMixin, TemplateView):
    """Renders the dry ``mode=new`` workspace.

    Nothing is sent to the server: the form is not submitted and the rows live
    in the browser, so reloading discards the draft. The ``beforeunload`` guard
    is the only net, by decision: a new series is finished now or started again.
    """

    template_name = "datadesk/issue_workspace.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Adds the form, the prefill and a grid with no rows."""
        context = super().get_context_data(**kwargs)
        prefill = last_issue_prefill()

        context.update(
            mode="new",
            prefill=prefill,
            form_fields=series_form_fields(prefill),
            metadata=[],
            stamp_count=0,
            config=workspace_config([], mode="new", prefill=prefill),
        )
        return context


def last_issue_prefill() -> dict[str, Any] | None:
    """Returns the country and year a new series starts with, if any.

    The last issue is the highest id, not the newest year: the years are entered
    in batches and the row added most recently is the one being continued. A
    ``None`` means there is nothing to copy — a fresh database — and the page
    hides the button instead of showing it disabled.
    """
    last = Issue.objects.order_by("-id").values("year__year", "country_id").first()
    if last is None:
        return None

    values: dict[str, Any] = {"year": last["year__year"]}
    if last["country_id"] is not None:
        values["country"] = last["country_id"]
    return values


def series_form_fields(prefill: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Returns the series form with its lookups loaded and marked.

    Only the fields in ``PREFILL_FIELDS`` arrive with a value; the rest is empty
    on purpose, and every list of options is ordered by the name the lookup
    screen shows. The year carries the year number, not the row id: the field
    takes a number and an unknown year is created when the series is saved.
    """
    values = prefill or {}
    fields: list[dict[str, Any]] = []
    for definition in SERIES_FIELDS:
        field = dict(definition)
        field["value"] = values.get(field["name"], "")
        if field["kind"] == "year":
            field["min"], field["max"] = series_year_bounds()
            field["options"] = year_suggestions()
        elif "lookup" in field:
            field["options"] = lookup_options(field["lookup"], field["value"])
        fields.append(field)
    return fields


def year_suggestions() -> list[dict[str, Any]]:
    """Returns the years that already exist, newest first.

    They are datalist entries, not select options: the field must still accept a
    year that no row holds, and the suggestions are there for the common case of
    correcting an existing series' year.
    """
    return [
        {"value": year, "label": str(year)}
        for year in Year.objects.order_by("-year").values_list("year", flat=True)
    ]


def lookup_options(key: str, selected: Any) -> list[dict[str, Any]]:
    """Returns the options of a lookup select, marking the prefilled one."""
    lookup = LOOKUPS[key]
    rows = lookup.model.objects.order_by(lookup.name_field)
    return [
        {
            "value": row.pk,
            "label": str(getattr(row, lookup.name_field)),
            "selected": str(row.pk) == str(selected),
        }
        for row in rows
    ]


@dataclass(frozen=True)
class NewRowSettings:
    """Bounds of the ``rows=N`` control, sent to the browser.

    The default is 4 because the real average is 3.8 stamps per issue; deriving
    it from the last series would spawn 57 empty rows after a long one.
    """

    default: int = DEFAULT_NEW_ROWS
    min: int = MIN_NEW_ROWS
    max: int = MAX_NEW_ROWS

    def as_dict(self) -> dict[str, int]:
        """Returns the bounds in the shape the page configuration uses."""
        return {"default": self.default, "min": self.min, "max": self.max}


def issue_metadata(issue: Issue) -> list[dict[str, Any]]:
    """Returns the strip above the grid, already formatted for the language.

    The strip is the only place the series values appear: the eight series
    attributes are not repeated per row, and nothing is inherited by a stamp.
    """
    return [
        {"label": _("Year"), "value": _display(issue.year.year)},
        {"label": _("Date"), "value": _display(issue.date, "date")},
        {"label": _("Name"), "value": _display(issue.name), "wide": True},
        {"label": _("Country"), "value": _display(_name_of(issue.country))},
        {"label": _("Stamp type"), "value": _display(_name_of(issue.stamp_type))},
        {"label": _("Print type"), "value": _display(_name_of(issue.print_type))},
        {"label": _("Printer"), "value": _display(_name_of(issue.printer))},
        {"label": _("Artist"), "value": _display(_name_of(issue.artist))},
        {"label": _("Paper type"), "value": _display(_name_of(issue.paper_type))},
        {"label": _("Perforation"), "value": _display(issue.perforation)},
        {
            "label": _("Total printed"),
            "value": _display(issue.total_printed, "count"),
        },
        {
            "label": _("Market value MNH"),
            "value": _display(issue.market_value_mnh, "money"),
        },
        {
            "label": _("Market value used"),
            "value": _display(issue.market_value_used, "money"),
        },
        {"label": _("Description"), "value": _display(issue.description), "wide": True},
        {"label": _("Note"), "value": _display(issue.note), "wide": True},
    ]


def workspace_config(
    rows: list[dict[str, Any]],
    mode: str = "edit",
    prefill: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Returns what the JavaScript needs to build the stamp grid.

    The rows travel with the page: one series is at most a few dozen stamps, so
    a second request would cost more than it saves. Titles are resolved here so
    the script holds no interface text, and each row gets the URL of its picture
    so the grid never builds one.

    ``mode=new`` adds the three element ids and the row bounds the script needs:
    it reads them instead of hardcoding names the template owns.
    """
    for row in rows:
        row["image_url"] = (
            reverse("datadesk:stamp_image", args=[row["id"]])
            if row.get("has_image")
            else None
        )

    config: dict[str, Any] = {
        "mode": mode,
        "data": rows,
        "columns": [
            {**column, "title": str(column["title"])} for column in STAMP_COLUMNS
        ],
        "issuesUrl": reverse("datadesk:issues"),
        "fallbackImage": static("datadesk/no_stamp.webp"),
    }
    config["emptyText"] = str(
        _("No stamp rows yet.") if mode == "new" else _("No stamps in this issue.")
    )

    if mode == "new":
        config.update(
            nameInput="field-name",
            rowsInput="row-count",
            countBadge="stamp-count",
            rowIdPrefix=NEW_ROW_PREFIX,
            rows=NewRowSettings().as_dict(),
            prefill=prefill,
        )
    return config


def _name_of(related: Any) -> str | None:
    """Returns the name of a lookup, or ``None`` when the FK is empty."""
    return related.name if related else None


def _display(value: Any, kind: str = "text") -> str:
    """Formats a value for the strip, following the active language.

    ``count`` adds the thousand separator and ``money`` also fixes two
    decimals; both read the locale, so Spanish gets ``500.000`` and English
    ``500,000``. A missing value is a dash, never an empty cell.
    """
    if value is None or value == "":
        return "—"
    if kind == "date":
        return date_format(value, "SHORT_DATE_FORMAT")
    if kind == "money":
        return f"{number_format(value, 2, force_grouping=True)} €"
    if kind == "count":
        return number_format(value, force_grouping=True)
    return str(value)
