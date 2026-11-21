"""Read layer for DataDesk.

Everything the maintenance UI displays goes through these functions: the
workbench grid (S8), the stamp grid of the workspace (S10) and the "needs
attention" queues of the dashboard (S20). Keeping the querysets here means the
query count is decided once, not per view.
"""
from dataclasses import dataclass, field
from decimal import Decimal
from math import ceil
from typing import Any

from django.db.models import Count, Exists, F, OuterRef, Q, QuerySet
from django.utils.translation import gettext_lazy as _

from datadesk.images import ImageIndex, has_picture, image_index
from datadesk.palette import tone_for
from datadesk.registry import get_lookup
from issues_api.models import Issue
from stamps_api.models import Stamp

ISSUE_SELECT_RELATED: tuple[str, ...] = (
    "year",
    "country",
    "stamp_type",
    "print_type",
    "printer",
    "artist",
    "paper_type",
)
"""The 7 foreign keys the workbench grid renders, in display order."""

REPORT_KEYS: tuple[str, ...] = (
    "issues_without_country",
    "issues_without_date",
    "issues_without_stamps",
    "stamps_without_colors",
    "stamps_without_face_value",
    "stamps_without_image",
)
"""The counters behind the "needs attention" selector."""

ATTENTION_KEYS: tuple[str, ...] = (
    "no_country",
    "no_date",
    "no_stamps",
    "stamps_without_colors",
    "stamps_without_face_value",
    "stamps_without_image",
)
"""The "needs attention" filters of the workbench.

Each one maps to a condition on the issue, so the grid and the badge tell the
same story. The last three are expressed with ``Exists`` instead of a join: a
join would multiply rows and break the stamp ``Count`` annotation.
"""

LOOKUP_SEARCH_LIMIT = 50
"""How many rows a lookup search returns: a hint, not a table."""

SORT_FIELDS: dict[str, str] = {
    "year": "year__year",
    "date": "date",
    "name": "name",
    "country": "country__name",
    "stamp_type": "stamp_type__name",
    "printer": "printer__name",
    "stamps": "stamp_count",
    "mnh": "market_value_mnh",
    "used": "market_value_used",
    "print_type": "print_type__name",
    "artist": "artist__name",
    "paper_type": "paper_type__name",
    "perforation": "perforation",
    "total_printed": "total_printed",
}
"""Sortable fields, mapped to their ORM path. Anything else is ignored."""

DEFAULT_SORT: tuple[str, str] = ("year", "asc")
DEFAULT_PAGE_SIZE = 100
MAX_PAGE_SIZE = 200

@dataclass(frozen=True)
class IssueFilters:
    """The filters the workbench can apply, as they arrive from the query string.

    Attributes:
        year_min: First year of the range, inclusive.
        year_max: Last year of the range, inclusive.
        q: Free text over the issue name.
        country: Country id.
        stamp_type: Stamp type id.
        attention: One of ``ATTENTION_KEYS``.
    """

    year_min: int | None = None
    year_max: int | None = None
    q: str = ""
    country: int | None = None
    stamp_type: int | None = None
    attention: str = ""

    def to_query(self) -> dict[str, Any]:
        """Returns the filters that are actually set, for rebuilding links."""
        values: dict[str, Any] = {}
        for name in ("year_min", "year_max", "q", "country", "stamp_type", "attention"):
            value = getattr(self, name)
            if value not in ("", None):
                values[name] = value
        return values


@dataclass(frozen=True)
class IssuePage:
    """One page of workbench rows, already shaped for the grid.

    Attributes:
        data: Serialized rows.
        total: Rows matching the filters.
        last_page: Last page number, at least 1.
        page: Page returned.
        size: Page size used.
    """

    data: list[dict[str, Any]] = field(default_factory=list)
    total: int = 0
    last_page: int = 1
    page: int = 1
    size: int = DEFAULT_PAGE_SIZE


