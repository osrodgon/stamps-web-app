"""Write layer for DataDesk.

One entry point per decision, one transaction each:

- ``create_series()`` writes one issue with its nested stamps, all or nothing.
  A half-written series would be worse than a failure, so there is no per-row
  recovery here: the first bad stamp rolls the whole thing back.
- ``apply_changes()`` writes a batch of existing rows with a savepoint per row:
  forty corrections of unrelated rows should not be lost because one of them
  references a deleted colour. Rejections are reported, never raised.
- ``clone_series()`` copies a series and its stamps into a new one. A copy is a
  copy, not a re-entry: the values are read from the origin's rows, so the gaps
  (a stamp without a face value, one without a colour) travel to the copy for
  the user to fix there.
- ``delete_series()`` removes a series, its stamps and whatever the cascade
  takes. It is the only deletion path in DataDesk, and it checks the typed year
  itself instead of trusting the dialog that asked for it.

``create_lookup()`` is the last, small one: a lookup typed into a cell while
editing a series must not force a round trip through the lookup screen, and a
name that already exists is returned instead of failing.

The audit trail of S6 is written here, inside the same transaction, one
``DataDeskChange`` per touched row and one ``commit_id`` per request. Rows that
are rejected leave no trace because they were never written.

References are created implicitly when a series needs them (the year of a new
series is typed, not chosen) and are **not** audited: they are a side effect of
the series, they live inside its transaction, and reverting the series leaves an
unused row that is harmless and reusable.
"""

import uuid
from dataclasses import dataclass, field
from typing import Any

from django.core.exceptions import FieldDoesNotExist
from django.db import models, transaction
from django.utils.dateparse import parse_date, parse_datetime

from datadesk.audit import new_commit_id, record, snapshot
from datadesk.dependencies import (
    Dependencies,
    StampDependencies,
    series_dependencies,
    stamp_dependencies,
)
from datadesk.registry import Lookup, get_lookup
from datadesk.rules import series_year_bounds
from datadesk.service import issue_queryset
from issues_api.api.serializers.issue_request_serializer import IssueRequestSerializer
from issues_api.models import Issue
from stamps_api.api.serializers.stamp_request_serializer import StampRequestSerializer
from colors_api.models import Color
from stamps_api.models import Stamp
from years_api.models import Year

MAX_CHANGES = 500
"""A request larger than this is a bug in the client, not a batch of fixes."""

MODEL_ALIASES: dict[str, type[models.Model]] = {"issue": Issue, "stamp": Stamp}
"""The models a change set may touch, by the short name the client sends."""

SERIALIZERS: dict[type[models.Model], type] = {
    Issue: IssueRequestSerializer,
    Stamp: StampRequestSerializer,
}
"""Request serializers, used for validation only: no DRF view is involved."""

WRITABLE_OPS = frozenset({"create", "update"})
"""Operations ``apply_changes()`` accepts. Deletes go through S17's preview."""

IMAGE_ERROR = "Images are read-only in DataDesk."
"""Pictures are served from the frontend's tree, never uploaded from here."""

CLONED_FROM_KEY = "cloned_from"
"""Where a clone's audit row records the series it was copied from.

The snapshot stays a snapshot: this is provenance, not a field, and it only
appears in ``after`` of a ``create`` row. S21's revert deletes what a ``create``
wrote and never rebuilds a model from its ``after``, so the key can never reach
``Model(**snapshot)``.
"""

COPY_SKIP = frozenset({"updated_at"})
"""Columns a copy leaves out: the bookkeeping timestamp is stamped by its save."""


class WriteError(Exception):
    """A request-level failure: nothing is applied.

    Attributes:
        message: Text the client shows as the reason.
        status: HTTP status to answer with.
        errors: Field errors, shaped like the serializer's.
        extra: Extra top-level keys (``needs_confirmation`` for a delete).
    """

    def __init__(
        self,
        message: str,
        *,
        status: int = 400,
        errors: dict[str, Any] | None = None,
        extra: dict[str, Any] | None = None,
    ) -> None:
        """Stores the pieces the view turns into a JSON body."""
        super().__init__(message)
        self.message = message
        self.status = status
        self.errors = errors or {}
        self.extra = extra or {}


