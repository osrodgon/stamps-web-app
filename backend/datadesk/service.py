"""Read layer for DataDesk.

Everything the maintenance UI displays goes through these functions: the
workbench grid (S8), the stamp grid of the workspace (S10) and the "needs
attention" queues of the dashboard (S20). Keeping the querysets here means the
query count is decided once, not per view.
"""
from django.db.models import Count, F, Q, QuerySet

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


def issue_queryset() -> QuerySet[Issue]:
    """Returns the workbench rows: issues with their lookups and stamp count.

    Ordering is chronological — year, then emission date, then name — with the
    undated series at the end. That is a default, not a rule: S8 lets the user
    sort by any column.
    """
    return (
        Issue.objects.select_related(*ISSUE_SELECT_RELATED)
        .annotate(stamp_count=Count("stamps"))
        .order_by("year__year", F("date").asc(nulls_last=True), "name")
    )


def stamp_queryset(issue_id: int) -> QuerySet[Stamp]:
    """Returns the stamps of one issue, colors included, without N+1."""
    return (
        Stamp.objects.filter(issue_id=issue_id)
        .prefetch_related("colors")
        .order_by("id")
    )


def missing_data_report() -> dict[str, int]:
    """Counts the rows that still need work, for the dashboard queues.

    ``image`` may be NULL or an empty string, so both are checked. ``face_value``
    cannot be NULL (the column has no ``null=True``), so the only way to be
    missing is an empty string.
    """
    stamps = Stamp.objects.all()

    return {
        "issues_without_country": Issue.objects.filter(country__isnull=True).count(),
        "issues_without_date": Issue.objects.filter(date__isnull=True).count(),
        "issues_without_stamps": Issue.objects.filter(stamps__isnull=True).count(),
        "stamps_without_colors": stamps.filter(colors__isnull=True).count(),
        "stamps_without_face_value": stamps.filter(face_value="").count(),
        "stamps_without_image": stamps.filter(
            Q(image__isnull=True) | Q(image="")
        ).count(),
    }