def issue_queryset() -> QuerySet[Issue]:
    """Returns the workbench rows: issues with their lookups and stamp count.

    Ordering is chronological — year, then emission date, then name — with the
    undated series at the end. That is a default, not a rule: the grid lets the
    user sort by any column.
    """
    return (
        Issue.objects.select_related(*ISSUE_SELECT_RELATED)
        .annotate(stamp_count=Count("stamps"))
        .order_by("year__year", F("date").asc(nulls_last=True), "name")
    )


def filter_issues(queryset: QuerySet[Issue], filters: IssueFilters) -> QuerySet[Issue]:
    """Applies the workbench filters to an issue queryset."""
    if filters.year_min is not None:
        queryset = queryset.filter(year__year__gte=filters.year_min)
    if filters.year_max is not None:
        queryset = queryset.filter(year__year__lte=filters.year_max)
    if filters.q:
        queryset = queryset.filter(name__icontains=filters.q)
    if filters.country is not None:
        queryset = queryset.filter(country_id=filters.country)
    if filters.stamp_type is not None:
        queryset = queryset.filter(stamp_type_id=filters.stamp_type)

    if filters.attention == "stamps_without_image":
        # The only queue that is not a queryset condition: see ATTENTION_CONDITIONS.
        queryset = queryset.filter(pk__in=picture_gaps()[1])
    else:
        attention = ATTENTION_CONDITIONS.get(filters.attention)
        if attention is not None:
            queryset = queryset.filter(attention)

    return queryset


def sort_issues(
    queryset: QuerySet[Issue], sort: str, direction: str
) -> QuerySet[Issue]:
    """Orders by a whitelisted column; unknown fields fall back to the default."""
    path = SORT_FIELDS.get(sort)
    if path is None:
        return queryset.order_by(
            "year__year", F("date").asc(nulls_last=True), "name"
        )

    descending = direction.lower() == "desc"
    expression = F(path)
    if sort == "date":
        expression = F("date").desc(nulls_last=True) if descending else F("date").asc(
            nulls_last=True
        )
        return queryset.order_by(expression, "name")
    if sort == "year":
        return queryset.order_by(
            expression.desc() if descending else expression.asc(),
            F("date").asc(nulls_last=True),
            "name",
        )
    return queryset.order_by(expression.desc() if descending else expression.asc())


def issue_page(
    filters: IssueFilters,
    sort: str = DEFAULT_SORT[0],
    direction: str = DEFAULT_SORT[1],
    page: int = 1,
    size: int = DEFAULT_PAGE_SIZE,
) -> IssuePage:
    """Returns one page of workbench rows, ready to be serialized to JSON."""
    size = max(1, min(size, MAX_PAGE_SIZE))
    page = max(1, page)

    queryset = sort_issues(filter_issues(issue_queryset(), filters), sort, direction)
    total = queryset.count()
    last_page = max(1, ceil(total / size))
    page = min(page, last_page)
    offset = (page - 1) * size

    return IssuePage(
        data=[serialize_issue(issue) for issue in queryset[offset : offset + size]],
        total=total,
        last_page=last_page,
        page=page,
        size=size,
    )


def issue_positions(filters: IssueFilters | None = None) -> list[int]:
    """Returns the pks of the workbench list, in the order the grid shows them.

    The list is pks only — 2.500 integers, not the eight-table join the grid
    uses — and it is what both "which page is this series on" and "which series
    comes next" are built on: the neighbour of a series is the neighbour in this
    list, with the filters and order the user was looking at.
    """
    queryset = sort_issues(
        filter_issues(Issue.objects.all(), filters or IssueFilters()), *DEFAULT_SORT
    )
    return list(queryset.values_list("pk", flat=True))


def page_of_issue(
    issue_id: int,
    filters: IssueFilters | None = None,
    size: int = DEFAULT_PAGE_SIZE,
) -> int:
    """Returns the page the workbench shows an issue on, in its default order.

    Landing back on the workbench after a commit is only useful if the series is
    in front of the user, and the grid pages server-side: the answer needs the
    position of the row, not just its id.
    """
    size = max(1, min(size, MAX_PAGE_SIZE))
    pks = issue_positions(filters)
    try:
        position = pks.index(issue_id)
    except ValueError:
        return 1
    return position // size + 1


