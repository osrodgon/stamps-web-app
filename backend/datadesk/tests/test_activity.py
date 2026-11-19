"""S21 acceptance: the log read back, and a commit undone whole or not at all.

The audit trail has been written since S6; what these tests pin is that reading
it gives the same story the editor told, and that undoing it puts the database
back where it was — including the ids and colours of rows a deletion took away,
and the ordering that makes a cascade not eat a row whose revert has not run yet.
"""

import json
import uuid
from datetime import timedelta

import pytest
from django.core.cache import cache
from django.test import Client
from django.utils import timezone

from colors_api.models import Color
from collection_items_api.models import CollectionItem
from collections_api.models import Collection
from countries_api.models import Country
from datadesk.activity import activity_page, changed_fields, revert_commit, revert_order
from datadesk.models import DataDeskChange
from datadesk.write import (
    CLONED_FROM_KEY,
    WriteError,
    apply_changes,
    clone_series,
    create_series,
    delete_series,
)
from issues_api.models import Issue
from stamps_api.models import Stamp
from years_api.models import Year

ACTIVITY_URL = "/datadesk/activity/"
REVERT_URL = "/datadesk/activity/{commit}/revert"
JSON = "application/json"
STAMPS = 3


@pytest.fixture
def writer(db, django_user_model):
    """The user the writers are called as."""
    return django_user_model.objects.create_user(
        username="writer", password="s3cret-pass", is_staff=True
    )


@pytest.fixture
def red(db) -> Color:
    """A colour, so a recreated stamp has something to keep."""
    return Color.objects.create(name="Rojo")


@pytest.fixture
def series(writer, red) -> Issue:
    """A series written the way the workspace writes one."""
    payload = {
        "issue": {
            "year": 1987,
            "date": "1987-05-12",
            "name": "Exposición de Málaga",
            "country": Country.objects.create(name="España").pk,
            "total_printed": 500_000,
        },
        "stamps": [
            {
                "name": f"Sello {index}",
                "face_value": "6 Pta",
                "edifil_code": f"{2744 + index}",
                "colors": [red.pk],
            }
            for index in range(STAMPS)
        ],
    }
    return create_series(payload, writer).issue


@pytest.fixture
def staff_client(mounted, django_user_model) -> Client:
    """A logged-in staff client."""
    django_user_model.objects.create_user(
        username="curator", password="s3cret-pass", is_staff=True
    )
    client = Client()
    client.login(username="curator", password="s3cret-pass")
    return client


def commit_of(issue: Issue) -> uuid.UUID:
    """Returns the commit that created a series."""
    return DataDeskChange.objects.get(
        model_label="issues_api.Issue", object_id=issue.pk, operation="create"
    ).commit_id


@pytest.mark.django_db
class TestReadingTheLog:
    """One commit is one card, with the rows in the order they would be undone."""

    def test_a_commit_is_one_card(self, series) -> None:
        page = activity_page()

        assert page.total == 1
        assert page.commits[0].summary == f"{1 + STAMPS} objects"
        assert page.commits[0].state == "reversible"

    def test_the_newest_commit_comes_first(self, series, writer) -> None:
        apply_changes(
            [
                {
                    "model": "issue",
                    "object_id": series.pk,
                    "op": "update",
                    "patch": {"name": "Otra cosa"},
                }
            ],
            writer,
        )

        page = activity_page()

        assert page.total == 2
        assert page.commits[0].rows[0].operation_label == "updated"

    def test_pagination_counts_commits_not_rows(self, series, writer) -> None:
        for name in ("Uno", "Dos"):
            apply_changes(
                [
                    {
                        "model": "issue",
                        "object_id": series.pk,
                        "op": "update",
                        "patch": {"name": name},
                    }
                ],
                writer,
            )

        page = activity_page(page=2, size=1)

        assert page.total == 3
        assert page.last_page == 3
        assert len(page.commits) == 1

    def test_a_create_lists_every_column(self, series) -> None:
        issue_row = [
            row
            for row in activity_page(labels={"name": "Name"}).commits[0].rows
            if row.object_label.startswith("Series")
        ][0]

        assert "Name" in issue_row.fields

    def test_an_update_lists_only_what_changed(self, series, writer) -> None:
        apply_changes(
            [
                {
                    "model": "issue",
                    "object_id": series.pk,
                    "op": "update",
                    "patch": {"name": "Solo el nombre"},
                }
            ],
            writer,
        )

        labels = {row.object_label: row for row in activity_page().commits[0].rows}

        assert labels[f"Series #{series.pk}"].fields == ["name"]

    def test_the_clone_marker_is_not_a_column(self, series, writer) -> None:
        """``cloned_from`` is provenance, not a field of the row."""
        copy = clone_series(series.pk, None, writer)

        row = DataDeskChange.objects.get(
            commit_id=copy.commit_id, model_label="issues_api.Issue"
        )

        assert CLONED_FROM_KEY in row.after
        assert CLONED_FROM_KEY not in changed_fields(None, row.after)
        assert "name" in changed_fields(None, row.after)

    def test_a_merge_is_marked_not_revertible(self, db, writer) -> None:
        Year.objects.create(year=1987)

        from datadesk.lookups import merge_lookups

        source = Year.objects.get(year=1987)
        target = Year.objects.create(year=1988)
        merge_lookups("year", source.pk, target.pk, "a", writer)

        commit = activity_page().commits[0]

        assert commit.state == "merged"
        assert "merge" in commit.state_label

    def test_the_undo_order_is_the_dependency_order(self, series) -> None:
        """Deletions run children first; recreations run parents first."""
        rows = list(DataDeskChange.objects.filter(commit_id=commit_of(series)))
        order = revert_order(rows)

        # Stamps first, the series at the end: the other way round the cascade
        # would delete a stamp whose own revert has not run yet.
        assert [row.model_label for row in order] == [
            "stamps_api.Stamp",
        ] * STAMPS + ["issues_api.Issue"]
        assert order[-1].object_id == series.pk


