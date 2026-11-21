"""S12 acceptance: the write core, without any UI involved.

Two paths, one transaction each: creating a series with its stamps is all or
nothing, a batch of edits keeps a savepoint per row. These tests use the writer
directly; the HTTP layer (staff gate, CSRF, status codes) has its own file,
because those are properties of the endpoint, not of the transaction.
"""

import pytest

from datadesk import write
from datadesk.models import DataDeskChange
from datadesk.write import (
    MAX_CHANGES,
    InvalidYear,
    WriteError,
    apply_changes,
    create_lookup,
    create_series,
    resolve_year,
)
from issues_api.models import Issue
from stamps_api.models import Stamp
from years_api.models import Year
from artists_api.models import Artist
from colors_api.models import Color
from countries_api.models import Country
from paper_types_api.models import PaperType
from print_types_api.models import PrintType
from printers_api.models import Printer
from stamp_types_api.models import StampType

STAMP_COUNT = 8


@pytest.fixture
def staff_user(db, django_user_model):
    """The single DataDesk user."""
    return django_user_model.objects.create_user(
        username="curator", password="s3cret-pass", is_staff=True
    )


@pytest.fixture
def lookups(db) -> dict:
    """The reference rows a series needs, one of each kind."""
    return {
        "country": Country.objects.create(name="España"),
        "stamp_type": StampType.objects.create(name="Conmemorativo"),
        "print_type": PrintType.objects.create(name="Offset"),
        "printer": Printer.objects.create(name="FNMT"),
        "artist": Artist.objects.create(name="Anónimo"),
        "paper_type": PaperType.objects.create(name="Estucado"),
        "red": Color.objects.create(name="Rojo"),
        "blue": Color.objects.create(name="Azul"),
    }


def series_payload(lookups: dict, year: int = 1987, stamps: int = STAMP_COUNT) -> dict:
    """Returns the body the new-series workspace will send."""
    return {
        "issue": {
            "year": year,
            "date": "1987-05-12",
            "name": "Serie de prueba",
            "country": lookups["country"].pk,
            "stamp_type": lookups["stamp_type"].pk,
            "total_printed": 100_000,
            "market_value_mnh": "12.50",
            "perforation": "13 1/4",
        },
        "stamps": [
            {
                "name": f"Sello {index}",
                "face_value": "6 Pta",
                "edifil_code": f"{100 + index}",
                "colors": [lookups["red"].pk, lookups["blue"].pk],
            }
            for index in range(stamps)
        ],
    }


@pytest.fixture
def series(lookups, staff_user) -> Issue:
    """An existing series with eight stamps, for the batch tests."""
    return create_series(series_payload(lookups), staff_user).issue


def issue_patch(issue: Issue, **values) -> dict:
    """Returns one ``update`` change for an issue."""
    return {
        "model": "issue",
        "object_id": issue.pk,
        "op": "update",
        "patch": values,
    }


def stamp_patch(stamp: Stamp, **values) -> dict:
    """Returns one ``update`` change for a stamp."""
    return {
        "model": "stamp",
        "object_id": stamp.pk,
        "op": "update",
        "patch": values,
    }


