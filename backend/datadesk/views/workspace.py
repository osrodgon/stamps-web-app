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
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView, TemplateView

from datadesk.mixins import DataDeskAccessMixin
from datadesk.registry import LOOKUPS
from datadesk.rules import series_year_bounds
from datadesk.service import Issue, issue_queryset, stamp_rows
from years_api.models import Year

STAMP_COLUMNS: tuple[dict[str, Any], ...] = (
    {
        "field": "edifil",
        "patch": "edifil_code",
        "title": _("Edifil"),
        "width": 90,
        "mono": True,
    },
    {
        "field": "fesofi",
        "patch": "fesofi_code",
        "title": _("Fesofi"),
        "width": 90,
        "mono": True,
    },
    {"field": "name", "patch": "name", "title": _("Name")},
    {"field": "face_value", "patch": "face_value", "title": _("Face value"),
     "width": 110},
    {"field": "colors", "title": _("Colors"), "width": 220},
    {
        "field": "total_printed",
        "patch": "total_printed",
        "editor": "number",
        "title": _("Total printed"),
        "align": "right",
    },
    {
        "field": "mnh",
        "patch": "market_value_mnh",
        "title": _("MNH"),
        "align": "right",
        "width": 90,
    },
    {
        "field": "used",
        "patch": "market_value_used",
        "title": _("Used"),
        "align": "right",
        "width": 90,
    },
    {"field": "has_image", "title": _("Image"), "align": "center", "width": 64},
)
"""The stamp's own columns.

Only fields a stamp stores: the eight series attributes (country, year, stamp
type, print type, printer, artist, paper type, perforation) are shown once, in
the strip above, and never repeated per row. ``patch`` is the model field the
column writes when it is edited and the key the change is sent with; a column
without it is read-only (colours are a multi-select, the picture is served from
the frontend's tree).
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
            stamp_count=len(rows),
            prefill=None,
            form_fields=series_form_fields(series_values(issue)),
            config=workspace_config(rows, series=issue),
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


def series_values(issue: Issue) -> dict[str, Any]:
    """Returns the current value of every series field, as the form shows it.

    The strip and the new-series form read the same definitions, so the two
    screens cannot disagree on a field name, a kind or an option list. Empty
    means empty: a cleared date travels as ``""`` and the writer turns it into
    ``NULL``, because that is what the form sends when a field is erased.
    """
    return {
        "year": issue.year.year,
        "date": issue.date.isoformat() if issue.date else "",
        "name": issue.name,
        "country": issue.country_id or "",
        "stamp_type": issue.stamp_type_id or "",
        "print_type": issue.print_type_id or "",
        "printer": issue.printer_id or "",
        "artist": issue.artist_id or "",
        "paper_type": issue.paper_type_id or "",
        "perforation": issue.perforation or "",
        "total_printed": issue.total_printed if issue.total_printed else "",
        "market_value_mnh": _amount(issue.market_value_mnh),
        "market_value_used": _amount(issue.market_value_used),
        "description": issue.description or "",
        "note": issue.note or "",
    }


def workspace_config(
    rows: list[dict[str, Any]],
    mode: str = "edit",
    prefill: dict[str, Any] | None = None,
    series: Issue | None = None,
) -> dict[str, Any]:
    """Returns what the JavaScript needs to build the stamp grid.

    The rows travel with the page: one series is at most a few dozen stamps, so
    a second request would cost more than it saves. Titles are resolved here so
    the script holds no interface text, and each row gets the URL of its picture
    so the grid never builds one.

    ``mode=new`` adds the three element ids and the row bounds the script needs:
    it reads them instead of hardcoding names the template owns. ``mode=edit``
    adds the baseline of the series row and the texts the commit bar shows, so
    the script still holds no interface text.
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
    config["applyUrl"] = reverse("datadesk:apply")

    if mode == "edit" and series is not None:
        config["series"] = {
            "id": series.pk,
            "updated_at": series.updated_at.isoformat() if series.updated_at else None,
        }
        config["texts"] = {
            "saved": str(_("Saved")),
            "unsaved": str(_("Edited, not saved yet.")),
            "rejected": str(_("The change was refused.")),
            "noChanges": str(_("Nothing changed.")),
            "seriesSaved": str(_("Series saved.")),
        }

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


def _amount(value: Any) -> str:
    """Returns a decimal as the string the form shows, or ``""`` when unset."""
    return "" if value is None else str(value)
