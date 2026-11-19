"""JSON endpoint feeding the workbench grid.

Plain Django returning JSON, not a DRF view: DataDesk is not part of the public
API and nothing here belongs under ``/api/v1/``.
"""
from django.http import HttpRequest, JsonResponse
from django.urls import reverse
from django.views import View

from datadesk.mixins import DataDeskAccessMixin
from datadesk.service import (
    ATTENTION_KEYS,
    DEFAULT_PAGE_SIZE,
    DEFAULT_SORT,
    IssueFilters,
    issue_page,
)


class IssueGridJsonView(DataDeskAccessMixin, View):
    """Returns one page of issues for Tabulator."""

    def get(self, request: HttpRequest, *args, **kwargs) -> JsonResponse:
        """Parses the flat query parameters and returns the page as JSON."""
        filters = IssueFilters(
            year_min=_int(request, "year_min"),
            year_max=_int(request, "year_max"),
            q=request.GET.get("q", "").strip(),
            country=_int(request, "country"),
            stamp_type=_int(request, "stamp_type"),
            attention=_attention(request),
        )
        field, direction = _sort(request)

        page = issue_page(
            filters,
            sort=field,
            direction=direction,
            page=_int(request, "page") or 1,
            size=_int(request, "size") or DEFAULT_PAGE_SIZE,
        )

        return JsonResponse(
            {
                "last_page": page.last_page,
                "total": page.total,
                "page": page.page,
                "data": [_with_urls(row) for row in page.data],
            }
        )


def _with_urls(row: dict) -> dict:
    """Adds the two URLs the row's delete needs, so the script composes none.

    The grid pages on the server, so a row only exists in the answer to this
    request: the URLs travel with it, the same way the picture's does in the
    workspace.
    """
    return {
        **row,
        "dependencies_url": reverse("datadesk:issue_dependencies", args=[row["id"]]),
        "delete_url": reverse("datadesk:issue_delete", args=[row["id"]]),
    }


def _int(request: HttpRequest, name: str) -> int | None:
    """Returns an integer query parameter, or ``None`` when absent or invalid."""
    raw = request.GET.get(name, "").strip()
    if raw == "":
        return None
    try:
        return int(raw)
    except ValueError:
        return None


def _attention(request: HttpRequest) -> str:
    """Returns the "needs attention" key, ignoring anything not registered."""
    value = request.GET.get("attention", "").strip()
    return value if value in ATTENTION_KEYS else ""


def _sort(request: HttpRequest) -> tuple[str, str]:
    """Reads Tabulator's ``sort[0][field]`` / ``sort[0][dir]`` pair.

    Falls back to the default order when the parameters are missing.
    """
    field = request.GET.get("sort[0][field]", "").strip()
    direction = request.GET.get("sort[0][dir]", "").strip() or "asc"
    if field == "":
        return DEFAULT_SORT
    return field, direction