@pytest.mark.django_db
class TestCreateSeries:
    """The series and its stamps land together, or not at all."""

    def test_writes_the_series_and_every_stamp(self, lookups, staff_user) -> None:
        result = create_series(series_payload(lookups), staff_user)

        assert Issue.objects.count() == 1
        assert Stamp.objects.count() == STAMP_COUNT
        assert result.issue.name == "Serie de prueba"
        assert [stamp.name for stamp in result.stamps] == [
            f"Sello {index}" for index in range(STAMP_COUNT)
        ]

    def test_keeps_the_colors_of_every_stamp(self, lookups, staff_user) -> None:
        create_series(series_payload(lookups), staff_user)

        for stamp in Stamp.objects.prefetch_related("colors"):
            assert sorted(color.name for color in stamp.colors.all()) == [
                "Azul",
                "Rojo",
            ]

    def test_audits_every_written_row_under_one_commit(
        self, lookups, staff_user
    ) -> None:
        result = create_series(series_payload(lookups), staff_user)

        changes = DataDeskChange.objects.all()
        assert changes.count() == 1 + STAMP_COUNT
        assert {change.commit_id for change in changes} == {result.commit_id}
        assert {change.operation for change in changes} == {"create"}
        assert {change.user for change in changes} == {staff_user}

    def test_creates_the_year_it_was_told_to(self, lookups, staff_user) -> None:
        result = create_series(series_payload(lookups, year=2001), staff_user)

        assert result.issue.year.year == 2001
        assert Year.objects.filter(year=2001).exists()

    def test_one_bad_stamp_writes_nothing(self, lookups, staff_user) -> None:
        payload = series_payload(lookups, year=2001)
        payload["stamps"][3]["name"] = ""

        with pytest.raises(WriteError) as refused:
            create_series(payload, staff_user)

        assert "stamps" in refused.value.errors
        assert Issue.objects.count() == 0
        assert Stamp.objects.count() == 0
        assert DataDeskChange.objects.count() == 0
        assert not Year.objects.filter(year=2001).exists()

    def test_a_bad_series_writes_nothing(self, lookups, staff_user) -> None:
        payload = series_payload(lookups)
        payload["issue"]["name"] = ""

        with pytest.raises(WriteError) as refused:
            create_series(payload, staff_user)

        assert "issue" in refused.value.errors
        assert Issue.objects.count() == 0
        assert DataDeskChange.objects.count() == 0

    def test_refuses_a_picture(self, lookups, staff_user) -> None:
        payload = series_payload(lookups)
        payload["stamps"][0]["image"] = "stamps/1987/1.webp"

        with pytest.raises(WriteError) as refused:
            create_series(payload, staff_user)

        assert refused.value.errors["stamps"]["0"]["image"] == [write.IMAGE_ERROR]
        assert Stamp.objects.count() == 0

    def test_refuses_a_year_out_of_range(self, lookups, staff_user) -> None:
        with pytest.raises(WriteError):
            create_series(series_payload(lookups, year=1700), staff_user)

        assert not Year.objects.filter(year=1700).exists()
        assert Issue.objects.count() == 0

    def test_refuses_a_series_without_a_year(self, lookups, staff_user) -> None:
        payload = series_payload(lookups)
        del payload["issue"]["year"]

        with pytest.raises(WriteError) as refused:
            create_series(payload, staff_user)

        assert refused.value.errors["issue"]["year"] == ["This field is required."]

    def test_refuses_a_missing_envelope(self, staff_user) -> None:
        with pytest.raises(WriteError):
            create_series({"stamps": []}, staff_user)

    def test_refuses_stamps_that_are_not_objects(self, lookups, staff_user) -> None:
        payload = series_payload(lookups)
        payload["stamps"] = ["Sello 1"]

        with pytest.raises(WriteError):
            create_series(payload, staff_user)


