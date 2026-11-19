"""S17 acceptance: copy a series, and delete one with a preview in front of it.

The clone is proven on the writer: a copy keeps the colours and the catalogue
codes, and a gap in the origin is copied instead of refused. The delete is proven
on the writer too, because the check that matters is the typed year and that
happens inside the transaction; the HTTP file proves the gate and the status
codes on top of it.
"""

import json

import pytest
from django.test import Client

from colors_api.models import Color
from collection_items_api.models import CollectionItem
from collections_api.models import Collection
from countries_api.models import Country
from datadesk.dependencies import (
    Dependencies,
    dependency_warning,
    series_dependencies,
)
from datadesk.models import DataDeskChange
from datadesk.write import (
    CLONED_FROM_KEY,
    WriteError,
    clone_series,
    create_series,
    delete_series,
)
from issues_api.models import Issue
from stamps_api.models import Stamp
from years_api.models import Year

STAMP_COUNT = 8
PAGE_URL = "/datadesk/issues/{pk}/"
NEW_URL = "/datadesk/issues/new/"
CLONE_URL = "/datadesk/issues/{pk}/clone"
DEPENDENCIES_URL = "/datadesk/issues/{pk}/dependencies"
DELETE_URL = "/datadesk/issues/{pk}/delete"
JSON = "application/json"


@pytest.fixture
def staff_user(db, django_user_model):
    """The user the writer is called as."""
    return django_user_model.objects.create_user(
        username="writer", password="s3cret-pass", is_staff=True
    )


@pytest.fixture
def red(db) -> Color:
    """A colour, so the copies have something to keep."""
    return Color.objects.create(name="Rojo")


@pytest.fixture
def series(staff_user, red) -> Issue:
    """A series written the way S16 writes one: eight stamps, all coloured."""
    payload = {
        "issue": {
            "year": 1987,
            "date": "1987-05-12",
            "name": "Exposición de Málaga",
            "country": Country.objects.create(name="España").pk,
            "total_printed": 500_000,
            "market_value_mnh": "12.50",
            "perforation": "13 1/4",
        },
        "stamps": [
            {
                "name": f"Sello {index}",
                "face_value": "6 Pta",
                "edifil_code": f"{2744 + index}",
                "colors": [red.pk],
            }
            for index in range(STAMP_COUNT)
        ],
    }
    return create_series(payload, staff_user).issue


@pytest.fixture
def collected(series) -> Collection:
    """A user collection holding three of the stamps of the series."""
    collection = Collection.objects.create(name="Mi colección")
    for stamp in series.stamps.order_by("pk")[:3]:
        CollectionItem.objects.create(collection=collection, stamp=stamp)
    return collection


@pytest.fixture
def staff_client(mounted, django_user_model) -> Client:
    """A logged-in staff client."""
    django_user_model.objects.create_user(
        username="curator", password="s3cret-pass", is_staff=True
    )
    client = Client()
    client.login(username="curator", password="s3cret-pass")
    return client


def post(client: Client, url: str, body=None) -> object:
    """Posts a JSON body the way the page script does."""
    return client.post(url, data=json.dumps(body or {}), content_type=JSON)


def config_of(response) -> dict:
    """Returns the grid configuration the page ships."""
    content = response.content.decode()
    blob = content.split('id="stamp-config" type="application/json">')[1]
    return json.loads(blob.split("</script>")[0])


