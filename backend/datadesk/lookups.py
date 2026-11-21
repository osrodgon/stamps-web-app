"""The reference tables, as one screen.

Eight lookups share a template, a grid and four operations because
``datadesk.registry`` already describes each of them: the model, the column that
names a row, and the relations pointing at it. Nothing here is per table.

The two things that make this work rather than being a thin wrapper over admin:

- **usage** is annotated, not counted per row. A page of 50 artists costs one
  query, not fifty.
- **a duplicate name is the normal case**, not an error: the rename answers 409
  with the id of the row that already has it, and the screen offers the merge,
  which is what the user almost always meant.

Merging is the careful one. A colour can be on a stamp that already has the other
colour, so the junction table is filled pair by pair and the source rows deleted
afterwards; a foreign key is moved with one ``update()`` and the timestamp is set
by hand, because ``auto_now`` does not fire on an update and S12's conflict check
would go blind.
"""

from dataclasses import dataclass
from math import ceil
from typing import Any

from django.apps import apps
from django.db import models, transaction
from django.db.models import Count, QuerySet
from django.urls import reverse
from django.utils import timezone
from django.utils.http import urlencode

from datadesk.audit import new_commit_id, record, snapshot
from datadesk.registry import Lookup, get_lookup
from datadesk.write import WriteError

from colors_api.models import Color

DEFAULT_SIZE = 50
MAX_SIZE = 200
"""A page of a reference table: 300 colours are three pages, not a scroll."""

NEXT_YEARS = 10
MAX_NEXT_YEARS = 50
"""How many years the "next ten" action writes: a decade is one click."""


@dataclass(frozen=True)
class LookupPage:
    """One page of a lookup, with the usage counts already in the rows.

    Attributes:
        rows: ``{"id", "name", "usage"}`` per row.
        page: Page served, clamped to the real range.
        last_page: Last page that has rows.
        total: Rows matching the search.
    """

    rows: list[dict[str, Any]]
    page: int
    last_page: int
    total: int

    def as_dict(self) -> dict[str, Any]:
        """Returns the shape Tabulator's remote pagination expects."""
        return {
            "data": self.rows,
            "page": self.page,
            "last_page": self.last_page,
            "total": self.total,
        }


@dataclass(frozen=True)
class MergeResult:
    """What a merge did, for the screen to say out loud.

    Attributes:
        commit_id: Id of the audit row written.
        moved: References moved from the source to the survivor.
        source: ``{"id", "name"}`` of the row that no longer exists.
        target: ``{"id", "name"}`` of the row that survived.
    """

    commit_id: Any
    moved: int
    source: dict[str, Any]
    target: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        """Returns the counts and the surviving row."""
        return {
            "moved": self.moved,
            "deleted": self.source,
            "survivor": self.target,
        }


def usage_counts(lookup: Lookup) -> dict[str, Count]:
    """Returns one ``Count`` annotation per relation pointing at the lookup.

    The reverse accessor comes from the model field, not from a table of names
    kept in a second place: ``Issue.artist`` already says it is ``issues``.
    ``distinct`` keeps two references of the same model from multiplying rows.
    """
    annotations: dict[str, Count] = {}
    for index, (label, field_name) in enumerate(lookup.refs):
        field = apps.get_model(label)._meta.get_field(field_name)
        accessor = field.remote_field.get_accessor_name()
        annotations[f"usage_{index}"] = Count(accessor, distinct=True)
    return annotations


def usage_of(row: models.Model, annotations: dict[str, Count]) -> int:
    """Returns how many rows point at this one."""
    return sum(getattr(row, name) or 0 for name in annotations)


def series_counts(lookup: Lookup) -> dict[str, Count]:
    """Returns the annotation counting the series behind a row, when it differs.

    A colour is on stamps, so the usage column counts stamps while the workbench
    behind the link shows series: the second number is not a detail, it is the
    only one the link can honestly say. It costs nothing to annotate it in the
    same query, and the two counts do not multiply because both ``distinct``.
    """
    if lookup.model is not Color:
        return {}
    return {"series_usage": Count("stamps__issue", distinct=True)}


def series_of(lookup: Lookup, row: models.Model, annotations: dict[str, Count]) -> int:
    """Returns how many series hold this row: the series the link will show."""
    if lookup.model is Color:
        return row.series_usage or 0
    return usage_of(row, annotations)


def filter_url(key: str, row: models.Model) -> str:
    """Returns the workbench with this row's filter applied.

    The years are the one case where the id is not the value: a series points at
    a ``Year`` row, and the workbench filters by the number, with the range's
    two ends set to it.
    """
    if key == "year":
        query = {"year_min": row.year, "year_max": row.year}
    else:
        query = {key: row.pk}
    return f"{reverse('datadesk:issues')}?{urlencode(query)}"


def lookup_queryset(key: str, query: str = "") -> QuerySet:
    """Returns the rows of a lookup with their usage annotated.

    Args:
        key: Registry key.
        query: What the user searched; empty returns the whole table.

    Raises:
        KeyError: If the key is not a registered lookup.
    """
    lookup = get_lookup(key)
    rows = lookup.model.objects.annotate(
        **usage_counts(lookup), **series_counts(lookup)
    ).order_by(lookup.name_field)
    text = query.strip()
    if text:
        rows = rows.filter(**{f"{lookup.name_field}__icontains": text})
    return rows