@dataclass(frozen=True)
class Neighbours:
    """The series either side of one, in the workbench order.

    Attributes:
        previous: Pk of the series before it, or ``None`` at the start.
        next: Pk of the series after it, or ``None`` at the end.
        position: 1-based position, or ``None`` when the series is not in the
            filtered list at all (a stale link, or arrived from the dashboard).
        total: How many series the list has.
    """

    previous: int | None
    next: int | None
    position: int | None
    total: int

    @property
    def found(self) -> bool:
        """Whether the series is in the list the arrows walk."""
        return self.position is not None


def neighbours_of_issue(
    issue_id: int, filters: IssueFilters | None = None
) -> Neighbours:
    """Returns the series before and after one, in the workbench order.

    Not ``id ± 1``: walking the 1987 series without a country should not jump to
    a 1994 one because the ids happen to be consecutive. The same pk list
    ``page_of_issue()`` walks answers both questions, in one query.
    """
    pks = issue_positions(filters)
    try:
        index = pks.index(issue_id)
    except ValueError:
        return Neighbours(previous=None, next=None, position=None, total=len(pks))

    return Neighbours(
        previous=pks[index - 1] if index > 0 else None,
        next=pks[index + 1] if index + 1 < len(pks) else None,
        position=index + 1,
        total=len(pks),
    )


def serialize_issue(issue: Issue) -> dict[str, Any]:
    """Turns an issue into the flat row the grid renders.

    Decimals travel as strings: the grid only displays them, and it avoids
    float drift between the query and the browser.
    """
    return {
        "id": issue.pk,
        "year": issue.year.year,
        "date": issue.date.isoformat() if issue.date else None,
        "name": issue.name,
        "country": issue.country.name if issue.country else None,
        "country_id": issue.country_id,
        "stamp_type": issue.stamp_type.name if issue.stamp_type else None,
        "stamp_type_id": issue.stamp_type_id,
        "print_type": issue.print_type.name if issue.print_type else None,
        "printer": issue.printer.name if issue.printer else None,
        "artist": issue.artist.name if issue.artist else None,
        "paper_type": issue.paper_type.name if issue.paper_type else None,
        "perforation": issue.perforation,
        "total_printed": issue.total_printed,
        "mnh": _decimal(issue.market_value_mnh),
        "used": _decimal(issue.market_value_used),
        "stamps": issue.stamp_count,
        "gaps": {
            "no_country": issue.country_id is None,
            "no_date": issue.date is None,
            "no_stamps": issue.stamp_count == 0,
        },
    }


def stamp_queryset(issue_id: int) -> QuerySet[Stamp]:
    """Returns the stamps of one issue, colors included, without N+1."""
    return (
        Stamp.objects.filter(issue_id=issue_id)
        .prefetch_related("colors")
        .order_by("id")
    )


def stamp_rows(issue: Issue) -> list[dict[str, Any]]:
    """Returns the stamps of an issue, ready for the workspace grid.

    The picture index is read once and shared by every row: the shared cache is
    a file, and asking it 57 times costs more than walking the folders.
    """
    index = image_index()
    return [
        serialize_stamp(stamp, issue, index=index)
        for stamp in stamp_queryset(issue.pk)
    ]