@pytest.mark.django_db
class TestCloningASeries:
    """A copy is a copy: the values come from the rows, not from a form."""

    def test_keeps_every_stamp_and_its_colours(self, series, staff_user) -> None:
        copy = clone_series(series.pk, None, staff_user)

        assert copy.issue.pk != series.pk
        assert copy.issue.stamps.count() == STAMP_COUNT
        for stamp in copy.issue.stamps.prefetch_related("colors"):
            assert [color.name for color in stamp.colors.all()] == ["Rojo"]

    def test_keeps_the_catalogue_codes(self, series, staff_user) -> None:
        copy = clone_series(series.pk, None, staff_user)

        assert [stamp.edifil_code for stamp in copy.stamps] == [
            str(2744 + index) for index in range(STAMP_COUNT)
        ]

    def test_copies_the_series_values(self, series, staff_user) -> None:
        copy = clone_series(series.pk, None, staff_user)

        assert copy.issue.name == "Exposición de Málaga"
        assert copy.issue.year.year == 1987
        assert copy.issue.date.isoformat() == "1987-05-12"
        assert copy.issue.country.name == "España"
        assert copy.issue.total_printed == 500_000
        assert copy.issue.perforation == "13 1/4"

    def test_the_origin_is_left_alone(self, series, staff_user) -> None:
        clone_series(series.pk, {"year": 1988}, staff_user)

        series.refresh_from_db()
        assert series.year.year == 1987
        assert series.stamps.count() == STAMP_COUNT

    def test_a_new_year_is_created_for_the_copy(self, series, staff_user) -> None:
        """The usual reason to clone: the same set next season."""
        copy = clone_series(series.pk, {"year": 1988}, staff_user)

        assert copy.issue.year.year == 1988
        assert Year.objects.filter(year=1988).exists()

    def test_the_date_can_be_replaced(self, series, staff_user) -> None:
        copy = clone_series(series.pk, {"date": "1988-01-02"}, staff_user)

        assert copy.issue.date.isoformat() == "1988-01-02"

    def test_the_date_can_be_cleared(self, series, staff_user) -> None:
        copy = clone_series(series.pk, {"date": None}, staff_user)

        assert copy.issue.date is None

    def test_a_gap_is_copied_instead_of_refused(self, series, staff_user) -> None:
        """A stamp with no colour is what the copy is for fixing."""
        stamp = series.stamps.order_by("pk").first()
        stamp.colors.clear()
        stamp.face_value = ""
        stamp.save()

        copy = clone_series(series.pk, None, staff_user)

        copied = copy.issue.stamps.order_by("pk").first()
        assert copied.face_value == ""
        assert copied.colors.count() == 0

    def test_an_unknown_series_is_a_404(self, db, staff_user) -> None:
        with pytest.raises(WriteError) as refused:
            clone_series(9999, None, staff_user)

        assert refused.value.status == 404

    def test_an_impossible_year_is_refused(self, series, staff_user) -> None:
        with pytest.raises(WriteError) as refused:
            clone_series(series.pk, {"year": 1700}, staff_user)

        assert "year" in refused.value.errors
        assert Issue.objects.count() == 1

    def test_an_invalid_date_is_refused(self, series, staff_user) -> None:
        with pytest.raises(WriteError) as refused:
            clone_series(series.pk, {"date": "12/05/1987"}, staff_user)

        assert "date" in refused.value.errors
        assert Issue.objects.count() == 1

    def test_every_written_row_is_audited_under_one_commit(
        self, series, staff_user
    ) -> None:
        copy = clone_series(series.pk, None, staff_user)

        changes = DataDeskChange.objects.filter(commit_id=copy.commit_id)
        assert changes.count() == 1 + STAMP_COUNT
        assert {change.operation for change in changes} == {"create"}

    def test_the_series_row_says_where_it_came_from(self, series, staff_user) -> None:
        copy = clone_series(series.pk, None, staff_user)

        issue_change = DataDeskChange.objects.get(
            commit_id=copy.commit_id, model_label="issues_api.Issue"
        )
        assert issue_change.after[CLONED_FROM_KEY] == series.pk
        assert issue_change.after["name"] == "Exposición de Málaga"

    def test_the_stamps_are_not_marked_as_clones(self, series, staff_user) -> None:
        """Provenance belongs to the series; a stamp came from a series."""
        copy = clone_series(series.pk, None, staff_user)

        stamp_changes = DataDeskChange.objects.filter(
            commit_id=copy.commit_id, model_label="stamps_api.Stamp"
        )
        assert all(CLONED_FROM_KEY not in change.after for change in stamp_changes)


