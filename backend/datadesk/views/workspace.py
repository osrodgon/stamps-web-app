"""Issue workspace: one series with its stamps, read-only (S10).

The same template hosts ``mode=new`` from S11 onwards and the editing of S13
and S14; this step only renders what the database already holds.
"""
from typing import Any

from django.db.models import QuerySet
from django.templatetags.static import static
from django.urls import reverse
from django.utils.formats import date_format, number_format
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView

from datadesk.mixins import DataDeskAccessMixin
from datadesk.service import Issue, issue_queryset, stamp_rows

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
            config=workspace_config(rows),
        )
        return context


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


def workspace_config(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Returns what the JavaScript needs to build the stamp grid.

    The rows travel with the page: one series is at most a few dozen stamps, so
    a second request would cost more than it saves. Titles are resolved here so
    the script holds no interface text, and each row gets the URL of its picture
    so the grid never builds one.
    """
    for row in rows:
        row["image_url"] = (
            reverse("datadesk:stamp_image", args=[row["id"]])
            if row.get("has_image")
            else None
        )

    return {
        "data": rows,
        "columns": [
            {**column, "title": str(column["title"])} for column in STAMP_COLUMNS
        ],
        "emptyText": str(_("No stamps in this issue.")),
        "issuesUrl": reverse("datadesk:issues"),
        "fallbackImage": static("datadesk/no_stamp.webp"),
    }


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
