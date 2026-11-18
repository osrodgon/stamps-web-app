"""Admin registration for DataDesk's audit trail.

The trail is read-only: rows are written by the app, never by hand, and the
activity screen (S21) will read from here too.
"""
from django.contrib import admin

from datadesk.models import DataDeskChange


@admin.register(DataDeskChange)
class DataDeskChangeAdmin(admin.ModelAdmin):
    """Read-only list of audit rows, ordered newest first."""

    list_display = (
        "created_at",
        "operation",
        "model_label",
        "object_id",
        "user",
        "commit_id",
    )
    list_filter = ("operation", "model_label")
    search_fields = ("model_label", "object_id")
    date_hierarchy = "created_at"
    readonly_fields = (
        "created_at",
        "user",
        "commit_id",
        "model_label",
        "object_id",
        "operation",
        "before",
        "after",
        "reverted_at",
        "reverts_commit_id",
    )

    def has_add_permission(self, request) -> bool:
        """Audit rows are never created by hand."""
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        """Audit rows are never edited."""
        return False

    def has_delete_permission(self, request, obj=None) -> bool:
        """Audit rows are never deleted: the trail must stay intact."""
        return False