@pytest.mark.django_db
class TestRevertingACreation:
    """What a commit created, a revert deletes — children before parents."""

    def test_the_series_and_its_stamps_go(self, series) -> None:
        revert_commit(commit_of(series), None)

        assert Issue.objects.count() == 0
        assert Stamp.objects.count() == 0

    def test_the_revert_is_a_commit_of_its_own(self, series, writer) -> None:
        result = revert_commit(commit_of(series), writer)

        undos = DataDeskChange.objects.filter(commit_id=result.commit_id)
        assert undos.count() == 1 + STAMPS
        assert {row.operation for row in undos} == {"delete"}
        assert {row.reverts_commit_id for row in undos} == {result.reverted}

    def test_the_original_rows_are_marked_reverted(self, series) -> None:
        original = commit_of(series)
        revert_commit(original, None)

        assert all(
            row.reverted_at is not None
            for row in DataDeskChange.objects.filter(commit_id=original)
        )
        commits = {commit.commit_id: commit for commit in activity_page().commits}
        assert commits[original].state == "reverted"
        assert commits[original].state_label.startswith("Reverted on")

    def test_a_second_revert_is_refused(self, series) -> None:
        revert_commit(commit_of(series), None)

        with pytest.raises(WriteError) as refused:
            revert_commit(commit_of(series), None)

        assert refused.value.status == 409
        assert "already" in refused.value.message

    def test_a_clone_is_a_creation_and_goes_the_same_way(self, series, writer) -> None:
        copy = clone_series(series.pk, None, writer)

        revert_commit(copy.commit_id, writer)

        assert not Issue.objects.filter(pk=copy.issue.pk).exists()
        assert Issue.objects.filter(pk=series.pk).exists()


@pytest.mark.django_db
class TestRevertingADeletion:
    """Rows come back with their ids, their colours and their collections gone."""

    def test_the_series_comes_back_with_its_stamps(self, series, writer) -> None:
        ids = list(series.stamps.order_by("pk").values_list("pk", flat=True))
        deletion = delete_series(series.pk, "1987", writer)

        revert_commit(deletion.commit_id, writer)

        assert Issue.objects.filter(pk=series.pk).exists()
        assert set(Stamp.objects.values_list("pk", flat=True)) == set(ids)

    def test_the_colours_come_back(self, series, writer) -> None:
        deletion = delete_series(series.pk, "1987", writer)

        revert_commit(deletion.commit_id, writer)

        for stamp in Stamp.objects.all():
            assert [color.name for color in stamp.colors.all()] == ["Rojo"]

    def test_the_collection_items_do_not_come_back(self, series, writer) -> None:
        """The catalogue is restored; who owned those stamps is not."""
        collection = Collection.objects.create(name="Mía")
        CollectionItem.objects.create(
            collection=collection, stamp=series.stamps.first()
        )
        deletion = delete_series(series.pk, "1987", writer)

        revert_commit(deletion.commit_id, writer)

        assert Stamp.objects.exists()
        assert CollectionItem.objects.count() == 0


@pytest.mark.django_db
class TestRevertingAnUpdate:
    """The whole snapshot goes back, not a diff."""

    def test_the_old_values_return(self, series, writer) -> None:
        apply_changes(
            [
                {
                    "model": "issue",
                    "object_id": series.pk,
                    "op": "update",
                    "patch": {"name": "Nombre nuevo", "total_printed": 1},
                }
            ],
            writer,
        )
        commit = DataDeskChange.objects.filter(operation="update").first().commit_id

        revert_commit(commit, writer)

        series.refresh_from_db()
        assert series.name == "Exposición de Málaga"
        assert series.total_printed == 500_000

    def test_the_timestamp_moves_so_the_conflict_check_still_sees_it(
        self, series, writer
    ) -> None:
        apply_changes(
            [
                {
                    "model": "issue",
                    "object_id": series.pk,
                    "op": "update",
                    "patch": {"name": "Nombre nuevo"},
                }
            ],
            writer,
        )
        commit = DataDeskChange.objects.filter(operation="update").first().commit_id
        before = Issue.objects.get(pk=series.pk).updated_at

        revert_commit(commit, writer)

        assert Issue.objects.get(pk=series.pk).updated_at > before

    def test_a_lookup_rename_is_undone_the_same_way(self, db, writer) -> None:
        from artists_api.models import Artist
        from datadesk.lookups import rename_lookup

        artist = Artist.objects.create(name="Murillo")
        rename_lookup("artist", artist.pk, "Murillo y taller", writer)
        commit = DataDeskChange.objects.filter(operation="update").first().commit_id

        revert_commit(commit, writer)

        artist.refresh_from_db()
        assert artist.name == "Murillo"


