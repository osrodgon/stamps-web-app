"""The lookups screen and the operations behind it.

One module, because it is one screen: the eight reference tables are listed, one
of them is browsed, and its rows can be renamed, merged or deleted. The work is
in ``datadesk.lookups``; this is the HTTP and the words.
"""

from typing import Any

from django.http import HttpRequest, Http404, JsonResponse
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic import TemplateView

from datadesk.lookups import (
    DEFAULT_SIZE,
    NEXT_YEARS,
    MergeResult,
    create_next_years,
    delete_lookup,
    lookup_page,
    merge_lookups,
    rename_lookup,
)
from datadesk.mixins import DataDeskAccessMixin
from datadesk.registry import LOOKUPS, get_lookup
from datadesk.texts import plural_forms
from datadesk.views.envelope import JsonPostView, written
from datadesk.write import WriteError

TAB_ORDER = tuple(LOOKUPS)
"""The tabs in registry order: the years first, the classifications after."""


class LookupIndexView(DataDeskAccessMixin, TemplateView):
    """The eight reference tables, with their size, as links."""

    template_name = "datadesk/lookups_index.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Lists every lookup with how many rows it holds."""
        context = super().get_context_data(**kwargs)
        context["cards"] = [
            {
                "key": key,
                "label": lookup.label,
                "rows": lookup.model.objects.count(),
                "url": reverse("datadesk:lookups_table", args=[key]),
            }
            for key, lookup in LOOKUPS.items()
        ]
        return context


class LookupTableView(DataDeskAccessMixin, TemplateView):
    """One lookup: its rows, and the four things they can do."""

    template_name = "datadesk/lookups.html"

    def get(self, request: HttpRequest, *args, **kwargs) -> Any:
        """Refuses a key nobody registered, before rendering anything."""
        if kwargs["key"] not in LOOKUPS:
            raise Http404("Unknown lookup")
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Adds the tabs, the label and the configuration the grid reads."""
        context = super().get_context_data(**kwargs)
        key = kwargs.get("key") or self.kwargs["key"]
        lookup = get_lookup(key)
        context.update(
            key=key,
            label=lookup.label,
            is_years=key == "year",
            tabs=[
                {
                    "key": name,
                    "label": LOOKUPS[name].label,
                    "active": name == key,
                    "url": reverse("datadesk:lookups_table", args=[name]),
                }
                for name in TAB_ORDER
            ],
            config=lookup_config(key),
        )
        return context


class LookupRowsJsonView(DataDeskAccessMixin, View):
    """One page of a lookup, with the usage counts in the rows."""

    def get(self, request: HttpRequest, *args, **kwargs) -> JsonResponse:
        """Returns the page in the shape Tabulator's remote mode expects."""
        try:
            page = lookup_page(
                kwargs["key"],
                request.GET.get("q", ""),
                _int(request, "page") or 1,
                _int(request, "size") or DEFAULT_SIZE,
            )
        except KeyError:
            return JsonResponse(
                {"success": False, "message": "Unknown lookup"}, status=404
            )
        return JsonResponse(page.as_dict())


class LookupRenameJsonView(JsonPostView):
    """Renames one row; a name already taken answers 409 and its id."""

    def handle(
        self, payload: dict[str, Any], request: HttpRequest, *args, **kwargs
    ) -> JsonResponse:
        """Writes the new name and returns the row as the grid reads it."""
        row = rename_lookup(
            _key(kwargs["key"]), payload.get("id"), payload.get("name"), request.user
        )
        return written("Saved.", {"data": row})


class LookupDeleteJsonView(JsonPostView):
    """Deletes a row nobody points at."""

    def handle(
        self, payload: dict[str, Any], request: HttpRequest, *args, **kwargs
    ) -> JsonResponse:
        """Removes the row, or refuses with its usage count."""
        row = delete_lookup(_key(kwargs["key"]), payload.get("id"), request.user)
        return written("The row was deleted.", {"data": row})