def serialize_stamp(
    stamp: Stamp, issue: Issue, index: ImageIndex | None = None
) -> dict[str, Any]:
    """Turns a stamp into the flat row the workspace grid renders.

    Nothing is inherited: every value shown belongs to the stamp. The series
    values describe the **set** (its print run, what the complete series is
    worth) and a stamp's describe the stamp, so an equal number is a
    coincidence, never a copy.

    Colours carry their tone as well as their name, so the chip keeps the same
    pastel everywhere without the script knowing any colour names.
    """
    return {
        "id": stamp.pk,
        "edifil": stamp.edifil_code or "",
        "fesofi": stamp.fesofi_code or "",
        "name": stamp.name,
        # The description has no column (prose in a 13px cell is an ellipsis);
        # it travels with the row so the preview pane can show and edit it.
        "description": stamp.description or "",
        "face_value": stamp.face_value,
        "colors": [
            {"name": name, "tone": tone_for(name)}
            for name in sorted(color.name for color in stamp.colors.all())
        ],
        "total_printed": stamp.total_printed,
        "mnh": _decimal(stamp.market_value_mnh),
        "used": _decimal(stamp.market_value_used),
        "has_image": has_picture(issue.year.year, stamp.fesofi_code, index),
        # The baseline the next write compares against: the grid sends it back
        # as ``expected_updated_at`` so a row changed in another tab is refused
        # instead of overwritten. Not a column — it travels as row data.
        "updated_at": stamp.updated_at.isoformat() if stamp.updated_at else None,
    }


ISSUES = "issues"
STAMPS = "stamps"
"""Which number a counter is about.

Three of the six queues count stamps and the workbench filters series, so those
cards carry both numbers instead of pretending the grid lost rows.
"""


@dataclass(frozen=True)
class Queue:
    """One "needs attention" card.

    Attributes:
        key: Counter in ``missing_data_report()``.
        attention: Filter value of the workbench that opens the same rows.
        label: Translated card title.
        unit: ``ISSUES`` or ``STAMPS``, what the counter counts.
    """

    key: str
    attention: str
    label: Any
    unit: str


QUEUES: tuple[Queue, ...] = (
    Queue(
        "issues_without_country",
        "no_country",
        _("Series with no country"),
        ISSUES,
    ),
    Queue("issues_without_date", "no_date", _("Series with no date"), ISSUES),
    Queue("issues_without_stamps", "no_stamps", _("Series with no stamps"), ISSUES),
    Queue(
        "stamps_without_colors",
        "stamps_without_colors",
        _("Stamps with no colour"),
        STAMPS,
    ),
    Queue(
        "stamps_without_face_value",
        "stamps_without_face_value",
        _("Stamps with no value"),
        STAMPS,
    ),
    Queue(
        "stamps_without_image",
        "stamps_without_image",
        _("Stamps with no picture"),
        STAMPS,
    ),
)
"""The six cards of the dashboard, in the order they are shown.

One entry per counter of the report, and the pair is what makes the card
honest: the counter says how many rows need work, the filter says where they
are. The mapping lives here, once, because the two names differ (``no_country``
against ``issues_without_country``) and a second copy of it in the template would
be a counter added in one place and forgotten in the other.
"""


@dataclass(frozen=True)
class QueueCard:
    """One queue with today's numbers.

    Attributes:
        key: Counter in the report.
        attention: Workbench filter that opens the rows.
        label: Translated card title.
        unit: What ``count`` counts.
        count: Rows that need attention.
        issues: Series holding those rows, for the stamp queues (else ``None``).
    """

    key: str
    attention: str
    label: str
    unit: str
    count: int
    issues: int | None = None


def dashboard_queues() -> list[QueueCard]:
    """Returns the six counters with the series count behind the stamp ones.

    The series count uses ``filter_issues``, the same function the workbench
    uses, so "412 series" on the card and the total of the filtered grid cannot
    disagree: they are the same query.
    """
    report = missing_data_report()
    cards: list[QueueCard] = []
    for queue in QUEUES:
        series = None
        if queue.unit == STAMPS:
            series = filter_issues(
                Issue.objects.all(), IssueFilters(attention=queue.attention)
            ).count()
        cards.append(
            QueueCard(
                key=queue.key,
                attention=queue.attention,
                label=str(queue.label),
                unit=queue.unit,
                count=report.get(queue.key, 0),
                issues=series,
            )
        )
    return cards