class RowRejected(Exception):
    """One row of a batch was refused; the rest of the batch still applies.

    Attributes:
        errors: Field errors for that row, shaped like the serializer's.
    """

    def __init__(self, errors: dict[str, Any]) -> None:
        """Stores the field errors of the refused row."""
        super().__init__("row rejected")
        self.errors = errors


class InvalidYear(ValueError):
    """A typed year is not a number or falls outside the allowed range."""


@dataclass(frozen=True)
class ApplyResult:
    """What ``apply_changes()`` did.

    Attributes:
        commit_id: Id shared by every audit row written.
        applied: Rows written.
        rejected: ``{"index", "errors"}`` per refused row, in request order.
        rows: ``{"index", "id", "updated_at"}`` per written row, so the client
            can keep editing without reloading.
    """

    commit_id: uuid.UUID
    applied: int = 0
    rejected: list[dict[str, Any]] = field(default_factory=list)
    rows: list[dict[str, Any]] = field(default_factory=list)

    @property
    def success(self) -> bool:
        """Whether the whole batch went through."""
        return not self.rejected

    def as_dict(self) -> dict[str, Any]:
        """Returns the keys this operation adds to the response envelope."""
        return {
            "applied": self.applied,
            "rejected": self.rejected,
            "data": {"rows": self.rows},
        }


@dataclass(frozen=True)
class CreatedSeries:
    """A series written by ``create_series()``.

    Attributes:
        commit_id: Id shared by every audit row written.
        issue: The series, with its primary key set.
        stamps: The stamps, in the order they arrived.
    """

    commit_id: uuid.UUID
    issue: Issue
    stamps: list[Stamp]

    def as_dict(self) -> dict[str, Any]:
        """Returns the ids the client needs to replace its temporary rows."""
        return {
            "applied": 1 + len(self.stamps),
            "rejected": [],
            "data": {
                "issue": row_ref(self.issue),
                "stamps": [row_ref(stamp) for stamp in self.stamps],
            },
        }


@dataclass(frozen=True)
class DeletedSeries:
    """A series removed by ``delete_series()``.

    Attributes:
        commit_id: Id shared by the audit rows of the deletion.
        issue_id: Primary key of the row that no longer exists.
        name: Its name, so the page can say what went.
        year: Its year, the value that had to be typed to confirm.
        dependencies: Stamps and collection items the cascade took with it.
    """

    commit_id: uuid.UUID
    issue_id: int
    name: str
    year: int
    dependencies: Dependencies

    def as_dict(self) -> dict[str, Any]:
        """Returns the identity that is gone and how much went with it."""
        return {
            "applied": 1 + self.dependencies.stamps,
            "rejected": [],
            "data": {
                "id": self.issue_id,
                "name": self.name,
                "year": self.year,
                **self.dependencies.as_dict(),
            },
        }


@dataclass(frozen=True)
class DeletedStamp:
    """A stamp removed by ``delete_stamp()``.

    Attributes:
        commit_id: Id of the audit row written.
        stamp_id: Primary key of the row that no longer exists.
        name: Its name, so the page can say what went.
        code: Edifil or Fesofi, whichever it had: the catalogue is how one
            stamp is told from another.
        dependencies: Collection items and siblings the deletion found.
    """

    commit_id: uuid.UUID
    stamp_id: int
    name: str
    code: str
    dependencies: StampDependencies

    def as_dict(self) -> dict[str, Any]:
        """Returns the identity that is gone and what went with it."""
        return {
            "applied": 1,
            "rejected": [],
            "data": {
                "id": self.stamp_id,
                "name": self.name,
                "code": self.code,
                **self.dependencies.as_dict(),
            },
        }


