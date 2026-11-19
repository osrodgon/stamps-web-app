"""Audit writer for DataDesk.

``snapshot()`` turns a model instance into a JSON-safe dict of every field the
maintenance UI can edit, and ``record()`` appends one row to the trail. Callers
own the transaction: a commit is all or nothing, so S12 wraps the whole change
set and its audit rows in a single ``transaction.atomic()``.
"""
import uuid
from datetime import date, datetime, time
from decimal import Decimal
from typing import Any

from django.db import models

from datadesk.models import DataDeskChange

NON_SNAPSHOT_FIELDS = frozenset({"updated_at"})
"""Fields that are bookkeeping and never part of a change."""


def model_label(instance: models.Model) -> str:
    """Returns ``app_label.ModelName`` for an instance."""
    return f"{instance._meta.app_label}.{instance._meta.object_name}"


def new_commit_id() -> uuid.UUID:
    """Returns a fresh id for a change set."""
    return uuid.uuid4()


def snapshot(instance: models.Model) -> dict[str, Any]:
    """Returns the full, JSON-safe state of the editable fields of a row.

    Foreign keys are stored as ids, many-to-many values as a sorted list of ids,
    ``Decimal`` as a string (the API already ships decimals that way and it
    avoids float drift) and dates as ISO-8601. Non-editable fields such as ``id``
    or ``updated_at`` are left out: they are not part of a change.

    Args:
        instance: The row to snapshot. It must be saved (it is read from the DB
            for its many-to-many values).

    Returns:
        A dict that survives ``json.dumps`` / ``json.loads`` unchanged.
    """
    data: dict[str, Any] = {}

    for field in instance._meta.concrete_fields:
        if field.primary_key or not field.editable or field.name in NON_SNAPSHOT_FIELDS:
            continue
        # Keys use the attname (`issue_id`, not `issue`) so the snapshot can be
        # splatted straight back into the model: `Stamp(**snapshot)`.
        data[field.attname] = _encode(getattr(instance, field.attname))

    for field in instance._meta.many_to_many:
        if not field.editable:
            continue
        ids = getattr(instance, field.name).values_list("pk", flat=True)
        data[field.name] = sorted(ids)

    return data


def record(
    commit_id: uuid.UUID,
    user,
    instance: models.Model,
    op: str,
    before: dict[str, Any] | None,
    after: dict[str, Any] | None,
    *,
    reverts_commit_id: uuid.UUID | None = None,
) -> DataDeskChange:
    """Appends one row to the audit trail.

    Args:
        commit_id: Id shared by every row of the same commit.
        user: Actor, or ``None`` for anonymous/system writes.
        instance: The touched row (deleted rows included: ``pk`` is still set).
        op: One of ``create``, ``update``, ``delete`` or ``merge``.
        before: Snapshot before the change, or ``None`` on create.
        after: Snapshot after the change, or ``None`` on delete.
        reverts_commit_id: On a revert, the commit these rows undo. It is what
            S21's screen reads to say "reverted on …" and what keeps a revert
            from being reverted by mistake.

    Returns:
        The written ``DataDeskChange``.

    Raises:
        ValueError: If ``op`` is not one of the known operations.
    """
    if op not in dict(DataDeskChange.OPERATIONS):
        raise ValueError(f"Unknown DataDesk operation: {op!r}")

    actor = user if getattr(user, "is_authenticated", False) else None
    return DataDeskChange.objects.create(
        commit_id=commit_id,
        user=actor,
        model_label=model_label(instance),
        object_id=instance.pk,
        operation=op,
        before=before,
        after=after,
        reverts_commit_id=reverts_commit_id,
    )


def _encode(value: Any) -> Any:
    """Converts a field value into something ``json.dumps`` accepts."""
    if value is None:
        return None
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    if isinstance(value, models.Model):
        return value.pk
    if hasattr(value, "name"):  # FieldFile: keep the reference, not the content
        return value.name
    return value