@pytest.mark.django_db
class TestTheDependencyPreview:
    """What the delete dialog must say before the button is pressed."""

    def test_counts_stamps_items_and_collections(self, series, collected) -> None:
        dependencies = series_dependencies(series)

        assert isinstance(dependencies, Dependencies)
        assert dependencies.stamps == STAMP_COUNT
        assert dependencies.items == 3

    def test_one_collection_with_three_items_counts_once(
        self, series, collected
    ) -> None:
        """Counting rows would report the same collection three times."""
        dependencies = series_dependencies(series)

        assert dependencies.collections == 1

    def test_two_collections_count_twice(self, series, collected) -> None:
        other = Collection.objects.create(name="Duplicados")
        CollectionItem.objects.create(
            collection=other, stamp=series.stamps.order_by("pk").first()
        )

        assert series_dependencies(series).collections == 2

    def test_a_series_nobody_collected_says_so(self, series) -> None:
        dependencies = series_dependencies(series)

        assert dependencies.items == 0
        assert dependencies.collections == 0
        assert dependency_warning(dependencies) == (
            "No user collection holds these stamps."
        )

    def test_a_collected_series_says_what_is_lost(self, series, collected) -> None:
        warning = dependency_warning(series_dependencies(series))

        assert warning == "These stamps are in user collections, which lose them too."

    def test_a_series_without_stamps_says_so(self, db) -> None:
        empty = Issue.objects.create(year=Year.objects.create(year=1990), name="Vacía")

        assert dependency_warning(series_dependencies(empty)) == (
            "This series has no stamps."
        )


@pytest.mark.django_db
class TestDeletingASeries:
    """The typed year is the check; the dialog is only the way in."""

    def test_a_wrong_year_deletes_nothing(self, series, staff_user) -> None:
        with pytest.raises(WriteError) as refused:
            delete_series(series.pk, "1988", staff_user)

        assert refused.value.status == 400
        assert "confirm" in refused.value.errors
        assert Issue.objects.filter(pk=series.pk).exists()
        assert Stamp.objects.count() == STAMP_COUNT

    def test_the_error_names_the_year_to_type(self, series, staff_user) -> None:
        with pytest.raises(WriteError) as refused:
            delete_series(series.pk, "", staff_user)

        message = refused.value.errors["confirm"][0]
        assert "1987" in message

    def test_the_series_and_its_stamps_are_gone(self, series, staff_user) -> None:
        result = delete_series(series.pk, "1987", staff_user)

        assert not Issue.objects.filter(pk=series.pk).exists()
        assert Stamp.objects.count() == 0
        assert result.dependencies.stamps == STAMP_COUNT

    def test_the_collection_items_go_with_the_cascade(
        self, series, collected, staff_user
    ) -> None:
        result = delete_series(series.pk, "1987", staff_user)

        assert CollectionItem.objects.count() == 0
        assert Collection.objects.count() == 1
        assert result.dependencies.items == 3

    def test_every_removed_row_is_audited(self, series, staff_user) -> None:
        result = delete_series(series.pk, "1987", staff_user)

        changes = DataDeskChange.objects.filter(commit_id=result.commit_id)
        assert changes.count() == 1 + STAMP_COUNT
        assert {change.operation for change in changes} == {"delete"}
        assert all(change.after is None for change in changes)

    def test_the_audit_keeps_what_it_takes_to_rebuild_the_series(
        self, series, staff_user
    ) -> None:
        """S21 recreates the rows from ``before`` and needs the id and the FKs."""
        result = delete_series(series.pk, "1987", staff_user)

        issue_change = DataDeskChange.objects.get(
            commit_id=result.commit_id, model_label="issues_api.Issue"
        )
        assert issue_change.object_id == series.pk
        assert issue_change.before["year_id"] == series.year_id
        assert issue_change.before["name"] == "Exposición de Málaga"

        stamp_change = DataDeskChange.objects.filter(
            commit_id=result.commit_id, model_label="stamps_api.Stamp"
        ).first()
        assert stamp_change.before["issue_id"] == series.pk

    def test_an_unknown_series_is_a_404(self, db, staff_user) -> None:
        with pytest.raises(WriteError) as refused:
            delete_series(9999, "1987", staff_user)

        assert refused.value.status == 404