@dataclass(frozen=True)
class LookupResult:
    """A lookup row returned to a cell.

    Attributes:
        commit_id: Id of the commit, used when the row was created.
        lookup: Registry entry the value belongs to.
        row: The row itself, existing or new.
        created: Whether this request wrote it.
    """

    commit_id: uuid.UUID
    lookup: Lookup
    row: models.Model
    created: bool

    def as_dict(self) -> dict[str, Any]:
        """Returns what the autocomplete needs to pick the row."""
        return {
            "created": self.created,
            "data": {
                "id": self.row.pk,
                "name": lookup_name(self.lookup, self.row),
                "created": self.created,
            },
        }


def create_series(payload: dict[str, Any], user) -> CreatedSeries:
    """Creates one series with its stamps, or nothing at all.

    Args:
        payload: ``{"issue": {...}, "stamps": [{...}, ...]}``, as sent by the
            new-series workspace.
        user: Actor, stored in the audit trail.

    Returns:
        The created series and its stamps.

    Raises:
        WriteError: If the envelope, the series or any stamp is invalid. The
            transaction is rolled back, so nothing is written.
    """
    issue_payload, stamps_payload = _split_series_payload(payload)
    commit_id = new_commit_id()

    with transaction.atomic():
        issue = _create_issue(issue_payload, commit_id, user)
        stamps = [
            _create_stamp(stamp_payload, index, issue, commit_id, user)
            for index, stamp_payload in enumerate(stamps_payload)
        ]

    return CreatedSeries(commit_id=commit_id, issue=issue, stamps=stamps)


def clone_series(pk: int, overrides: dict[str, Any] | None, user) -> CreatedSeries:
    """Copies a series and its stamps, colours included, in one transaction.

    Copying is not re-entering: the values come from the origin's rows, not from
    a form, so a series with a gap (a stamp without a face value, one without a
    colour) is copied as it is. Those gaps are exactly what the copy is for
    fixing, and refusing to clone until they are filled would help nobody.

    The copy keeps the name and the catalogue codes. Renaming is a decision only
    the user can make, so the copy opens on the workspace and the name is theirs
    to change there — inventing "… (copy)" would put a string in the catalogue
    that nobody chose.

    Args:
        pk: Primary key of the series to copy.
        overrides: ``{"year": ..., "date": ...}``, both optional. A new year is
            the usual reason to clone a series; anything else is copied.
        user: Actor, stored in the audit trail.

    Returns:
        The copy with its stamps, in the origin's order.

    Raises:
        WriteError: If the series does not exist or an override is not valid.
    """
    origin = issue_queryset().filter(pk=pk).first()
    if origin is None:
        raise WriteError("The series does not exist.", status=404)

    values = _clone_overrides(overrides)
    year = _clone_year(origin, values)
    sources = list(
        Stamp.objects.filter(issue=origin).prefetch_related("colors").order_by("pk")
    )
    commit_id = new_commit_id()

    with transaction.atomic():
        fields = _copy_fields(origin, Issue)
        fields["year_id"] = year.pk
        if "date" in values:
            fields["date"] = values["date"]
        issue = Issue.objects.create(**fields)
        record(
            commit_id,
            user,
            issue,
            "create",
            None,
            {**snapshot(issue), CLONED_FROM_KEY: origin.pk},
        )
        stamps = [_copy_stamp(source, issue, commit_id, user) for source in sources]

    return CreatedSeries(commit_id=commit_id, issue=issue, stamps=stamps)


def _copy_stamp(source: Stamp, issue: Issue, commit_id: uuid.UUID, user) -> Stamp:
    """Copies one stamp and its colours under the same audit commit."""
    stamp = Stamp.objects.create(
        issue=issue, **_copy_fields(source, Stamp, skip={"issue"})
    )
    stamp.colors.set([color.pk for color in source.colors.all()])
    record(commit_id, user, stamp, "create", None, snapshot(stamp))
    return stamp


