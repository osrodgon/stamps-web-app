"""Workbench page: the issues grid with its filters."""
import json
from typing import Any

from django.http import HttpRequest
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from countries_api.models import Country
from datadesk.mixins import DataDeskAccessMixin
from datadesk.service import DEFAULT_PAGE_SIZE, IssueFilters
from stamp_types_api.models import StampType

COLUMNS: tuple[dict[str, Any], ...] = (
    {"field": "year", "title": _("Year"), "visible": True, "align": "right"},
    {"field": "date", "title": _("Date"), "visible": True},
    {"field": "name", "title": _("Name"), "visible": True},
    {"field": "country", "title": _("Country"), "visible": True},
    {"field": "stamp_type", "title": _("Stamp type"), "visible": True},
    {"field": "printer", "title": _("Printer"), "visible": True},
    {"field": "stamps", "title": _("Stamps"), "visible": True, "align": "right"},
    {"field": "mnh", "title": _("MNH"), "visible": True, "align": "right"},
    {"field": "used", "title": _("Used"), "visible": True, "align": "right"},
    {"field": "print_type", "title": _("Print type"), "visible": False},
    {"field": "artist", "title": _("Artist"), "visible": False},
    {"field": "paper_type", "title": _("Paper type"), "visible": False},
    {"field": "perforation", "title": _("Perforation"), "visible": False},
    {
        "field": "total_printed",
        "title": _("Total printed"),
        "visible": False,
        "align": "right",
    },
    {"field": "gaps", "title": _("Gaps"), "visible": False},
)
"""Column definitions, translated here so the JavaScript holds no UI text.

Fourteen columns do not fit legibly at 1366px, so only the first nine are shown
by default and the rest live behind the column toggle.
"""


class WorkbenchView(DataDeskAccessMixin, TemplateView):
    """Renders the read-only issues grid."""

    template_name = "datadesk/workbench.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Adds the filter state, the lookups and the grid configuration."""
        context = super().get_context_data(**kwargs)
        filters = filters_from(self.request)

        context.update(
            filters=filters,
            filter_query=filters.to_query(),
            countries=Country.objects.order_by("name"),
            stamp_types=StampType.objects.order_by("name"),
            page_size=DEFAULT_PAGE_SIZE,
            config=grid_config(),
        )
        return context


def filters_from(request: HttpRequest) -> IssueFilters:
    """Rebuilds the filter state from the query string.

    The URL is the single source of truth: the page renders with those filters
    and the grid asks for the same values, so a shared link opens the same view.
    """

    def _int(name: str) -> int | None:
        raw = request.GET.get(name, "").strip()
        if raw == "":
            return None
        try:
            return int(raw)
        except ValueError:
            return None

    return IssueFilters(
        year_min=_int("year_min"),
        year_max=_int("year_max"),
        q=request.GET.get("q", "").strip(),
        country=_int("country"),
        stamp_type=_int("stamp_type"),
        attention=request.GET.get("attention", "").strip(),
    )


def grid_config() -> dict[str, Any]:
    """Returns what the JavaScript needs to build the grid.

    Titles are resolved here, per request, so they follow the active language.
    """
    return {
        "dataUrl": reverse("datadesk:issue_grid"),
        "columns": [{**column, "title": str(column["title"])} for column in COLUMNS],
        "pageSize": DEFAULT_PAGE_SIZE,
        "emptyText": str(_("No issues match these filters.")),
        "counterText": str(_("issues")),
        "openText": str(_("Open")),
        "issueUrlPrefix": reverse("datadesk:issues"),
    }
