"""The audit trail, read back: what happened, and how to undo it.

Every commit written since S6 is one ``DataDeskChange`` row per touched object,
grouped by ``commit_id``. This module turns those groups into something a person
can read, and undoes one of them in a single transaction.

Undoing is not symmetric, and that is the whole difficulty:

- a ``create`` is deleted, **children first**, because the cascade would
  otherwise take rows whose own revert has not run yet;
- a ``delete`` is recreated with its **original id**, parents first, because
  whatever pointed at it expects that id;
- an ``update`` gets its full ``before`` snapshot written back, not a diff, and
  ``updated_at`` by hand because ``auto_now`` does not fire on ``update()``;
- a ``merge`` cannot be undone at all: the audit kept the counts, not the rows
  that moved.

What no revert can give back: the ``CollectionItem`` rows the cascade deleted
with a series or a stamp. The catalogue comes back; who owned those stamps does
not.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from math import ceil
from typing import Any

from django.apps import apps
from django.db import IntegrityError, models, transaction
from django.db.models import Count, Min
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext

from datadesk.audit import model_label, new_commit_id, record, snapshot
from datadesk.models import DataDeskChange
from datadesk.registry import LOOKUPS
from datadesk.write import CLONED_FROM_KEY, WriteError

DEFAULT_PAGE_SIZE = 10
"""Commits per page: one commit can be forty rows, so ten is already a lot."""

MERGE = "merge"

OPERATION_LABELS = {
    "create": _("created"),
    "update": _("updated"),
    "delete": _("deleted"),
    MERGE: _("merged"),
}
"""One verb per operation, translated once."""

UNDO_LABELS = {
    "create": _("will be deleted"),
    "update": _("will be restored"),
    "delete": _("will be created again"),
}
"""What reverting does to a row, in the words the dialog uses."""

LOOKUP_LABELS: dict[str, Any] = {
    model_label(lookup.model): lookup.label for lookup in LOOKUPS.values()
}
"""The registry's label for each lookup model, so the log names tables."""

MODEL_RANK: dict[str, int] = {
    model_label(lookup.model): 0 for lookup in LOOKUPS.values()
} | {"issues_api.Issue": 1, "stamps_api.Stamp": 2}
"""Dependency order: lookups first, then series, then stamps.

Recreating runs it forwards (a stamp needs its series), deleting runs it
backwards (the series would cascade the stamp that is still to be deleted).
"""


@dataclass(frozen=True)
class ChangeView:
    """One row of the log, as the screen reads it.

    Attributes:
        object_label: Translated table name and id (``Series #12``).
        operation_label: ``created``, ``updated``, ``deleted`` or ``merged``.
        undo_label: What reverting does to this row.
        fields: Translated names of the columns that changed.
    """

    object_label: str
    operation_label: str
    undo_label: str
    fields: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class CommitView:
    """One commit: its rows, who made it and whether it can be undone.

    Attributes:
        commit_id: Id shared by the rows.
        when: Timestamp of the first row.
        user: Actor, or the anonymous placeholder.
        summary: "12 objects" in the active language.
        rows: The rows, in dependency order for reading.
        state: ``reversible``, ``merged`` or ``reverted``.
        state_label: That state, translated.
        reverted_at: When it was undone, if it was.
        touches_collections: Whether reverting it recreates catalogue rows whose
            ``CollectionItem`` rows are gone for good.
    """

    commit_id: uuid.UUID
    when: datetime
    user: str
    summary: str
    rows: list[ChangeView]
    state: str
    state_label: str
    reverted_at: datetime | None = None
    touches_collections: bool = False


@dataclass(frozen=True)
class ActivityPage:
    """One page of commits.

    Attributes:
        commits: The commits, newest first.
        page: Page served, clamped to the real range.
        last_page: Last page with commits.
        total: Commits in the log.
    """

    commits: list[CommitView]
    page: int
    last_page: int
    total: int


@dataclass(frozen=True)
class RevertResult:
    """What a revert did.

    Attributes:
        commit_id: Id of the new commit that undoes the old one.
        reverted: Id of the commit that was undone.
        undone: Rows undone.
    """

    commit_id: uuid.UUID
    reverted: uuid.UUID
    undone: int


def activity_page(
    page: int = 1,
    size: int = DEFAULT_PAGE_SIZE,
    labels: dict[str, str] | None = None,
    anonymous: str = "",
) -> ActivityPage:
    """Returns one page of commits, newest first.

    Pagination is by commit, not by row: forty rows are one decision, and a page
    cut in the middle of a commit would offer half a revert.

    Args:
        page: Page asked for, clamped.
        size: Commits per page.
        labels: Translated names of the columns, from the editor's own
            definitions; a missing one falls back to the column name.
        anonymous: How to name a commit made without a user.
    """
    names = labels or {}
    grouped = (
        DataDeskChange.objects.values("commit_id")
        .annotate(first=Min("created_at"), rows=Count("pk"))
        .order_by("-first", "-commit_id")
    )

    size = max(1, size)
    total = grouped.count()
    last_page = max(1, ceil(total / size))
    page = max(1, min(page, last_page))
    groups = list(grouped[(page - 1) * size : page * size])

    commits = _commit_views(groups, names, anonymous)
    return ActivityPage(commits=commits, page=page, last_page=last_page, total=total)