def _copy_fields(
    obj: models.Model,
    model: type[models.Model],
    skip: frozenset[str] | set[str] = frozenset(),
) -> dict[str, Any]:
    """Returns a row's column values, ready to be inserted as a new row.

    Keys are attnames (``year_id``, not ``year``), so the dict splats straight
    into the model and no lookup has to be resolved a second time. The primary
    key, the bookkeeping timestamp and the caller's ``skip`` stay out.
    """
    fields: dict[str, Any] = {}
    for field in model._meta.concrete_fields:
        if field.primary_key or field.attname in COPY_SKIP:
            continue
        if field.name in skip or field.attname in skip:
            continue
        fields[field.attname] = getattr(obj, field.attname)
    return fields


def _clone_overrides(overrides: Any) -> dict[str, Any]:
    """Reads the two values a clone may change, and validates them.

    Anything else in the body is ignored: the client sends the year it wants
    and, occasionally, the date; a typo in a third key is not worth a refusal
    when the copy is otherwise complete.
    """
    if overrides in (None, ""):
        return {}
    if not isinstance(overrides, dict):
        raise WriteError(
            "The overrides must be an object.",
            errors={"overrides": ["Expected an object."]},
        )

    values: dict[str, Any] = {}
    if overrides.get("year") not in (None, ""):
        values["year"] = overrides["year"]

    if "date" in overrides:
        raw = overrides["date"]
        if raw in (None, ""):
            values["date"] = None
        else:
            moment = parse_date(str(raw))
            if moment is None:
                raise WriteError(
                    "The date is not valid.",
                    errors={"date": ["Use a date like 1987-05-12."]},
                )
            values["date"] = moment

    return values


def _clone_year(origin: Issue, values: dict[str, Any]) -> Year:
    """Returns the year row of the copy: the origin's, or the one asked for."""
    if "year" not in values:
        return origin.year
    try:
        return resolve_year(values["year"])
    except InvalidYear as error:
        raise WriteError(
            "The year is not valid.", errors={"year": [str(error)]}
        ) from error


def apply_changes(changes: Any, user) -> ApplyResult:
    """Applies a batch of ``create``/``update`` rows, one savepoint each.

    Args:
        changes: The ``changes`` list of the request, unvalidated.
        user: Actor, stored in the audit trail.

    Returns:
        How many rows were written and which ones were refused.

    Raises:
        WriteError: If the envelope is unusable (not a list, unknown model or
            operation, too many rows, a ``delete``). Nothing is applied.
    """
    rows = _check_batch(changes)
    commit_id = new_commit_id()
    applied = 0
    rejected: list[dict[str, Any]] = []
    written: list[dict[str, Any]] = []

    with transaction.atomic():
        for index, change in enumerate(rows):
            try:
                with transaction.atomic():
                    obj = _apply_row(change, commit_id, user)
            except RowRejected as rejection:
                rejected.append({"index": index, "errors": rejection.errors})
            else:
                applied += 1
                written.append({"index": index, **row_ref(obj)})

    return ApplyResult(
        commit_id=commit_id, applied=applied, rejected=rejected, rows=written
    )