@pytest.mark.django_db
class TestTheEndpoints:
    """The HTTP boundary: gate, envelope and status codes."""

    def test_anonymous_gets_a_401(self, mounted, series) -> None:
        response = post(Client(HTTP_ACCEPT=JSON), CLONE_URL.format(pk=series.pk))

        assert response.status_code == 401
        assert Issue.objects.count() == 1

    def test_a_non_staff_user_gets_a_403(
        self, mounted, django_user_model, series
    ) -> None:
        django_user_model.objects.create_user(
            username="visitor", password="s3cret-pass", is_staff=False
        )
        client = Client()
        client.login(username="visitor", password="s3cret-pass")

        response = post(client, DELETE_URL.format(pk=series.pk), {"confirm": "1987"})

        assert response.status_code == 403
        assert Issue.objects.count() == 1

    def test_cloning_answers_with_the_url_of_the_copy(
        self, staff_client, series
    ) -> None:
        response = post(staff_client, CLONE_URL.format(pk=series.pk))

        body = response.json()
        assert response.status_code == 200
        assert body["success"] is True
        assert body["commit_id"]
        assert body["data"]["url"] == PAGE_URL.format(pk=body["data"]["issue"]["id"])

    def test_the_preview_returns_the_counts_and_the_warning(
        self, staff_client, series, collected
    ) -> None:
        body = staff_client.get(DEPENDENCIES_URL.format(pk=series.pk)).json()

        assert body["success"] is True
        assert body["data"]["stamps"] == STAMP_COUNT
        assert body["data"]["items"] == 3
        assert body["data"]["collections"] == 1
        assert body["data"]["year"] == 1987
        assert "user collections" in body["data"]["warning"]

    def test_the_preview_of_an_unknown_series_is_a_404(self, staff_client, db) -> None:
        response = staff_client.get(DEPENDENCIES_URL.format(pk=9999))

        assert response.status_code == 404

    def test_a_wrong_year_answers_400_with_the_field(
        self, staff_client, series
    ) -> None:
        response = post(staff_client, DELETE_URL.format(pk=series.pk), {"confirm": "1"})

        assert response.status_code == 400
        assert response.json()["errors"]["confirm"]
        assert Issue.objects.count() == 1

    def test_a_confirmed_delete_answers_200_and_removes_the_series(
        self, staff_client, series
    ) -> None:
        response = post(
            staff_client, DELETE_URL.format(pk=series.pk), {"confirm": "1987"}
        )

        body = response.json()
        assert response.status_code == 200
        assert body["success"] is True
        assert body["data"]["id"] == series.pk
        assert Issue.objects.count() == 0


@pytest.mark.django_db
class TestThePageOffersBoth:
    """The workspace carries the two buttons and the numbers they need."""

    def test_edit_mode_has_the_clone_and_delete_controls(
        self, staff_client, series
    ) -> None:
        content = staff_client.get(PAGE_URL.format(pk=series.pk)).content.decode()

        assert 'id="clone-button"' in content
        assert 'id="delete-button"' in content
        assert 'id="delete-panel"' in content
        assert 'id="delete-confirm"' in content

    def test_new_mode_has_neither(self, staff_client, series) -> None:
        """A series that does not exist cannot be copied or deleted."""
        content = staff_client.get(NEW_URL).content.decode()

        assert 'id="clone-button"' not in content
        assert 'id="delete-button"' not in content
        assert 'id="delete-panel"' not in content

    def test_the_config_carries_the_three_urls(self, staff_client, series) -> None:
        config = config_of(staff_client.get(PAGE_URL.format(pk=series.pk)))

        assert config["cloneUrl"] == CLONE_URL.format(pk=series.pk)
        assert config["dependenciesUrl"] == DEPENDENCIES_URL.format(pk=series.pk)
        assert config["deleteUrl"] == DELETE_URL.format(pk=series.pk)

    def test_the_texts_come_from_the_server(self, staff_client, series) -> None:
        texts = config_of(staff_client.get(PAGE_URL.format(pk=series.pk)))["texts"]

        for key in (
            "cloning",
            "cloneFailed",
            "deleting",
            "deleteFailed",
            "previewFailed",
            "commitFirst",
            "confirmYear",
        ):
            assert texts[key]

        assert texts["confirmYear"] == "Type %(year)s to confirm"
        assert texts["commitFirst"] == ("Commit or discard the pending changes first.")