class LookupMergeJsonView(JsonPostView):
    """Moves every reference from one row to another and deletes the first."""

    def handle(
        self, payload: dict[str, Any], request: HttpRequest, *args, **kwargs
    ) -> JsonResponse:
        """Merges the two rows and reports how many references moved."""
        result: MergeResult = merge_lookups(
            _key(str(payload.get("table", ""))),
            payload.get("from_id"),
            payload.get("to_id"),
            payload.get("keep_name_from"),
            request.user,
        )
        return written(
            f"Merged {result.moved} references.",
            result.as_dict(),
            commit_id=result.commit_id,
        )


class LookupNextYearsJsonView(JsonPostView):
    """Writes the years after the newest one."""

    def handle(
        self, payload: dict[str, Any], request: HttpRequest, *args, **kwargs
    ) -> JsonResponse:
        """Creates the years the screen asked for and reports how many are new."""
        created = create_next_years(payload.get("count", NEXT_YEARS))
        return written(f"Created {created} years.", {"created": created})


def lookup_config(key: str) -> dict[str, Any]:
    """Returns what the grid script needs: URLs, columns and every text.

    ``dataKey`` is the column the rename writes and the rows are sorted by;
    ``numeric`` tells the script to edit it as a number (the years). No UI text
    is hardcoded in the script: all of it travels here, translated.
    """
    lookup = get_lookup(key)
    return {
        "key": key,
        "nameField": lookup.name_field,
        "numeric": lookup.numeric,
        "rowsUrl": reverse("datadesk:lookup_rows", args=[key]),
        "renameUrl": reverse("datadesk:lookup_rename", args=[key]),
        "deleteUrl": reverse("datadesk:lookup_delete", args=[key]),
        "mergeUrl": reverse("datadesk:lookup_merge"),
        "nextYearsUrl": (
            reverse("datadesk:lookup_next_years") if key == "year" else None
        ),
        "nextYears": NEXT_YEARS,
        "pageSize": DEFAULT_SIZE,
        "texts": {
            "name": str(_("Name")),
            "usage": str(_("Used by")),
            "empty": str(_("No rows yet.")),
            "delete": str(_("Delete")),
            "inUse": str(_("In use: merge it into another row")),
            "merge": str(_("Merge two rows")),
            "keepName": str(_("Keep this name")),
            "mergeWarning": str(
                _("The references move for good: this cannot be undone. Back up first.")
            ),
            "confirmMerge": str(_("Merge and delete the other row")),
            "confirmDelete": str(_("Delete the row")),
            "nextYears": str(_("Create the next %(count)s years")),
            "search": str(_("Search")),
            "duplicate": str(
                _("That name already exists. Merge the two rows instead?")
            ),
            "saved": str(_("Saved.")),
            "deleted": str(_("The row was deleted.")),
            "failed": str(_("The change was refused.")),
            "selectTwo": str(_("Select exactly two rows to merge.")),
            "cancel": str(_("Cancel")),
            "close": str(_("Close")),
            "deleteTitle": str(_("Delete this row")),
            "removed": str(_("Source row: it disappears after the merge.")),
            "survivor": str(_("Surviving row: it keeps every reference.")),
        },
        "plurals": {
            "usage": plural_forms("Used by %(count)s row", "Used by %(count)s rows"),
            "rows": plural_forms("%(count)s row", "%(count)s rows"),
            "moved": plural_forms(
                "Moved %(count)s reference", "Moved %(count)s references"
            ),
            "created": plural_forms(
                "Created %(count)s year", "Created %(count)s years"
            ),
        },
    }


def _key(value: str) -> str:
    """Refuses a registry key nobody registered, as a 404."""
    if value not in LOOKUPS:
        raise WriteError("Unknown lookup.", status=404)
    return value


def _int(request: HttpRequest, name: str) -> int | None:
    """Returns an integer query parameter, or ``None`` when absent or invalid."""
    raw = request.GET.get(name, "").strip()
    if raw == "":
        return None
    try:
        return int(raw)
    except ValueError:
        return None