def delete_series(pk: int, confirmation: Any, user) -> DeletedSeries:
    """Deletes a series, its stamps and everything the cascade takes.

    The typed year is compared here, not in the browser: the dialog is a
    courtesy, this check is the one that decides. The dependency counts are also
    recomputed inside the transaction, because the preview on screen may be
    minutes old and a number that grew is worse than no number.

    Every stamp and the series get their own audit row, so S21 can rebuild them
    with their original ids — the ``CollectionItem`` rows the cascade removes are
    gone for good, and the dialog says so.

    Args:
        pk: Primary key of the series.
        confirmation: What the user typed; it must be the series' year.
        user: Actor, stored in the audit trail.

    Returns:
        What was deleted and what went with it.

    Raises:
        WriteError: 404 when the series does not exist, 400 when the typed year
            does not match.
    """
    commit_id = new_commit_id()

    with transaction.atomic():
        issue = Issue.objects.select_for_update().filter(pk=pk).first()
        if issue is None:
            raise WriteError("The series does not exist.", status=404)

        year = issue.year.year
        typed = "" if confirmation is None else str(confirmation).strip()
        if typed != str(year):
            message = f"Type the year of the series to confirm ({year})."
            raise WriteError(
                "The series was not deleted.", errors={"confirm": [message]}
            )

        dependencies = series_dependencies(issue)
        stamps = list(Stamp.objects.filter(issue=issue).prefetch_related("colors"))
        issue_id = issue.pk
        name = issue.name

        for stamp in stamps:
            record(commit_id, user, stamp, "delete", snapshot(stamp), None)
        record(commit_id, user, issue, "delete", snapshot(issue), None)
        issue.delete()

    return DeletedSeries(
        commit_id=commit_id,
        issue_id=issue_id,
        name=name,
        year=year,
        dependencies=dependencies,
    )


def delete_stamp(pk: int, user) -> DeletedStamp:
    """Deletes one stamp, and whatever the cascade takes with it.

    The series-level deletion has a typed confirmation because a set of stamps is
    a decision; one row is not, so this one is a dialog with the counts and no
    secret handshake. The audit writes the full ``before`` snapshot, which is
    what lets S21 bring the stamp back with its original id and colours — the
    ``CollectionItem`` rows the cascade removes do not come back, and the dialog
    says so.

    Args:
        pk: Primary key of the stamp.
        user: Actor, stored in the audit trail.

    Returns:
        What was deleted and what went with it.

    Raises:
        WriteError: 404 when the stamp does not exist.
    """
    commit_id = new_commit_id()

    with transaction.atomic():
        stamp = Stamp.objects.select_for_update().filter(pk=pk).first()
        if stamp is None:
            raise WriteError("The stamp does not exist.", status=404)

        dependencies = stamp_dependencies(stamp)
        identity = {
            "id": stamp.pk,
            "name": stamp.name,
            "code": stamp.edifil_code or stamp.fesofi_code or "",
        }
        record(commit_id, user, stamp, "delete", snapshot(stamp), None)
        stamp.delete()

    return DeletedStamp(
        commit_id=commit_id,
        stamp_id=identity["id"],
        name=identity["name"],
        code=identity["code"],
        dependencies=dependencies,
    )


def create_lookup(key: str, value: Any, user) -> LookupResult:
    """Returns the lookup row for a value, creating it when it is new.

    Args:
        key: Registry key (``country``, ``artist``, ``color``, ...).
        value: The name — or the year, for the numeric lookup.
        user: Actor, stored in the audit trail when a row is created.

    Returns:
        The row and whether it was created. A duplicated name returns the
        existing row with ``created: False`` instead of failing.

    Raises:
        WriteError: If the lookup is unknown or the value is empty.
    """
    lookup = _lookup(key)
    name = _lookup_value(lookup, value)
    commit_id = new_commit_id()

    with transaction.atomic():
        obj, created = lookup.model.objects.get_or_create(**{lookup.name_field: name})
        if created:
            record(commit_id, user, obj, "create", None, snapshot(obj))

    return LookupResult(commit_id=commit_id, lookup=lookup, row=obj, created=created)


def lookup_name(lookup: Lookup, obj: models.Model) -> str:
    """Returns the identifying value of a lookup row, as text."""
    return str(getattr(obj, lookup.name_field))


def row_ref(obj: models.Model) -> dict[str, Any]:
    """Returns the minimum a client needs to replace a temporary row.

    The id is the real one and ``updated_at`` is the baseline the next write
    compares against, so the client can keep editing without reloading.
    """
    updated_at = getattr(obj, "updated_at", None)
    return {
        "id": obj.pk,
        "updated_at": updated_at.isoformat() if updated_at else None,
    }