def lookup_page(
    key: str, query: str = "", page: int = 1, size: int = DEFAULT_SIZE
) -> LookupPage:
    """Returns one page of a lookup, clamped like the workbench grid."""
    lookup = get_lookup(key)
    annotations = usage_counts(lookup)
    queryset = lookup_queryset(key, query)

    size = max(1, min(size, MAX_SIZE))
    total = queryset.count()
    last_page = max(1, ceil(total / size))
    page = max(1, min(page, last_page))

    rows = [
        {
            "id": row.pk,
            "name": str(getattr(row, lookup.name_field)),
            "usage": usage_of(row, annotations),
            "series": series_of(lookup, row, annotations),
            "filter_url": filter_url(key, row),
        }
        for row in queryset[(page - 1) * size : page * size]
    ]
    return LookupPage(rows=rows, page=page, last_page=last_page, total=total)


def rename_lookup(key: str, pk: Any, name: Any, user) -> dict[str, Any]:
    """Renames one row, refusing a name that another row already has.

    Args:
        key: Registry key.
        pk: Primary key of the row.
        name: The new name, as typed.
        user: Actor, stored in the audit trail.

    Returns:
        ``{"id", "name", "usage"}`` of the renamed row.

    Raises:
        WriteError: 404 when the row is gone, 409 ``duplicate_name`` with the id
            of the row that already has it — which is the screen's cue to offer
            the merge — and 400 for a name that cannot be one (empty, or not a
            number for the years).
    """
    lookup = get_lookup(key)
    value = _clean_name(lookup, name)
    commit_id = new_commit_id()

    with transaction.atomic():
        row = lookup.model.objects.select_for_update().filter(pk=pk).first()
        if row is None:
            raise WriteError("The row does not exist.", status=404)

        if str(getattr(row, lookup.name_field)) == str(value):
            return _row_ref(key, lookup, row)

        clash = (
            lookup.model.objects.filter(**{lookup.name_field: value})
            .exclude(pk=row.pk)
            .first()
        )
        if clash is not None:
            raise WriteError(
                "The name already exists.",
                status=409,
                extra={
                    "error": "duplicate_name",
                    "existing_id": clash.pk,
                    "existing_name": str(getattr(clash, lookup.name_field)),
                },
            )

        before = snapshot(row)
        setattr(row, lookup.name_field, value)
        row.save()
        record(commit_id, user, row, "update", before, snapshot(row))

    return _row_ref(key, lookup, row)


def delete_lookup(key: str, pk: Any, user) -> dict[str, Any]:
    """Deletes a row nobody points at.

    A lookup in use is refused with the count: the only way out of that is the
    merge, and the screen says so. Deleting the row behind 143 stamps would
    either fail on the constraint or take the stamps with it (``year`` is
    ``CASCADE``), and neither is what anyone wanted.

    Raises:
        WriteError: 404 when the row is gone, 409 ``in_use`` with the count.
    """
    lookup = get_lookup(key)
    annotations = usage_counts(lookup)
    commit_id = new_commit_id()

    with transaction.atomic():
        row = (
            lookup.model.objects.select_for_update()
            .annotate(**annotations)
            .filter(pk=pk)
            .first()
        )
        if row is None:
            raise WriteError("The row does not exist.", status=404)

        usage = usage_of(row, annotations)
        if usage:
            raise WriteError(
                "This row is still in use.",
                status=409,
                extra={"error": "in_use", "usage": usage},
            )

        ref = {"id": row.pk, "name": str(getattr(row, lookup.name_field))}
        record(commit_id, user, row, "delete", snapshot(row), None)
        row.delete()

    return ref


def merge_lookups(
    key: str,
    from_id: Any,
    to_id: Any,
    keep_name_from: Any,
    user,
) -> MergeResult:
    """Moves every reference from one row to another, then deletes the source.

    Args:
        key: Registry key.
        from_id: Row that disappears.
        to_id: Row that survives.
        keep_name_from: ``"a"`` keeps the survivor's name, ``"b"`` takes the
            source's — the case «the good name is on the row I am deleting».
        user: Actor, stored in the audit trail.

    Raises:
        WriteError: 404 for an unknown row, 400 for the same row twice, for an
            unknown ``keep_name_from`` or for a name that collides when it is
            borrowed from the source.
    """
    lookup = get_lookup(key)
    if str(from_id) == str(to_id):
        raise WriteError("A row cannot be merged into itself.")

    keep = str(keep_name_from or "a").lower()
    if keep not in {"a", "b"}:
        raise WriteError("The name to keep must be 'a' or 'b'.")

    commit_id = new_commit_id()

    with transaction.atomic():
        rows = {
            row.pk: row
            for row in lookup.model.objects.select_for_update()
            .filter(pk__in=[_pk(from_id), _pk(to_id)])
            .order_by("pk")
        }
        source = rows.get(_pk(from_id))
        target = rows.get(_pk(to_id))
        if source is None or target is None:
            raise WriteError("The row does not exist.", status=404)

        source_name = str(getattr(source, lookup.name_field))
        target_name = str(getattr(target, lookup.name_field))
        before = {"lookup": source_name, "refs": _references_to(lookup, source)}
        moved = _move_references(lookup, source, target)

        record(
            commit_id,
            user,
            source,
            "merge",
            before,
            {"lookup": target_name, "refs": _references_to(lookup, target)},
        )
        source.delete()

        if keep == "b":
            setattr(target, lookup.name_field, source_name)
            try:
                with transaction.atomic():
                    target.save()
            except Exception as error:  # noqa: BLE001 - the constraint decides
                raise WriteError(
                    "The name could not be moved to the surviving row.",
                    status=409,
                ) from error

    return MergeResult(
        commit_id=commit_id,
        moved=moved,
        source={"id": source.pk, "name": source_name},
        target={"id": target.pk, "name": str(getattr(target, lookup.name_field))},
    )


