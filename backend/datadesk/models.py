"""Models owned by DataDesk.

The audit trail lives here, not in the public apps: it is bookkeeping for the
maintenance UI and nothing else reads it.
"""
from django.conf import settings
from django.db import models


class DataDeskChange(models.Model):
    """One row of the DataDesk audit trail.

    A commit is a group of rows sharing ``commit_id``: the change set is applied
    in a single transaction, so either the whole group lands or none of it does.

    Attributes:
        created_at (DateTimeField): When the change was written.
        user (ForeignKey): Actor. ``SET_NULL`` so deleting the user keeps history.
        commit_id (UUIDField): Groups the rows of one commit.
        model_label (CharField): ``app_label.ModelName`` of the touched row.
        object_id (BigIntegerField): Primary key of the touched row, if any.
        operation (CharField): ``create``, ``update``, ``delete`` or ``merge``.
        before (JSONField): Full snapshot before the change, or null on create.
        after (JSONField): Full snapshot after the change, or null on delete.
        reverted_at (DateTimeField): When this row's commit was reverted.
        reverts_commit_id (UUIDField): On revert rows, the commit they undo.
    """

    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    MERGE = "merge"
    OPERATIONS = (
        (CREATE, "create"),
        (UPDATE, "update"),
        (DELETE, "delete"),
        (MERGE, "merge"),
    )

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="datadesk_changes",
    )
    commit_id = models.UUIDField(db_index=True)
    model_label = models.CharField(max_length=64)
    object_id = models.BigIntegerField(null=True, blank=True)
    operation = models.CharField(max_length=8, choices=OPERATIONS)
    before = models.JSONField(null=True, blank=True)
    after = models.JSONField(null=True, blank=True)
    reverted_at = models.DateTimeField(null=True, blank=True)
    reverts_commit_id = models.UUIDField(null=True, blank=True)

    class Meta:
        verbose_name = "DataDesk change"
        verbose_name_plural = "DataDesk changes"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        """Returns a short human-readable label for the admin and logs."""
        return f"{self.operation} {self.model_label}#{self.object_id}"