@pytest.mark.django_db
class TestApplyChanges:
    """A batch applies what it can and reports what it cannot."""

    def test_applies_forty_changes_in_one_commit(self, lookups, staff_user) -> None:
        create_series(series_payload(lookups, stamps=40), staff_user)
        baseline = DataDeskChange.objects.count()
        stamps = list(Stamp.objects.order_by("pk"))
        changes = [
            stamp_patch(stamp, edifil_code=f"X{index}")
            for index, stamp in enumerate(stamps)
        ]

        result = apply_changes(changes, staff_user)

        assert result.applied == 40
        assert result.rejected == []
        assert result.success
        assert Stamp.objects.filter(edifil_code__startswith="X").count() == 40
        assert [row["index"] for row in result.rows] == list(range(40))
        assert all(row["updated_at"] for row in result.rows)
        written = DataDeskChange.objects.filter(commit_id=result.commit_id)
        assert written.count() == 40
        assert DataDeskChange.objects.count() == baseline + 40

    def test_one_bad_row_does_not_stop_the_batch(self, lookups, staff_user) -> None:
        create_series(series_payload(lookups, stamps=40), staff_user)
        stamps = list(Stamp.objects.order_by("pk"))
        changes = [
            (
                stamp_patch(stamp, market_value_mnh="no es un número")
                if index == 20
                else stamp_patch(stamp, edifil_code=f"B{index}")
            )
            for index, stamp in enumerate(stamps)
        ]

        result = apply_changes(changes, staff_user)

        assert result.applied == 39
        assert not result.success
        assert [row["index"] for row in result.rejected] == [20]
        assert "market_value_mnh" in result.rejected[0]["errors"]
        assert Stamp.objects.filter(edifil_code__startswith="B").count() == 39
        assert DataDeskChange.objects.filter(commit_id=result.commit_id).count() == 39

    def test_delete_needs_the_preview(self, series, staff_user) -> None:
        change = {
            "model": "issue",
            "object_id": series.pk,
            "op": "delete",
            "patch": {},
        }

        with pytest.raises(WriteError) as refused:
            apply_changes([change], staff_user)

        assert refused.value.status == 409
        assert refused.value.extra == {"needs_confirmation": True}
        assert Issue.objects.filter(pk=series.pk).exists()
        assert DataDeskChange.objects.count() == 1 + STAMP_COUNT

    def test_a_stale_timestamp_rejects_only_that_row(self, series, staff_user) -> None:
        stamps = list(Stamp.objects.order_by("pk")[:2])
        changes = [
            stamp_patch(stamps[0], edifil_code="900")
            | {"expected_updated_at": "2020-01-01T00:00:00+00:00"},
            stamp_patch(stamps[1], edifil_code="901"),
        ]

        result = apply_changes(changes, staff_user)

        assert result.applied == 1
        assert result.rejected[0]["index"] == 0
        assert "expected_updated_at" in result.rejected[0]["errors"]
        stamps[0].refresh_from_db()
        stamps[1].refresh_from_db()
        assert stamps[0].edifil_code != "900"
        assert stamps[1].edifil_code == "901"

    def test_a_matching_timestamp_is_accepted(self, series, staff_user) -> None:
        stamp = Stamp.objects.order_by("pk").first()
        change = stamp_patch(stamp, edifil_code="902") | {
            "expected_updated_at": stamp.updated_at.isoformat()
        }

        result = apply_changes([change], staff_user)

        assert result.applied == 1
        stamp.refresh_from_db()
        assert stamp.edifil_code == "902"

    def test_a_null_timestamp_is_not_a_conflict(self, series, staff_user) -> None:
        stamp = Stamp.objects.order_by("pk").first()
        Stamp.objects.filter(pk=stamp.pk).update(updated_at=None)
        change = stamp_patch(stamp, edifil_code="903") | {
            "expected_updated_at": "2020-01-01T00:00:00+00:00"
        }

        result = apply_changes([change], staff_user)

        assert result.applied == 1

    def test_a_stamp_description_is_written_from_the_pane(
        self, series, staff_user
    ) -> None:
        """The description has no column, but it is a field like any other."""
        stamp = Stamp.objects.order_by("pk").first()
        change = stamp_patch(stamp, description="Cuadro conmemorativo")

        result = apply_changes([change], staff_user)

        assert result.applied == 1
        stamp.refresh_from_db()
        assert stamp.description == "Cuadro conmemorativo"

    def test_a_cleared_description_becomes_null(self, series, staff_user) -> None:
        stamp = Stamp.objects.order_by("pk").first()
        Stamp.objects.filter(pk=stamp.pk).update(description="Algo")

        result = apply_changes([stamp_patch(stamp, description="")], staff_user)

        assert result.applied == 1
        stamp.refresh_from_db()
        assert stamp.description is None

    def test_creates_a_stamp_of_an_existing_series(self, series, staff_user) -> None:
        change = {
            "model": "stamp",
            "op": "create",
            "patch": {
                "issue": series.pk,
                "name": "Sello nuevo",
                "face_value": "2 Pta",
            },
        }

        result = apply_changes([change], staff_user)

        assert result.applied == 1
        assert series.stamps.count() == STAMP_COUNT + 1
        created = DataDeskChange.objects.filter(commit_id=result.commit_id)
        assert created.count() == 1
        assert created.get().operation == "create"
        assert result.rows[0]["id"] == series.stamps.order_by("-pk").first().pk

    def test_creates_a_series_through_apply(self, staff_user) -> None:
        change = {
            "model": "issue",
            "op": "create",
            "patch": {"year": 1999, "name": "Suelta"},
        }

        result = apply_changes([change], staff_user)

        assert result.applied == 1
        assert Issue.objects.get(name="Suelta").year.year == 1999

    def test_a_cleared_date_becomes_null(self, series, staff_user) -> None:
        result = apply_changes([issue_patch(series, date="")], staff_user)

        assert result.applied == 1
        series.refresh_from_db()
        assert series.date is None

    def test_changes_the_year_of_a_series(self, series, staff_user) -> None:
        result = apply_changes([issue_patch(series, year=1990)], staff_user)

        assert result.applied == 1
        series.refresh_from_db()
        assert series.year.year == 1990

    def test_refuses_more_changes_than_the_cap(self, series, staff_user) -> None:
        changes = [issue_patch(series, name="x") for _ in range(MAX_CHANGES + 1)]

        with pytest.raises(WriteError) as refused:
            apply_changes(changes, staff_user)

        assert refused.value.status == 400
        assert DataDeskChange.objects.count() == 1 + STAMP_COUNT

    def test_refuses_an_unknown_model(self, staff_user) -> None:
        with pytest.raises(WriteError):
            apply_changes([{"model": "color", "op": "update", "patch": {}}], staff_user)

    def test_refuses_an_unknown_operation(self, series, staff_user) -> None:
        change = issue_patch(series, name="x") | {"op": "merge"}

        with pytest.raises(WriteError):
            apply_changes([change], staff_user)

    def test_refuses_a_change_set_that_is_not_a_list(self, staff_user) -> None:
        with pytest.raises(WriteError):
            apply_changes({"model": "issue"}, staff_user)

    def test_a_missing_object_id_is_a_rejected_row(self, staff_user) -> None:
        change = {"model": "issue", "op": "update", "patch": {"name": "x"}}

        result = apply_changes([change], staff_user)

        assert result.applied == 0
        assert "object_id" in result.rejected[0]["errors"]

    def test_a_missing_row_is_a_rejected_row(self, staff_user) -> None:
        change = {
            "model": "issue",
            "object_id": 999_999,
            "op": "update",
            "patch": {"name": "x"},
        }

        result = apply_changes([change], staff_user)

        assert result.rejected[0]["errors"]["object_id"] == ["Row not found."]

    def test_an_unknown_field_is_a_rejected_row(self, series, staff_user) -> None:
        result = apply_changes([issue_patch(series, nope=1)], staff_user)

        assert result.applied == 0
        assert "nope" in result.rejected[0]["errors"]

    def test_an_unexpected_failure_rolls_the_whole_batch_back(
        self, series, staff_user, monkeypatch
    ) -> None:
        stamps = list(Stamp.objects.order_by("pk")[:3])
        changes = [
            stamp_patch(stamp, edifil_code=f"R{index}")
            for index, stamp in enumerate(stamps)
        ]
        calls = {"count": 0}
        original = write.record

        def failing_record(*args, **kwargs):
            calls["count"] += 1
            if calls["count"] == 2:
                raise RuntimeError("boom")
            return original(*args, **kwargs)

        monkeypatch.setattr(write, "record", failing_record)

        with pytest.raises(RuntimeError):
            apply_changes(changes, staff_user)

        assert Stamp.objects.filter(edifil_code__startswith="R").count() == 0
        assert DataDeskChange.objects.count() == 1 + STAMP_COUNT