def changed_fields(
    before: dict[str, Any] | None, after: dict[str, Any] | None
) -> list[str]:
    """Returns the columns a row actually changed.

    ``cloned_from`` is skipped: it is provenance S17 writes into the ``after`` of
    a clone, not a column, and the log must not present it as one.
    """
    if before is None:
        return [name for name in (after or {}) if name != CLONED_FROM_KEY]
    if after is None:
        return list(before)
    return [name for name in after if before.get(name) != after.get(name)]


def revert_commit(commit_id: uuid.UUID, user) -> RevertResult:
    """Undoes one commit, all of it or nothing.

    Args:
        commit_id: The commit to undo.
        user: Actor, stored in the audit trail of the revert.

    Returns:
        The new commit id and how many rows were undone.

    Raises:
        WriteError: 404 for an unknown commit, 409 when it cannot be undone
            (a merge, already reverted, an object changed since, or a collision
            while recreating).
    """
    with transaction.atomic():
        rows = list(
            DataDeskChange.objects.select_for_update()
            .filter(commit_id=commit_id)
            .order_by("pk")
        )
        if not rows:
            raise WriteError("This commit does not exist.", status=404)

        _check_revertible(rows)
        _check_unchanged(rows)

        new_commit = new_commit_id()
        for row in revert_order(rows):
            _undo(row, commit_id, new_commit, user)

        DataDeskChange.objects.filter(pk__in=[row.pk for row in rows]).update(
            reverted_at=timezone.now()
        )

    return RevertResult(commit_id=new_commit, reverted=commit_id, undone=len(rows))


def revert_order(rows: list[DataDeskChange]) -> list[DataDeskChange]:
    """Returns the rows in the order their undo has to run.

    Recreations first, parents before children; updates in between; deletions
    last, children before parents. The dependency order is the whole point: the
    other way round, deleting a series cascades the stamps whose own revert is
    still pending and the transaction fails on a row that is already gone.
    """
    deleted = sorted(
        (row for row in rows if row.operation == "delete"),
        key=lambda row: (MODEL_RANK.get(row.model_label, 9), row.pk),
    )
    updated = sorted(
        (row for row in rows if row.operation == "update"),
        key=lambda row: (MODEL_RANK.get(row.model_label, 9), row.pk),
    )
    created = sorted(
        (row for row in rows if row.operation == "create"),
        key=lambda row: (MODEL_RANK.get(row.model_label, 9), row.pk),
        reverse=True,
    )
    return deleted + updated + created


def _commit_views(
    groups: list[dict[str, Any]],
    labels: dict[str, str],
    anonymous: str,
) -> list[CommitView]:
    """Builds the screen's commits out of the grouped ids, in one extra query."""
    ids = [group["commit_id"] for group in groups]
    rows = (
        DataDeskChange.objects.filter(commit_id__in=ids)
        .select_related("user")
        .order_by("created_at", "pk")
    )
    by_commit: dict[uuid.UUID, list[DataDeskChange]] = {key: [] for key in ids}
    for row in rows:
        by_commit[row.commit_id].append(row)

    commits: list[CommitView] = []
    for group in groups:
        commit_rows = by_commit[group["commit_id"]]
        if not commit_rows:
            continue
        reverted_at = max(
            (row.reverted_at for row in commit_rows if row.reverted_at),
            default=None,
        )
        merged = any(row.operation == MERGE for row in commit_rows)
        state = "merged" if merged else ("reverted" if reverted_at else "reversible")
        commits.append(
            CommitView(
                commit_id=group["commit_id"],
                when=commit_rows[0].created_at,
                user=(
                    commit_rows[0].user.get_username()
                    if commit_rows[0].user
                    else anonymous
                ),
                summary=ngettext(
                    "%(count)s object", "%(count)s objects", len(commit_rows)
                )
                % {"count": len(commit_rows)},
                rows=[_change_view(row, labels) for row in revert_order(commit_rows)],
                state=state,
                state_label=_state_label(state, reverted_at),
                reverted_at=reverted_at,
                touches_collections=any(
                    row.operation in {"create", "delete"}
                    and row.model_label in {"issues_api.Issue", "stamps_api.Stamp"}
                    for row in commit_rows
                ),
            )
        )
    return commits