def picture_gaps() -> tuple[int, set[int]]:
    """Returns the stamps with no picture file, and the series holding them.

    The pictures are served from the mounted ``<year>/<code>.webp`` tree, not
    from ``Stamp.image`` (empty in every row of the real database), so "has a
    picture" is a lookup in the file index and not a column. The index is cached
    for a minute, so this is a scan of one column of ``Stamp`` and no disk.

    Both numbers come from the same walk on purpose: the counter on the
    dashboard and the rows the workbench filter returns are the same question,
    and they were answering it differently before S20.
    """
    index = image_index()
    series: set[int] = set()
    count = 0
    rows = Stamp.objects.values_list(
        "fesofi_code", "issue_id", "issue__year__year"
    )
    for code, issue_id, year in rows:
        if not has_picture(year, code, index):
            count += 1
            series.add(issue_id)
    return count, series


def missing_data_report() -> dict[str, int]:
    """Counts the rows that still need work, for the dashboard queues.

    ``stamps_without_image`` looks at the picture files, not at ``Stamp.image``:
    the column is empty in every row and the pictures live in the mounted
    folder, so the queue must count what the workspace can actually show.
    ``face_value`` cannot be NULL (the column has no ``null=True``), so the only
    way to be missing is an empty string.
    """
    without_picture, _ = picture_gaps()
    return {
        "issues_without_country": Issue.objects.filter(country__isnull=True).count(),
        "issues_without_date": Issue.objects.filter(date__isnull=True).count(),
        "issues_without_stamps": Issue.objects.filter(stamps__isnull=True).count(),
        "stamps_without_colors": Stamp.objects.filter(colors__isnull=True).count(),
        "stamps_without_face_value": Stamp.objects.filter(face_value="").count(),
        "stamps_without_image": without_picture,
    }


def search_lookups(
    key: str, query: str, limit: int = LOOKUP_SEARCH_LIMIT
) -> list[dict[str, Any]]:
    """Returns the lookup rows that match what was typed in a cell.

    The search runs on the server so a page never has to ship a whole table:
    the colours are 300 rows and the artists close to a hundred, which is too
    much to send with every series just to fill six dropdowns.

    Args:
        key: Registry key (``artist``, ``color``, ...).
        query: What the user typed. Empty returns the first rows, sorted, so
            opening a field proposes something instead of nothing.
        limit: How many rows come back; small on purpose, the list is a hint.

    Returns:
        ``{"value", "label"}`` per row, ready for a datalist.

    Raises:
        KeyError: If the key is not a registered lookup.
    """
    lookup = get_lookup(key)
    rows = lookup.model.objects.order_by(lookup.name_field)
    text = query.strip()
    if text:
        rows = rows.filter(**{f"{lookup.name_field}__icontains": text})

    return [
        {"value": row.pk, "label": str(getattr(row, lookup.name_field))}
        for row in rows[:limit]
    ]


def _decimal(value: Decimal | None) -> str | None:
    """Returns a decimal as string, or ``None`` when it is unset."""
    return None if value is None else str(value)


def _stamps_of_issue(**filters: Any) -> QuerySet[Stamp]:
    """Stamps of the issue being annotated, for the ``Exists`` conditions."""
    return Stamp.objects.filter(issue=OuterRef("pk"), **filters)


ATTENTION_CONDITIONS: dict[str, Q | Exists] = {
    "no_country": Q(country__isnull=True),
    "no_date": Q(date__isnull=True),
    "no_stamps": ~Exists(Stamp.objects.filter(issue=OuterRef("pk"))),
    "stamps_without_colors": Exists(_stamps_of_issue(colors__isnull=True)),
    "stamps_without_face_value": Exists(_stamps_of_issue(face_value="")),
}
"""The filters that are one queryset condition.

``stamps_without_image`` is deliberately absent: the pictures live in the
mounted folder and ``Stamp.image`` is empty in every row of the real database, so
that queue cannot be expressed in SQL — it is ``picture_gaps()`` below, and
``filter_issues`` applies it by hand.
"""
"""Filter condition for each "needs attention" key."""
