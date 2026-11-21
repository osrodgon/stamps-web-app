"""Issue workspace: one series with its stamps, in both modes.

S10 renders what the database holds. S11 adds the dry ``mode=new`` on the same
template: the series form, the row generator that lives entirely in the browser
and the guards that stop the user from losing work that cannot be recovered.
S16 makes that form write: the page posts the series and its rows to
``/datadesk/issues/create`` and offers the "Create another" loop, which is a
fresh ``mode=new`` page prefilled by the server from the series just saved.
"""
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode

from django.db.models import QuerySet
from django.templatetags.static import static
from django.utils.formats import number_format
from django.utils import timezone
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView, TemplateView

from colors_api.models import Color
from datadesk.mixins import DataDeskAccessMixin
from datadesk.palette import tone_for
from datadesk.registry import LOOKUPS
from datadesk.rules import series_year_bounds
from datadesk.service import (
    Issue,
    IssueFilters,
    issue_queryset,
    neighbours_of_issue,
    stamp_rows,
)
from datadesk.texts import plural_forms
from datadesk.views.workbench import filters_from
from years_api.models import Year

STAMP_COLUMNS: tuple[dict[str, Any], ...] = (
    {
        "field": "edifil",
        "patch": "edifil_code",
        "title": _("Edifil"),
        "width": 94,
        "mono": True,
    },
    {
        "field": "fesofi",
        "patch": "fesofi_code",
        "title": _("Fesofi"),
        "width": 94,
        "mono": True,
    },
    {"field": "name", "patch": "name", "title": _("Name")},
    {
        "field": "description",
        "patch": "description",
        "title": _("Stamp description"),
        # Prose has no column: it would be an ellipsis in a 13px cell. The
        # field exists here so the change set, the review panel and the draft
        # treat it like every other value, and the preview pane owns the
        # widget the user actually types in.
        "hidden": True,
    },
    {"field": "face_value", "patch": "face_value", "title": _("Face value"),
     "width": 122},
    {"field": "colors", "title": _("Colors"), "width": 220},
    {
        "field": "total_printed",
        "patch": "total_printed",
        "editor": "number",
        # "Printed" on the header, "Total printed" everywhere a field is named:
        # the grid header is 11px and uppercase, and the long label was the one
        # that could not fit whatever the widths were.
        "title": _("Printed"),
        "label": _("Total printed"),
        "align": "right",
    },
    {
        "field": "mnh",
        "patch": "market_value_mnh",
        "title": _("MNH"),
        "align": "right",
        "width": 90,
        "money": True,
    },
    {
        "field": "used",
        "patch": "market_value_used",
        "title": _("Used"),
        "align": "right",
        "width": 90,
        "money": True,
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
     "kind": "number", "step": "0.01", "min": 0, "unit": "€"},
    {"name": "market_value_used", "label": _("Market value used"),
     "kind": "number", "step": "0.01", "min": 0, "unit": "€"},
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

REPEAT_FIELDS: tuple[str, ...] = (
    "country",
    "year",
    "stamp_type",
    "print_type",
    "printer",
    "artist",
    "paper_type",
    "perforation",
)
"""What the "Create another" loop keeps from the series just written.

It goes further than ``PREFILL_FIELDS`` on purpose, and the difference is the
source: the last issue may be from months ago, while this one was saved seconds
ago, so the next series almost certainly belongs to the same emission and shares
its classification and perforation. What identifies a series (name, date) and
what belongs to its set (print run, market values, free text) is cleared, because
carrying those over writes one series' numbers into another.
"""

FAST_FIELDS: tuple[str, ...] = ("edifil", "fesofi", "face_value", "colors")
"""The columns the fast row keeps: what a new stamp really needs.

Everything else is editable in ``mode=edit`` once the series exists, so typing
eight stamps does not mean tabbing through five columns of nulls.
"""

FILL_FIELDS: tuple[str, ...] = ("edifil", "fesofi")
"""The catalogue codes ``Fill series`` numbers.

Both are sequences over the same set — Edifil and Fesofi number it differently —
so the button advances whichever of the two has a first code and leaves the
other alone. A series with only one of them is the normal case, not an error.
"""

LOOKUP_FIELDS: tuple[str, ...] = (
    "country",
    "stamp_type",
    "print_type",
    "printer",
    "artist",
    "paper_type",
)
"""The reference fields of the strip, in display order.

They are typed with completion rather than chosen from a select: the page would
otherwise ship every artist and every colour with each series, and a table of
mechanically typed reference rows only grows.
"""

DEFAULT_NEW_ROWS = 4
MIN_NEW_ROWS = 1
MAX_NEW_ROWS = 100
BUFFER_SCHEMA = 1
"""Version of the draft a browser may keep for a series.

A change in shape (a field renamed, a new piece of state) bumps this: the old
draft is discarded with a notice instead of being restored into code that no
longer understands it.
"""

BACKUP_THRESHOLD = 20
"""Changes from which the panel offers a dump before committing.

Below it the risk of a bad batch is one edit, and writing a file for that is
noise; above it, a dump costs seconds and the rollback costs an afternoon.
"""

UNDO_LIMIT = 200
"""How many edits the browser keeps for Ctrl+Z. Beyond this the oldest goes."""

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
        """Adds the strip, the stamp rows, the arrows and the grid config."""
        context = super().get_context_data(**kwargs)
        issue: Issue = self.object
        rows = stamp_rows(issue)

        context.update(
            mode="edit",
            stamp_count=len(rows),
            prefill=None,
            form_fields=series_form_fields(series_values(issue)),
            config=workspace_config(rows, series=issue),
            navigation=navigation_for(issue, self.request),
        )
        return context


class IssueNewView(DataDeskAccessMixin, TemplateView):
    """Renders ``mode=new``, which now creates the series it shows.

    Two ways in, and they only differ in what the form starts with: ``?from=<id>``
    is the "Create another" loop and repeats the series just saved, while the
    plain URL copies the country and year of the last row. Nothing is kept in the
    browser: reloading discards the draft, and the loop works because the server
    renders the next page, not because the client remembered anything.
    """

    template_name = "datadesk/issue_workspace.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Adds the form, the prefill and a grid with no rows."""
        context = super().get_context_data(**kwargs)
        last = last_issue_prefill()
        source = self._source_issue()
        # The form starts from the series just saved when the loop asks for it,
        # and from the last issue otherwise. The button always means "use the
        # last issue", so it carries its own values and does not follow the
        # loop: the two are the same only because the loop usually continues
        # the row just written.
        values = repeat_values(source) if source is not None else last
        values = with_default_date(values or {})

        context.update(
            mode="new",
            prefill=last,
            prefill_label=prefill_summary(last),
            form_fields=series_form_fields(values),
            metadata=[],
            stamp_count=0,
            config=workspace_config([], mode="new", prefill=last),
        )
        return context

    def _source_issue(self) -> Issue | None:
        """Returns the series the loop continues, if the URL points at one.

        An unknown or unreadable id is not an error: it is a stale link, and the
        page falls back to the last issue instead of refusing to open.
        """
        raw = self.request.GET.get("from", "").strip()
        if raw == "":
            return None
        try:
            pk = int(raw)
        except ValueError:
            return None
        return issue_queryset().filter(pk=pk).first()


def navigation_for(issue: Issue, request: Any) -> dict[str, Any]:
    """Returns the previous/next links, the position and the way back.

    The neighbour is the series beside this one **in the workbench list the user
    came from**: the filters travel in the query string, so walking the 1987
    series without a country keeps walking those and not whatever has the next
    id. A series outside that list (a stale link, or one opened from the
    dashboard) falls back to the unfiltered order instead of leaving the arrows
    dead.
    """
    filters = filters_from(request)
    neighbours = neighbours_of_issue(issue.pk, filters)
    if not neighbours.found and filters.to_query():
        filters = IssueFilters()
        neighbours = neighbours_of_issue(issue.pk, filters)

    query = urlencode(filters.to_query())
    suffix = f"?{query}" if query else ""

    def url(pk: int | None) -> str:
        return "" if pk is None else reverse("datadesk:issue_workspace", args=[pk]) + suffix

    return {
        "previous": url(neighbours.previous),
        "next": url(neighbours.next),
        "position": _number(neighbours.position) if neighbours.found else "",
        "total": _number(neighbours.total),
        "back": reverse("datadesk:issues") + suffix,
        "query": suffix,
    }


def _number(value: int | None) -> str:
    """Returns a count grouped the way the active language groups numbers."""
    return "" if value is None else number_format(value, force_grouping=True)


def with_default_date(values: dict[str, Any]) -> dict[str, Any]:
    """Starts a current-year series with today's date.

    The date is what decides the year in the form, so an empty one would make the
    user type the year twice; a series that comes out now is dated now. A series
    from another year keeps the date empty on purpose: inventing a day is worse
    than leaving it blank, and that is exactly the inheritance the plan warned
    about. The year stays the only required field of the two.
    """
    if values.get("date"):
        return values
    year = values.get("year")
    if year is not None and year != timezone.localdate().year:
        return values
    return {**values, "date": timezone.localdate().isoformat()}


def prefill_summary(values: dict[str, Any] | None) -> str:
    """Returns what the "use last issue" button would put in the form.

    A button that says only "use the last issue" looks dead when the form
    already holds those values — which it does on load. Naming them turns it
    into a label the user can check against the fields.
    """
    if not values:
        return ""
    parts: list[str] = []
    country = values.get("country")
    if isinstance(country, dict) and country.get("label"):
        parts.append(str(country["label"]))
    if values.get("year") is not None:
        parts.append(str(values["year"]))
    return " · ".join(parts)


def repeat_values(issue: Issue) -> dict[str, Any]:
    """Returns the values the loop carries from the series just created.

    ``REPEAT_FIELDS`` explains which ones and why; the rest comes out empty
    because the form's default already is empty, and an empty field is what the
    writer turns into ``NULL``.
    """
    values: dict[str, Any] = {}
    for name in REPEAT_FIELDS:
        if name == "year":
            values["year"] = issue.year.year
        elif name == "perforation":
            values["perforation"] = issue.perforation or ""
        else:
            values[name] = getattr(issue, f"{name}_id") or ""
    return values


def last_issue_prefill() -> dict[str, Any] | None:
    """Returns the country and year a new series starts with, if any.

    The last issue is the highest id, not the newest year: the years are entered
    in batches and the row added most recently is the one being continued. A
    ``None`` means there is nothing to copy — a fresh database — and the page
    hides the button instead of showing it disabled.
    """
    last = (
        Issue.objects.order_by("-id")
        .values("year__year", "country_id", "country__name")
        .first()
    )
    if last is None:
        return None

    values: dict[str, Any] = {"year": last["year__year"]}
    if last["country_id"] is not None:
        # The form holds a name and sends an id, so both travel: the button has
        # to fill the field the way the user would have.
        values["country"] = {
            "value": last["country_id"],
            "label": last["country__name"],
        }
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
        raw = values.get(field["name"], "")
        # A lookup may arrive as ``{value, label}`` (the prefill carries both,
        # so the button can fill the box the way a person would) or as a bare
        # id, which then has to be resolved into the name it shows.
        paired = isinstance(raw, dict)
        field["value"] = raw.get("value", "") if paired else raw
        if field["kind"] == "year":
            low, high = series_year_bounds()
            field["min"], field["max"] = low, high
            field["options"] = year_suggestions()
        elif field["kind"] == "date":
            low, high = series_year_bounds()
            field["min"], field["max"] = f"{low}-01-01", f"{high}-12-31"
        elif "lookup" in field:
            field["value_label"] = (
                raw.get("label", "")
                if paired
                else lookup_label(field["lookup"], field["value"])
            )
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


def lookup_label(key: str, value: Any) -> str:
    """Returns the name of the selected lookup row, or ``""`` when unset.

    One query per field with a value: the strip ships the selected row's name,
    not the whole table, because the field completes as the user types and the
    options come from the search endpoint (S18).
    """
    if value in ("", None):
        return ""
    row = LOOKUPS[key].model.objects.filter(pk=value).first()
    if row is None:
        return ""
    return str(getattr(row, LOOKUPS[key].name_field))


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

    ``mode=new`` adds the element ids the script reads instead of hardcoding
    names the template owns, the row bounds, the fast-row columns and the colour
    options; the create URL and its texts travel too, so the script still holds
    no interface text. ``mode=edit`` adds the baseline of the series row and the
    texts the commit bar shows, with the same rule.
    """
    for row in rows:
        row["image_url"] = (
            reverse("datadesk:stamp_image", args=[row["id"]])
            if row.get("has_image")
            else None
        )
        if mode == "edit":
            # One URL per row instead of a template the script has to fill: the
            # grid already carries the picture's, so this is the same trick.
            row["dependencies_url"] = reverse(
                "datadesk:stamp_dependencies", args=[row["id"]]
            )
            row["delete_url"] = reverse("datadesk:stamp_delete", args=[row["id"]])

    config: dict[str, Any] = {
        "mode": mode,
        "data": rows,
        "lookups": lookup_endpoints(),
        "lookupLabels": lookup_labels(),
        "lookupText": {
            "create": str(_("+ Create \"%(name)s\"")),
            "created": str(_("Added to the list.")),
            "failed": str(_("The value could not be created.")),
            "unresolved": str(
                _("%(name)s is not a saved value yet. Use the + button to add it.")
            ),
            "newRows": str(_("New reference rows")),
            "savedRow": str(_("Saved now: reference rows are reused.")),
        },
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
            "rejected": str(_("The change was refused.")),
            "noChanges": str(_("Nothing changed.")),
            "saving": str(_("Saving…")),
            "backupSaved": str(_("Backup saved: %(file)s")),
            "backupFailed": str(_("The backup failed, so nothing was committed.")),
            "cloning": str(_("Cloning…")),
            "cloneFailed": str(_("The series was not cloned.")),
            "deleting": str(_("Deleting…")),
            "deleteFailed": str(_("The series was not deleted.")),
            "previewFailed": str(_("The preview could not be loaded.")),
            "commitFirst": str(_("Commit or discard the pending changes first.")),
            "confirmYear": str(_("Type %(year)s to confirm")),
            "deleteStamp": str(_("Delete this stamp")),
            "stampDeleted": str(_("The stamp was deleted.")),
            "stampDeleteFailed": str(_("The stamp was not deleted.")),
        }
        # The plural rules stay on the server: the browser only substitutes the
        # number into the form it was given, so Spanish and English keep their
        # own agreement.
        config["plurals"] = {
            "changes": plural_forms("%(count)s change", "%(count)s changes"),
            "recover": plural_forms(
                "%(count)s saved change", "%(count)s saved changes"
            ),
            "commit": plural_forms(
                "Commit %(count)s change", "Commit %(count)s changes"
            ),
        }
        config["fieldLabels"] = field_labels()
        config["modelLabels"] = {
            "issue": str(_("Series")),
            "stamp": str(_("Stamps")),
        }
        config["backupThreshold"] = BACKUP_THRESHOLD
        config["backupUrl"] = reverse("datadesk:backup")
        config["cloneUrl"] = reverse("datadesk:issue_clone", args=[series.pk])
        config["dependenciesUrl"] = reverse(
            "datadesk:issue_dependencies", args=[series.pk]
        )
        config["deleteUrl"] = reverse("datadesk:issue_delete", args=[series.pk])
        config["countBadge"] = "stamp-count"
        config["storageKey"] = f"datadesk:buffer:edit:{series.pk}"
        config["schemaVersion"] = BUFFER_SCHEMA
        config["undoLimit"] = UNDO_LIMIT

    if mode == "new":
        config.update(
            nameInput="field-name",
            rowsInput="row-count",
            countBadge="stamp-count",
            fillButton="fill-series",
            fastToggle="fast-row",
            createButton="create-button",
            createStatus="create-status",
            createdBar="created-bar",
            createdText="created-text",
            createdOpen="created-open",
            createdAgain="created-again",
            rowIdPrefix=NEW_ROW_PREFIX,
            rows=NewRowSettings().as_dict(),
            prefill=prefill,
            fastRow={"fields": list(FAST_FIELDS), "on": True},
            fillColumns=fill_columns(),
            colours=colour_options(),
            fieldLabels=field_labels(),
            createUrl=reverse("datadesk:issue_create"),
            newUrl=reverse("datadesk:issue_new"),
            texts={
                "saved": str(_("The series was created.")),
                "rejected": str(_("The series was not created.")),
                "saving": str(_("Saving…")),
                "fillNeedsFirst": str(
                    _("Type the first code to number the rest.")
                ),
                "fillImpossible": str(
                    _("The first %(column)s code has no number to continue from.")
                ),
                "createAnother": str(_("Create another in %(year)s")),
                "rowRefused": str(_("Stamp %(row)s: %(message)s")),
                "removeRow": str(_("Remove this row")),
                "yearFromDate": str(_("The year comes from the date.")),
            },
        )
    return config


def lookup_endpoints() -> dict[str, dict[str, str]]:
    """Returns the search and create URLs of every lookup the page types into.

    Both modes need them (the strip is the same form), and so does the colour
    dialog, which is why ``color`` is here without being a strip field.
    """
    return {
        key: {
            "search": reverse("datadesk:lookup_search", args=[key]),
            "create": reverse("datadesk:lookup_create", args=[key]),
        }
        for key in (*LOOKUP_FIELDS, "color")
    }


def lookup_labels() -> dict[str, str]:
    """Returns the translated name of each lookup, for the review panel."""
    return {key: str(LOOKUPS[key].label) for key in (*LOOKUP_FIELDS, "color")}


def fill_columns() -> list[dict[str, Any]]:
    """Returns the columns ``Fill series`` numbers, with the labels they show.

    The names and titles come from the grid definitions, so the script never
    hardcodes a column and a message can name the column it refused.
    """
    titles = {str(column["field"]): str(column["title"]) for column in STAMP_COLUMNS}
    return [{"field": field, "label": titles[field]} for field in FILL_FIELDS]


def colour_options() -> list[dict[str, Any]]:
    """Returns the colours a stamp may have, for the cell's multiple choice.

    The tone travels with each option so the chip the grid paints is the same
    pastel it paints in ``mode=edit``, where the row already carries the tone
    and the script knows no colour names.
    """
    return [
        {"value": color.pk, "label": color.name, "tone": tone_for(color.name)}
        for color in Color.objects.order_by("name")
    ]


def field_labels() -> dict[str, dict[str, str]]:
    """Returns the human label of every field a change set can touch.

    Built from the same definitions the form and the grid use, so the review
    panel cannot call a field something the editor does not. The script never
    hardcodes a column name.
    """
    return {
        "issue": {
            # The unit travels with the name: "1.20 → 1.30" says nothing about
            # what the number is worth.
            field["name"]: str(field["label"])
            + (f" ({field['unit']})" if field.get("unit") else "")
            for field in SERIES_FIELDS
        },
        "stamp": {
            str(column["patch"]): str(column.get("label", column["title"]))
            for column in STAMP_COLUMNS
            if "patch" in column
        },
    }


def _amount(value: Any) -> str:
    """Returns a decimal as the string the form shows, or ``""`` when unset."""
    return "" if value is None else str(value)