def _change_view(row: DataDeskChange, labels: dict[str, str]) -> ChangeView:
    """Turns one audit row into the line the screen shows."""
    return ChangeView(
        object_label=f"{_object_name(row)} #{row.object_id}",
        operation_label=str(OPERATION_LABELS.get(row.operation, row.operation)),
        undo_label=str(UNDO_LABELS.get(row.operation, "")),
        fields=[
            labels.get(name, name) for name in changed_fields(row.before, row.after)
        ],
    )


def _object_name(row: DataDeskChange) -> str:
    """Returns the translated name of the table a row belongs to."""
    if row.model_label == "issues_api.Issue":
        return str(_("Series"))
    if row.model_label == "stamps_api.Stamp":
        return str(_("Stamp"))
    label = LOOKUP_LABELS.get(row.model_label)
    return str(label) if label is not None else row.model_label


def _state_label(state: str, reverted_at: datetime | None) -> str:
    """Returns the badge text of a commit."""
    if state == "merged":
        return str(_("Not revertible: it contains a merge"))
    if state == "reverted" and reverted_at is not None:
        moment = timezone.localtime(reverted_at).strftime("%Y-%m-%d %H:%M")
        return str(_("Reverted on %(when)s")) % {"when": moment}
    return str(_("Revertible"))


def _check_revertible(rows: list[DataDeskChange]) -> None:
    """Refuses the commits no revert can honour."""
    if any(row.operation == MERGE for row in rows):
        raise WriteError(
            "A commit with a merge cannot be reverted: the log kept the counts, "
            "not the references that moved.",
            status=409,
        )
    if any(row.reverted_at for row in rows):
        raise WriteError("This commit was already reverted.", status=409)


def _check_unchanged(rows: list[DataDeskChange]) -> None:
    """Refuses to overwrite anything that moved after the commit."""
    for row in rows:
        model = _model(row.model_label)
        if model is None:
            raise WriteError(
                f"Unknown model in the log: {row.model_label}.", status=409
            )
        obj = model.objects.filter(pk=row.object_id).first()
        if obj is None:
            continue
        stamp = getattr(obj, "updated_at", None)
        if stamp is not None and stamp > row.created_at:
            raise WriteError(
                f"{_object_name(row)} #{row.object_id} changed after this commit.",
                status=409,
            )


def _undo(row: DataDeskChange, original: uuid.UUID, commit_id: uuid.UUID, user) -> None:
    """Undoes one row, writing the inverse change into the new commit."""
    model = _model(row.model_label)
    if model is None:
        raise WriteError(f"Unknown model in the log: {row.model_label}.", status=409)

    if row.operation == "create":
        obj = model.objects.filter(pk=row.object_id).first()
        if obj is None:
            raise WriteError(
                f"{_object_name(row)} #{row.object_id} is gone already.", status=409
            )
        before = snapshot(obj)
        obj.delete()
        record(commit_id, user, obj, "delete", before, None, reverts_commit_id=original)
        return

    if row.operation == "delete":
        _recreate(row, model, commit_id, original, user)
        return

    _restore(row, model, commit_id, original, user)


def _recreate(
    row: DataDeskChange,
    model: type[models.Model],
    commit_id: uuid.UUID,
    original: uuid.UUID,
    user,
) -> None:
    """Puts a deleted row back with its id, its foreign keys and its colours."""
    data = dict(row.before or {})
    colours = data.pop("colors", None)
    try:
        with transaction.atomic():
            obj = model(id=row.object_id, **data)
            obj.save(force_insert=True)
            if colours is not None and hasattr(obj, "colors"):
                obj.colors.set(colours)
    except IntegrityError as error:
        raise WriteError(
            f"{_object_name(row)} #{row.object_id} could not be recreated: "
            "its id or a unique value is taken.",
            status=409,
        ) from error

    record(
        commit_id, user, obj, "create", None, snapshot(obj), reverts_commit_id=original
    )


def _restore(
    row: DataDeskChange,
    model: type[models.Model],
    commit_id: uuid.UUID,
    original: uuid.UUID,
    user,
) -> None:
    """Writes the whole ``before`` snapshot back onto the row."""
    obj = model.objects.filter(pk=row.object_id).first()
    if obj is None:
        raise WriteError(f"{_object_name(row)} #{row.object_id} is gone.", status=409)

    before = snapshot(obj)
    data = dict(row.before or {})
    colours = data.pop("colors", None)
    if any(field.name == "updated_at" for field in model._meta.concrete_fields):
        # `update()` never fires `auto_now`, and S12's conflict check reads it.
        data["updated_at"] = timezone.now()

    model.objects.filter(pk=obj.pk).update(**data)
    obj.refresh_from_db()
    if colours is not None and hasattr(obj, "colors"):
        obj.colors.set(colours)

    record(
        commit_id,
        user,
        obj,
        "update",
        before,
        snapshot(obj),
        reverts_commit_id=original,
    )


def _model(label: str) -> type[models.Model] | None:
    """Returns the model behind ``app_label.ModelName``, or ``None``."""
    try:
        return apps.get_model(label)
    except LookupError:
        return None