def _split_series_payload(
    payload: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Separates the series from its stamps, checking the envelope shape."""
    if not isinstance(payload, dict):
        raise WriteError("The request body must be a JSON object.")

    issue_payload = payload.get("issue")
    if not isinstance(issue_payload, dict):
        raise WriteError(
            "The series is missing.", errors={"issue": ["This field is required."]}
        )

    stamps_payload = payload.get("stamps", [])
    if not isinstance(stamps_payload, list) or not all(
        isinstance(stamp, dict) for stamp in stamps_payload
    ):
        raise WriteError(
            "The stamps must be a list of objects.",
            errors={"stamps": ["Expected a list of objects."]},
        )

    return issue_payload, stamps_payload


def _create_issue(payload: dict[str, Any], commit_id: uuid.UUID, user) -> Issue:
    """Validates and writes the series row, with its audit entry."""
    try:
        data = _with_year(payload)
    except RowRejected as rejection:
        raise WriteError(
            "The series was not created.", errors={"issue": rejection.errors}
        )

    serializer = IssueRequestSerializer(data=data)
    if not serializer.is_valid():
        raise WriteError(
            "The series was not created.", errors={"issue": serializer.errors}
        )

    issue = serializer.save()
    record(commit_id, user, issue, "create", None, snapshot(issue))
    return issue


def _create_stamp(
    payload: dict[str, Any],
    index: int,
    issue: Issue,
    commit_id: uuid.UUID,
    user,
) -> Stamp:
    """Validates and writes one stamp of a new series, with its audit entry."""
    data = dict(payload)
    data["issue"] = issue.pk

    try:
        _check_image(data)
        colors = _colors_of(Stamp, data)
    except RowRejected as rejection:
        raise _stamp_failure(index, rejection.errors) from rejection

    serializer = _serializer(Stamp, data=data)
    if not serializer.is_valid():
        raise _stamp_failure(index, _plain(serializer.errors))

    stamp = serializer.save()
    if colors is not None:
        stamp.colors.set(colors)
    record(commit_id, user, stamp, "create", None, snapshot(stamp))
    return stamp


def _stamp_failure(index: int, errors: dict[str, Any]) -> WriteError:
    """Wraps a stamp's field errors into the request-level failure."""
    return WriteError(
        "The series was not created.",
        errors={"stamps": {str(index): _plain(errors)}},
    )


def _with_year(payload: dict[str, Any]) -> dict[str, Any]:
    """Replaces the typed year with the primary key of its ``Year`` row."""
    data = dict(payload)
    raw = data.pop("year", None)
    if raw in (None, ""):
        raise RowRejected({"year": ["This field is required."]})

    data["year"] = _year_pk(raw)
    return data


def _year_pk(value: Any) -> int:
    """Resolves a typed year into a primary key, as a row error when invalid."""
    try:
        return resolve_year(value).pk
    except InvalidYear as error:
        raise RowRejected({"year": [str(error)]}) from error


def resolve_year(value: Any) -> Year:
    """Returns the ``Year`` row for a typed year, creating it when new.

    Args:
        value: The year as the form sends it: a number, or a string holding one.

    Returns:
        The row, existing or just created.

    Raises:
        InvalidYear: If the value is not a number or falls outside the bounds
            shared with the form.
    """
    try:
        year = int(value)
    except (TypeError, ValueError) as error:
        raise InvalidYear("The year must be a number.") from error

    low, high = series_year_bounds()
    if not low <= year <= high:
        raise InvalidYear(f"The year must be between {low} and {high}.")

    return Year.objects.get_or_create(year=year)[0]


def _check_batch(changes: Any) -> list[dict[str, Any]]:
    """Rejects a change set that cannot be applied, before anything is written.

    Envelope-level checks only: the per-row ones need the row and belong to the
    savepoint, so forty corrections are not lost because one of them is wrong.
    """
    if not isinstance(changes, list):
        raise WriteError(
            "The change set is missing.", errors={"changes": ["Expected a list."]}
        )

    if len(changes) > MAX_CHANGES:
        raise WriteError(
            f"At most {MAX_CHANGES} changes per request.",
            errors={"changes": [f"At most {MAX_CHANGES} changes per request."]},
        )

    for change in changes:
        if not isinstance(change, dict):
            raise WriteError(
                "Every change must be an object.",
                errors={"changes": ["Expected a list of objects."]},
            )

        if change.get("model") not in MODEL_ALIASES:
            raise WriteError(
                "Unknown model.",
                errors={"model": [f"Unknown model: {change.get('model')!r}"]},
            )

        op = change.get("op")
        if op == "delete":
            raise WriteError(
                "Deleting needs a confirmation preview.",
                status=409,
                extra={"needs_confirmation": True},
            )
        if op not in WRITABLE_OPS:
            raise WriteError(
                "Unknown operation.", errors={"op": [f"Unknown operation: {op!r}"]}
            )

        if not isinstance(change.get("patch") or {}, dict):
            raise WriteError(
                "The patch must be an object.",
                errors={"patch": ["Expected an object."]},
            )

    return changes


def _apply_row(
    change: dict[str, Any], commit_id: uuid.UUID, user
) -> models.Model:
    """Applies one change inside its savepoint, or raises ``RowRejected``."""
    model = MODEL_ALIASES[change["model"]]
    patch = _prepare_patch(model, dict(change.get("patch") or {}))
    _check_image(patch, model=model)
    colors = _colors_of(model, patch)

    if change["op"] == "create":
        return _insert_row(model, patch, colors, commit_id, user)
    return _update_row(model, change, patch, colors, commit_id, user)


def _serializer(model: type[models.Model], *args, **kwargs):
    """Returns a request serializer without the colour field.

    Colours are taken out of the patch before this point and written with one
    ``set()``, so the serializer must not see the key — and must not ask for it
    either: its field would refuse the empty list a colourless stamp sends.
    """
    serializer = SERIALIZERS[model](*args, **kwargs)
    if model is Stamp:
        serializer.fields.pop("colors", None)
    return serializer


def _colors_of(model: type[models.Model], patch: dict[str, Any]) -> list[Color] | None:
    """Takes the colour ids out of a stamp patch and resolves them to rows.

    They are applied with one ``set()`` inside the transaction instead of
    through the serializer, which refuses an empty list: a stamp without colours
    is a gap the "needs attention" queues report, not an error the user cannot
    fix from the grid.
    """
    if model is not Stamp or "colors" not in patch:
        return None

    raw = patch.pop("colors")
    if not isinstance(raw, list):
        raise RowRejected({"colors": ["Expected a list of ids."]})

    ids = []
    for value in raw:
        try:
            ids.append(int(value))
        except (TypeError, ValueError) as error:
            raise RowRejected({"colors": [f"Not an id: {value!r}"]}) from error

    colors = list(Color.objects.filter(pk__in=ids))
    if len(colors) != len(set(ids)):
        raise RowRejected({"colors": ["One or more colours do not exist."]})
    return colors


def _insert_row(
    model: type[models.Model],
    patch: dict[str, Any],
    colors: list[Color] | None,
    commit_id: uuid.UUID,
    user,
) -> models.Model:
    """Creates one row of the batch, with its audit entry."""
    serializer = _serializer(model, data=patch)
    if not serializer.is_valid():
        raise RowRejected(_plain(serializer.errors))

    obj = serializer.save()
    if colors is not None:
        obj.colors.set(colors)
    record(commit_id, user, obj, "create", None, snapshot(obj))
    return obj


def _update_row(
    model: type[models.Model],
    change: dict[str, Any],
    patch: dict[str, Any],
    colors: list[Color] | None,
    commit_id: uuid.UUID,
    user,
) -> models.Model:
    """Updates one row of the batch, with its audit entry and conflict check."""
    obj = model.objects.select_for_update().filter(pk=_object_id(change)).first()
    if obj is None:
        raise RowRejected({"object_id": ["Row not found."]})

    conflict = _conflict(obj, change.get("expected_updated_at"))
    if conflict is not None:
        raise RowRejected({"expected_updated_at": [conflict]})

    before = snapshot(obj)
    serializer = _serializer(model, obj, data=patch, partial=True)
    if not serializer.is_valid():
        raise RowRejected(_plain(serializer.errors))

    serializer.save()
    if colors is not None:
        obj.colors.set(colors)
    record(commit_id, user, obj, "update", before, snapshot(obj))
    return obj


def _object_id(change: dict[str, Any]) -> int:
    """Returns the primary key of the row to update."""
    try:
        return int(change["object_id"])
    except (KeyError, TypeError, ValueError) as error:
        raise RowRejected({"object_id": ["This field is required."]}) from error


def _prepare_patch(model: type[models.Model], patch: dict[str, Any]) -> dict[str, Any]:
    """Normalizes a patch before it reaches the serializer.

    Empty strings become ``None`` on nullable columns — a cleared date field
    arrives as ``""`` from the form, and the serializer would reject it — and a
    typed issue year is resolved to its primary key.
    """
    prepared: dict[str, Any] = {}
    for name, value in patch.items():
        if model is Issue and name == "year":
            prepared["year"] = _year_pk(value)
            continue

        field = _model_field(model, name)
        if field is not None and value == "" and field.null:
            prepared[name] = None
        else:
            prepared[name] = value

    return prepared


def _model_field(model: type[models.Model], name: str) -> models.Field | None:
    """Returns the model field behind a name, or ``None`` for anything else."""
    try:
        return model._meta.get_field(name)
    except FieldDoesNotExist:
        return None


def _check_image(patch: dict[str, Any], model: type[models.Model] = Stamp) -> None:
    """Refuses any attempt to write a picture.

    DataDesk displays the images the frontend already has; uploading or
    replacing one is out of scope, so the field only accepts nothing.
    """
    if model is not Stamp or not patch.get("image"):
        return
    raise RowRejected({"image": [IMAGE_ERROR]})


def _conflict(obj: models.Model, expected: Any) -> str | None:
    """Compares the row's timestamp with the one the client read.

    Returns:
        An error message when the row changed since, ``None`` when it did not
        or when there is nothing to compare — a row written before the column
        existed has a null timestamp and is accepted.
    """
    if not expected:
        return None

    current = getattr(obj, "updated_at", None)
    if current is None:
        return None

    moment = parse_datetime(str(expected))
    if moment is None:
        return "The expected timestamp is not valid."
    if current != moment:
        return "This row was changed in another tab."
    return None


def _lookup(key: str) -> Lookup:
    """Returns a registry lookup, or refuses the request."""
    try:
        return get_lookup(key)
    except KeyError as error:
        raise WriteError("Unknown lookup.", status=404) from error


def _lookup_value(lookup: Lookup, value: Any) -> Any:
    """Normalizes the value typed in a cell into the row's identifying column."""
    if lookup.numeric:
        try:
            return int(value)
        except (TypeError, ValueError) as error:
            raise WriteError(
                "The value must be a number.", errors={"value": ["Not a number."]}
            ) from error

    name = str(value if value is not None else "").strip()
    if name == "":
        raise WriteError("The name is required.", errors={"value": ["Required."]})
    return name


def _plain(errors: Any) -> Any:
    """Rebuilds DRF's error structure out of plain types for ``JsonResponse``."""
    if isinstance(errors, dict):
        return {str(key): _plain(value) for key, value in errors.items()}
    if isinstance(errors, (list, tuple)):
        return [_plain(value) for value in errors]
    return str(errors)
