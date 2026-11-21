"""Workbench page: the issues grid with its filters."""

import json
from typing import Any

from django.http import HttpRequest
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from datadesk.mixins import DataDeskAccessMixin
from datadesk.registry import LOOKUPS
from datadesk.service import (
    ATTENTION_KEYS,
    DEFAULT_PAGE_SIZE,
    FILTER_NAMES,
    IssueFilters,
    page_of_issue,
)

FILTER_LOOKUPS: tuple[str, ...] = (
    "country",
    "stamp_type",
    "printer",
    "artist",
    "paper_type",
    "print_type",
    "color",
)
"""The filters that are one reference table, in the order the form shows them.

The keys are the registry ones, so the label, the model and the column that
names a row come from ``datadesk.registry`` instead of a second copy here.
"""

PRIMARY_LOOKUPS: tuple[str, ...] = ("country", "stamp_type")
"""The two the bar has always had: they are on screen, not behind a disclosure."""

EXTRA_LOOKUPS: tuple[str, ...] = (
    "printer",
    "artist",
    "paper_type",
    "print_type",
    "color",
)
"""The five S30 added. Behind "More filters" so the bar keeps its old height:
seven selects at once pushed the grid's pagination below the fold."""

PRIMARY_LABELS: dict[str, Any] = {
    "year_min": _("From year"),
    "year_max": _("To year"),
    "q": _("Name"),
}
"""The filters that are not a reference table."""

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
            filter_options=filter_options(filters, PRIMARY_LOOKUPS),
            extra_filter_options=filter_options(filters, EXTRA_LOOKUPS),
            extra_filters_open=any(
                getattr(filters, key) is not None for key in EXTRA_LOOKUPS
            ),
            page_size=DEFAULT_PAGE_SIZE,
            config=grid_config(focus=focus, initial_page=initial_page),
        )
        return context


def filters_from(request: HttpRequest) -> IssueFilters:
    """Rebuilds the filter state from the query string.

    The URL is the single source of truth: the page renders with those filters
    and the grid asks for the same values, so a shared link opens the same view.
    Every filter is read from ``FILTER_NAMES``, so a filter added to the service
    cannot be missing here.
    """

    values: dict[str, Any] = {}
    for name in FILTER_NAMES:
        if name == "q":
            values[name] = request.GET.get("q", "").strip()
        elif name == "attention":
            value = request.GET.get("attention", "").strip()
            # Anything not registered is ignored, not passed through: the
            # dashboard links and the chips are the only places a key comes
            # from, and a typo must not turn into a filter nobody defined.
            values[name] = value if value in ATTENTION_KEYS else ""
        else:
            values[name] = _int(request, name)
    return IssueFilters(**values)


def filter_options(
    filters: IssueFilters, keys: tuple[str, ...] = FILTER_LOOKUPS
) -> list[dict[str, Any]]:
    """Returns the rows of the given reference filters, already selected.

    The tables are small enough to ship whole (the largest is 300 colours), and
    a native ``select`` needs no script: it works before the grid does, and it
    keeps the form the single place a filter is set.
    """
    options = []
    for key in keys:
        lookup = LOOKUPS[key]
        chosen = getattr(filters, key)
        options.append(
            {
                "key": key,
                "label": lookup.label,
                "rows": [
                    {
                        "id": row.pk,
                        "name": str(getattr(row, lookup.name_field)),
                        "selected": row.pk == chosen,
                    }
                    for row in lookup.model.objects.order_by(lookup.name_field)
                ],
            }
        )
    return options


def _filter_label(name: str) -> Any:
    """Returns the translated name of a filter, for the chip the script paints."""
    if name in PRIMARY_LABELS:
        return PRIMARY_LABELS[name]
    if name == "attention":
        return _("Needs attention")
    return LOOKUPS[name].label


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
        "filterNames": list(FILTER_NAMES),
        "filterLabels": {name: str(_filter_label(name)) for name in FILTER_NAMES},
        "chipsText": {
            "title": str(_("Filters")),
            "clearAll": str(_("Clear all")),
            "remove": str(_("Remove this filter")),
        },
        "pageSize": DEFAULT_PAGE_SIZE,
        "emptyText": str(_("No issues match these filters.")),
        "counterText": str(_("issues")),
        "openText": str(_("Open")),
        "issueUrlPrefix": reverse("datadesk:issues"),
        "initialPage": initial_page,
        "focus": focus,
        "texts": {
            "deleteSeries": str(_("Delete this series")),
            "deleting": str(_("Deleting…")),
            "deleteFailed": str(_("The series was not deleted.")),
            "previewFailed": str(_("The preview could not be loaded.")),
            "confirmYear": str(_("Type %(year)s to confirm")),
            "deleted": str(_("The series was deleted.")),
        },
    }
