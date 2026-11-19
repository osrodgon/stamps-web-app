"""Workbench page: the issues grid with its filters."""

import json
from typing import Any

from django.http import HttpRequest
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from countries_api.models import Country
from datadesk.mixins import DataDeskAccessMixin
from datadesk.service import DEFAULT_PAGE_SIZE, IssueFilters, page_of_issue
from stamp_types_api.models import StampType

COLUMNS: tuple[dict[str, Any], ...] = (
    {"field": "year", "title": _("Year"), "visible": True, "align": "right", "grow": 1},
    {"field": "date", "title": _("Date"), "visible": True, "grow": 1},
    {"field": "name", "title": _("Name"), "visible": True, "grow": 4, "min": 180},
    {"field": "country", "title": _("Country"), "visible": True, "grow": 2},
    {"field": "stamp_type", "title": _("Stamp type"), "visible": True, "grow": 2},
    {"field": "printer", "title": _("Printer"), "visible": True, "grow": 2},
    {
        "field": "stamps",
        "title": _("Stamps"),
        "visible": True,
        "align": "right",
        "grow": 1,
    },
    {"field": "mnh", "title": _("MNH"), "visible": True, "align": "right", "grow": 1},
    {"field": "used", "title": _("Used"), "visible": True, "align": "right", "grow": 1},
    {"field": "print_type", "title": _("Print type"), "visible": False, "grow": 2},
    {"field": "artist", "title": _("Artist"), "visible": False, "grow": 2},
    {"field": "paper_type", "title": _("Paper type"), "visible": False, "grow": 2},
    {"field": "perforation", "title": _("Perforation"), "visible": False, "grow": 1},
    {
        "field": "total_printed",
        "title": _("Total printed"),
        "visible": False,
        "align": "right",
        "grow": 1,
    },
    {"field": "gaps", "title": _("Gaps"), "visible": False, "grow": 1},
)
"""Column definitions, translated here so the JavaScript holds no UI text.

Fourteen columns do not fit legibly side by side, so only the first nine are
shown by default and the rest live behind the column toggle. ``grow`` is how
much of the width a column asks for when the grid fits itself to the page: the
name takes four shares and the numbers one, so fitting never squeezes the only
column whose content is long.
"""


class WorkbenchView(DataDeskAccessMixin, TemplateView):
    """Renders the read-only issues grid."""

    template_name = "datadesk/workbench.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Adds the filter state, the lookups and the grid configuration."""
        context = super().get_context_data(**kwargs)
        filters = filters_from(self.request)

        # ``focus`` is how the workspace says "the series you just saved is this
        # one": the page it lives on has to be resolved here, because the grid
        # pages on the server.
        focus = _int(self.request, "focus")
        initial_page = page_of_issue(focus, filters) if focus is not None else 1

        context.update(
            filters=filters,
            filter_query=filters.to_query(),
            countries=Country.objects.order_by("name"),
            stamp_types=StampType.objects.order_by("name"),
            page_size=DEFAULT_PAGE_SIZE,
            config=grid_config(focus=focus, initial_page=initial_page),
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


def _int(request: HttpRequest, name: str) -> int | None:
    """Returns an integer query parameter, or ``None`` when absent or invalid."""
    raw = request.GET.get(name, "").strip()
    if raw == "":
        return None
    try:
        return int(raw)
    except ValueError:
        return None


def grid_config(focus: int | None = None, initial_page: int = 1) -> dict[str, Any]:
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
        "initialPage": initial_page,
        "focus": focus,
    }