def create_next_years(count: Any = NEXT_YEARS) -> int:
    """Creates the years after the newest one, returning how many are new.

    ``Year`` has no row until a series uses it, so writing the next decade is
    what saves the user from typing a year and finding out it had to be created.
    """
    try:
        wanted = int(count)
    except (TypeError, ValueError) as error:
        raise WriteError(
            "The count must be a number.", errors={"count": ["Not a number."]}
        ) from error

    wanted = max(1, min(wanted, MAX_NEXT_YEARS))
    model = get_lookup("year").model
    newest = model.objects.order_by("-year").first()
    start = (newest.year if newest else timezone.localdate().year) + 1

    created = 0
    for year in range(start, start + wanted):
        _, is_new = model.objects.get_or_create(year=year)
        created += int(is_new)
    return created


def _clean_name(lookup: Lookup, name: Any) -> Any:
    """Normalizes a typed name, refusing the ones that cannot be a name."""
    if lookup.numeric:
        try:
            return int(str(name).strip())
        except (TypeError, ValueError) as error:
            raise WriteError(
                "The name must be a number.",
                errors={str(lookup.name_field): ["Not a number."]},
            ) from error

    text = str(name if name is not None else "").strip()
    if text == "":
        raise WriteError(
            "The name is required.", errors={str(lookup.name_field): ["Required."]}
        )
    return text


def _pk(value: Any) -> int:
    """Returns a primary key from a request value, as a row-level failure."""
    try:
        return int(value)
    except (TypeError, ValueError) as error:
        raise WriteError(
            "The row is required.", errors={"id": ["This field is required."]}
        ) from error


def _references_to(lookup: Lookup, row: models.Model) -> int:
    """Counts the rows pointing at one row, for the audit note."""
    annotations = usage_counts(lookup)
    annotated = lookup.model.objects.annotate(**annotations).get(pk=row.pk)
    return usage_of(annotated, annotations)


def _move_references(lookup: Lookup, source: models.Model, target: models.Model) -> int:
    """Points everything at ``target`` that pointed at ``source``.

    Two shapes, and they need different care:

    - a foreign key is one ``update()``; the timestamp goes with it because
      ``auto_now`` is a ``save()`` hook and an update never calls it (S12's
      conflict check reads that column);
    - a many-to-many (colours) can be on a stamp that already has the target, so
      the junction table is filled pair by pair with ``ignore_conflicts`` and the
      source rows are deleted afterwards — no duplicates, and no reliance on
      ``.add()`` ignoring conflicts, which changed between Django versions.
    """
    moved = 0
    for label, field_name in lookup.refs:
        model = apps.get_model(label)
        field = model._meta.get_field(field_name)

        if field.many_to_many:
            through = field.remote_field.through
            owner = field.m2m_field_name()
            other = field.m2m_reverse_field_name()
            linked = through.objects.filter(**{other: source.pk})
            keep = set(
                through.objects.filter(**{other: target.pk}).values_list(
                    owner, flat=True
                )
            )
            owners = list(linked.values_list(owner, flat=True))
            through.objects.bulk_create(
                [
                    through(**{f"{owner}_id": pk, f"{other}_id": target.pk})
                    for pk in owners
                    if pk not in keep
                ],
                ignore_conflicts=True,
            )
            linked.delete()
            # The stamps whose colours changed are different rows now.
            model.objects.filter(pk__in=owners).update(updated_at=timezone.now())
            moved += len(owners)
            continue

        moved += model.objects.filter(**{field_name: source}).update(
            **{field_name: target}, updated_at=timezone.now()
        )
    return moved


def _row_ref(key: str, lookup: Lookup, row: models.Model) -> dict[str, Any]:
    """Returns the row as the grid reads it, with its counts and its link."""
    annotations = usage_counts(lookup)
    annotated = lookup.model.objects.annotate(
        **annotations, **series_counts(lookup)
    ).get(pk=row.pk)
    return {
        "id": annotated.pk,
        "name": str(getattr(annotated, lookup.name_field)),
        "usage": usage_of(annotated, annotations),
        "series": series_of(lookup, annotated, annotations),
        "filter_url": filter_url(key, annotated),
    }