@pytest.mark.django_db
class TestResolveYear:
    """The typed year, bound to the same range the form uses."""

    def test_reuses_an_existing_row(self, db) -> None:
        year = Year.objects.create(year=1987)

        assert resolve_year("1987") == year

    def test_creates_a_new_row(self, db) -> None:
        assert resolve_year(1975).year == 1975

    def test_refuses_a_value_that_is_not_a_number(self, db) -> None:
        with pytest.raises(InvalidYear):
            resolve_year("mil novecientos")

    def test_refuses_a_year_before_the_bound(self, db) -> None:
        with pytest.raises(InvalidYear):
            resolve_year(1700)


@pytest.mark.django_db
class TestCreateLookup:
    """An inline lookup is created once and reused afterwards."""

    def test_creates_and_audits_a_new_row(self, staff_user) -> None:
        result = create_lookup("country", "Portugal", staff_user)

        assert result.created
        assert result.row.name == "Portugal"
        assert result.as_dict()["data"] == {
            "id": result.row.pk,
            "name": "Portugal",
            "created": True,
        }
        assert DataDeskChange.objects.get().commit_id == result.commit_id

    def test_returns_the_existing_row_on_a_duplicate(self, staff_user) -> None:
        first = create_lookup("country", "Portugal", staff_user)
        second = create_lookup("country", "Portugal", staff_user)

        assert not second.created
        assert second.row == first.row
        assert DataDeskChange.objects.count() == 1

    def test_creates_the_numeric_lookup(self, staff_user) -> None:
        result = create_lookup("year", "1975", staff_user)

        assert result.created
        assert result.row.year == 1975
        assert result.as_dict()["data"]["name"] == "1975"

    def test_refuses_an_empty_name(self, staff_user) -> None:
        with pytest.raises(WriteError):
            create_lookup("country", "   ", staff_user)

    def test_refuses_an_unknown_lookup(self, staff_user) -> None:
        with pytest.raises(WriteError) as refused:
            create_lookup("planet", "Marte", staff_user)

        assert refused.value.status == 404