@pytest.mark.django_db
class TestWhatCannotBeReverted:
    """Three refusals, each one with its reason and nothing applied."""

    def test_an_object_changed_after_the_commit(self, series, writer) -> None:
        apply_changes(
            [
                {
                    "model": "issue",
                    "object_id": series.pk,
                    "op": "update",
                    "patch": {"name": "Primero"},
                }
            ],
            writer,
        )
        commit = DataDeskChange.objects.filter(operation="update").first().commit_id
        # Age the commit so the next edit is unambiguously later.
        DataDeskChange.objects.filter(commit_id=commit).update(
            created_at=timezone.now() - timedelta(minutes=5)
        )
        series.refresh_from_db()
        series.name = "Después"
        series.save()

        with pytest.raises(WriteError) as refused:
            revert_commit(commit, writer)

        assert refused.value.status == 409
        assert "changed after this commit" in refused.value.message
        series.refresh_from_db()
        assert series.name == "Después"

    def test_a_merge_commit(self, db, writer) -> None:
        from datadesk.lookups import merge_lookups

        source = Year.objects.create(year=1987)
        target = Year.objects.create(year=1988)
        result = merge_lookups("year", source.pk, target.pk, "a", writer)

        with pytest.raises(WriteError) as refused:
            revert_commit(result.commit_id, writer)

        assert "merge" in refused.value.message
        assert not Year.objects.filter(pk=source.pk).exists()

    def test_a_collision_while_recreating(self, series, writer) -> None:
        stamp_ids = list(series.stamps.values_list("pk", flat=True))
        deletion = delete_series(series.pk, "1987", writer)
        # Somebody else took the id in the meantime.
        Stamp.objects.create(
            id=stamp_ids[0],
            issue=Issue.objects.create(
                year=Year.objects.create(year=1991), name="Otra"
            ),
            name="Intruso",
            face_value="1 Pta",
        )

        with pytest.raises(WriteError) as refused:
            revert_commit(deletion.commit_id, writer)

        assert refused.value.status == 409
        assert not Issue.objects.filter(pk=series.pk).exists()

    def test_an_unknown_commit(self, db) -> None:
        with pytest.raises(WriteError) as refused:
            revert_commit(uuid.uuid4(), None)

        assert refused.value.status == 404


@pytest.mark.django_db
class TestTheScreen:
    """The page, its badges and the one POST on it."""

    def test_it_lists_the_commits(self, staff_client, series) -> None:
        content = staff_client.get(ACTIVITY_URL).content.decode()

        # The log identifies rows by table and id, not by their name.
        assert "Exposición de Málaga" not in content
        assert f"Series #{series.pk}" in content
        assert "Revertible" in content
        assert 'id="revert-' in content

    def test_a_merged_commit_offers_no_button(self, staff_client, db, writer) -> None:
        from datadesk.lookups import merge_lookups

        source = Year.objects.create(year=1987)
        target = Year.objects.create(year=1988)
        merge_lookups("year", source.pk, target.pk, "a", writer)

        content = staff_client.get(ACTIVITY_URL).content.decode()

        assert "Not revertible" in content
        assert "/revert" not in content

    def test_the_post_reverts_and_returns(self, staff_client, series) -> None:
        response = staff_client.post(REVERT_URL.format(commit=commit_of(series)))

        assert response.status_code == 302
        assert response["Location"].endswith(f"?reverted={commit_of(series)}")
        assert Issue.objects.count() == 0

    def test_the_banner_says_so(self, staff_client, series) -> None:
        commit = commit_of(series)
        staff_client.post(REVERT_URL.format(commit=commit))

        content = staff_client.get(f"{ACTIVITY_URL}?reverted={commit}").content.decode()

        assert "The commit was reverted." in content

    def test_a_refusal_answers_with_the_page_and_the_reason(
        self, staff_client, series
    ) -> None:
        commit = commit_of(series)
        staff_client.post(REVERT_URL.format(commit=commit))

        response = staff_client.post(REVERT_URL.format(commit=commit))

        assert response.status_code == 409
        assert b"already reverted" in response.content

    def test_anonymous_cannot_reach_it(self, mounted, series) -> None:
        response = Client().get(ACTIVITY_URL)

        assert response.status_code == 302
        assert response["Location"].startswith("/datadesk/login/")

    def test_anonymous_cannot_revert(self, mounted, series) -> None:
        response = Client().post(REVERT_URL.format(commit=commit_of(series)))

        assert response.status_code == 302
        assert Issue.objects.count() == 1
