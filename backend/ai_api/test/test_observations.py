"""Tests for `SourceObservation`, the evidence behind a valuation (step A1)."""

from decimal import Decimal

import pytest
from django.db import IntegrityError, transaction

from ai_api.models import SourceObservation
from issues_api.models import Issue
from stamps_api.models import Stamp
from years_api.models import Year


pytestmark = pytest.mark.django_db


@pytest.fixture
def issue() -> Issue:
    """A series to attach observations to."""
    year, _ = Year.objects.get_or_create(year=1850)
    return Issue.objects.create(year=year, name="Isabel II")


@pytest.fixture
def stamp(issue: Issue) -> Stamp:
    """A stamp of that series."""
    return Stamp.objects.create(
        issue=issue,
        name="6 cuartos",
        face_value="6 cuartos",
        edifil_code="1",
    )


def observation(**overrides) -> SourceObservation:
    """Build an unsaved observation with sensible defaults."""
    fields = {
        "source": SourceObservation.Source.TODOCOLECCION,
        "kind": SourceObservation.Kind.ASK,
        "price": Decimal("24.00"),
        "currency": "EUR",
        "condition": SourceObservation.Condition.USED,
        "url": "https://www.todocoleccion.net/lote/123",
    }
    fields.update(overrides)
    return SourceObservation(**fields)


class TestIdentity:
    """The hash decides what counts as the same observation."""

    def test_the_hash_is_computed_on_save(self, stamp: Stamp):
        row = observation(stamp=stamp)
        row.save()

        assert len(row.raw_hash) == 64
        assert row.raw_hash == row.build_hash()

    def test_the_same_price_twice_is_one_row(self, stamp: Stamp):
        observation(stamp=stamp).save()

        with pytest.raises(IntegrityError):
            with transaction.atomic():
                observation(stamp=stamp).save()

    def test_a_different_price_is_a_second_row(self, stamp: Stamp):
        observation(stamp=stamp).save()
        observation(stamp=stamp, price=Decimal("31.00")).save()

        assert SourceObservation.objects.filter(stamp=stamp).count() == 2

    def test_a_different_condition_is_a_second_row(self, stamp: Stamp):
        observation(stamp=stamp).save()
        observation(stamp=stamp, condition=SourceObservation.Condition.MNH).save()

        assert SourceObservation.objects.count() == 2

    def test_the_subject_is_part_of_the_identity(self, issue: Issue):
        stamp = Stamp.objects.create(
            issue=issue, name="6 cuartos", face_value="6 cuartos"
        )
        other = Stamp.objects.create(
            issue=issue, name="12 cuartos", face_value="12 cuartos"
        )

        observation(stamp=stamp).save()
        observation(stamp=other).save()

        assert SourceObservation.objects.count() == 2

    def test_the_timestamp_is_not_part_of_the_identity(self, stamp: Stamp):
        first = observation(stamp=stamp)
        second = observation(stamp=stamp)

        assert first.build_hash() == second.build_hash()


class TestSubject:
    """An observation is about a stamp or a series, never both and never neither."""

    def test_a_stamp_observation_is_stored(self, stamp: Stamp):
        row = observation(stamp=stamp)
        row.save()

        assert row.stamp == stamp
        assert row.issue is None

    def test_an_issue_observation_is_stored(self, issue: Issue):
        row = observation(issue=issue)
        row.save()

        assert row.issue == issue
        assert row.stamp is None

    def test_neither_subject_is_refused(self):
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                observation().save()

    def test_both_subjects_are_refused(self, issue: Issue, stamp: Stamp):
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                observation(issue=issue, stamp=stamp).save()


class TestDefaults:
    """What an observation assumes when the source says nothing."""

    def test_currency_defaults_to_euro(self, stamp: Stamp):
        row = SourceObservation(
            source=SourceObservation.Source.TODOCOLECCION,
            kind=SourceObservation.Kind.ASK,
            price=Decimal("24.00"),
            stamp=stamp,
        )
        row.save()

        assert row.currency == "EUR"

    def test_condition_defaults_to_unknown(self, stamp: Stamp):
        row = SourceObservation(
            source=SourceObservation.Source.COLNECT,
            kind=SourceObservation.Kind.SOLD,
            price=Decimal("10.00"),
            stamp=stamp,
        )
        row.save()

        assert row.condition == SourceObservation.Condition.UNKNOWN

    def test_observed_at_is_set_on_creation(self, stamp: Stamp):
        row = observation(stamp=stamp)
        row.save()

        assert row.observed_at is not None

    def test_raw_payload_is_kept_when_given(self, stamp: Stamp):
        row = observation(stamp=stamp, raw={"title": "6 cuartos negro"})
        row.save()

        assert row.raw["title"] == "6 cuartos negro"

    def test_the_string_names_the_source_and_the_price(self, stamp: Stamp):
        row = observation(stamp=stamp)
        row.save()

        assert "todocoleccion" in str(row)
        assert "24.00" in str(row)
