"""S25 acceptance: delete one stamp, with the preview the series already had.

The interesting cases are the two axes the dialog has to keep straight: whether
anybody holds the stamp, and whether it is the last of its series. Everything
else is S17's pattern applied to one row — audited, restoreable by S21, outside
the change set and outside `/apply`.
"""

import json
import uuid

import pytest
from django.test import Client

from artists_api.models import Artist
from collection_items_api.models import CollectionItem
from collections_api.models import Collection
from countries_api.models import Country
from datadesk.activity import revert_commit
from datadesk.dependencies import (
    stamp_dependencies,
    stamp_warning,
)
from datadesk.models import DataDeskChange
from datadesk.write import WriteError, delete_stamp
from issues_api.models import Issue
from stamps_api.models import Stamp
from years_api.models import Year

PAGE_URL = "/datadesk/issues/{pk}/"
DEPENDENCIES_URL = "/datadesk/stamps/{pk}/dependencies"
DELETE_URL = "/datadesk/stamps/{pk}/delete"
APPLY_URL = "/datadesk/apply"
JSON = "application/json"


@pytest.fixture
def writer(db, django_user_model):
    """The user the writers are called as."""
    return django_user_model.objects.create_user(
        username="writer", password="s3cret-pass", is_staff=True
    )


@pytest.fixture
def series(db, writer) -> Issue:
    """A series with three stamps, written the way the workspace writes one."""
    return Issue.objects.create(
        year=Year.objects.create(year=1987),
        name="Exposición de Málaga",
        country=Country.objects.create(name="España"),
        artist=Artist.objects.create(name="Anónimo"),
        date="1987-05-12",
    )


@pytest.fixture
def stamps(series) -> list[Stamp]:
    """Three stamps with a catalogue code and a colour each."""
    from colors_api.models import Color

    red = Color.objects.create(name="Rojo")
    created = [
        Stamp.objects.create(
            issue=series,
            name=f"Sello {index}",
            face_value="6 Pta",
            edifil_code=f"{2744 + index}",
        )
        for index in range(3)
    ]
    for stamp in created:
        stamp.colors.set([red])
    return created


@pytest.fixture
def held(stamps) -> Collection:
    """A collection holding two of the stamps."""
    collection = Collection.objects.create(name="Mía")
    for stamp in stamps[:2]:
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


@pytest.mark.django_db
class TestThePreview:
    """Two axes: is it collected, and is it the last of the series."""

    def test_counts_the_items_and_their_collections(self, stamps, held) -> None:
        dependencies = stamp_dependencies(stamps[0])

        assert dependencies.items == 1
        assert dependencies.collections == 1
        assert dependencies.siblings == 2

    def test_an_uncollected_stamp_counts_nothing(self, stamps, held) -> None:
        dependencies = stamp_dependencies(stamps[2])

        assert dependencies.items == 0
        assert dependencies.collections == 0
        assert dependencies.collected is False

    def test_the_last_stamp_of_a_series_knows_it(self, series, writer) -> None:
        only = Stamp.objects.create(issue=series, name="Único", face_value="1 Pta")

        dependencies = stamp_dependencies(only)

        assert dependencies.siblings == 0
        assert dependencies.last_of_series is True

    def test_the_sentence_covers_the_four_cases(self, stamps, held) -> None:
        alone = Issue.objects.create(
            year=Year.objects.create(year=1990), name="De un solo sello"
        )
        only = Stamp.objects.create(issue=alone, name="Solo", face_value="1 Pta")
        assert stamp_warning(stamp_dependencies(only)) == (
            "It is the last stamp of the series: the series is left empty."
        )

        CollectionItem.objects.create(collection=held, stamp=only)
        assert stamp_warning(stamp_dependencies(only)) == (
            "It is the last stamp of the series, and its collections go too."
        )

        assert stamp_warning(stamp_dependencies(stamps[0])) == (
            "This stamp is in user collections, which lose it too."
        )
        assert stamp_warning(stamp_dependencies(stamps[2])) == (
            "No user collection holds this stamp."
        )


@pytest.mark.django_db
class TestDeleting:
    """One row, audited, and the cascade takes what it takes."""

    def test_the_stamp_is_gone_and_the_others_stay(self, stamps, writer) -> None:
        result = delete_stamp(stamps[1].pk, writer)

        assert result.stamp_id == stamps[1].pk
        assert result.code == "2745"
        assert Stamp.objects.count() == 2
        assert not Stamp.objects.filter(pk=stamps[1].pk).exists()

    def test_the_collection_items_go_with_the_cascade(
        self, stamps, held, writer
    ) -> None:
        result = delete_stamp(stamps[0].pk, writer)

        assert CollectionItem.objects.count() == 1
        assert result.dependencies.items == 1
        assert Collection.objects.count() == 1

    def test_one_audit_row_with_the_whole_snapshot(self, stamps, writer) -> None:
        colours = sorted(stamps[0].colors.values_list("pk", flat=True))
        result = delete_stamp(stamps[0].pk, writer)

        change = DataDeskChange.objects.get(commit_id=result.commit_id)
        assert change.operation == "delete"
        assert change.object_id == stamps[0].pk
        assert change.after is None
        assert change.before["edifil_code"] == "2744"
        assert change.before["colors"] == colours

    def test_the_last_stamp_leaves_the_series_standing(self, series, writer) -> None:
        only = Stamp.objects.create(issue=series, name="Único", face_value="1 Pta")

        delete_stamp(only.pk, writer)

        assert Issue.objects.filter(pk=series.pk).exists()
        assert series.stamps.count() == 0

    def test_an_unknown_stamp_is_a_404(self, db, writer) -> None:
        with pytest.raises(WriteError) as refused:
            delete_stamp(9999, writer)

        assert refused.value.status == 404

    def test_the_revert_brings_it_back_whole(self, stamps, held, writer) -> None:
        """S21 recreates the row with its id and colours, not its collections."""
        original = stamps[0].pk
        result = delete_stamp(original, writer)

        revert_commit(result.commit_id, writer)

        restored = Stamp.objects.get(pk=original)
        assert [color.name for color in restored.colors.all()] == ["Rojo"]
        # The other stamp of the collection is untouched; the one that went with
        # the deletion does not come back.
        assert CollectionItem.objects.filter(stamp=original).count() == 0
        assert CollectionItem.objects.count() == 1


@pytest.mark.django_db
class TestTheEndpoints:
    """The HTTP boundary: gate, shapes and status codes."""

    def test_the_preview_returns_the_counts_and_the_warning(
        self, staff_client, stamps, held
    ) -> None:
        body = staff_client.get(DEPENDENCIES_URL.format(pk=stamps[0].pk)).json()

        assert body["success"] is True
        assert body["data"]["items"] == 1
        assert body["data"]["collections"] == 1
        assert body["data"]["siblings"] == 2
        assert body["data"]["code"] == "2744"
        assert "user collections" in body["data"]["warning"]

    def test_the_preview_of_an_unknown_stamp_is_a_404(self, staff_client, db) -> None:
        assert staff_client.get(DEPENDENCIES_URL.format(pk=9999)).status_code == 404

    def test_the_delete_answers_200_and_removes_it(self, staff_client, stamps) -> None:
        response = post(staff_client, DELETE_URL.format(pk=stamps[0].pk))

        body = response.json()
        assert response.status_code == 200
        assert body["success"] is True
        assert body["data"]["id"] == stamps[0].pk
        assert Stamp.objects.count() == 2

    def test_an_unknown_stamp_is_a_404(self, staff_client, db) -> None:
        assert post(staff_client, DELETE_URL.format(pk=9999)).status_code == 404

    def test_anonymous_gets_a_401(self, mounted, stamps) -> None:
        response = post(Client(HTTP_ACCEPT=JSON), DELETE_URL.format(pk=stamps[0].pk))

        assert response.status_code == 401
        assert Stamp.objects.count() == 3

    def test_a_non_staff_user_gets_a_403(
        self, mounted, django_user_model, stamps
    ) -> None:
        django_user_model.objects.create_user(
            username="visitor", password="s3cret-pass", is_staff=False
        )
        client = Client()
        client.login(username="visitor", password="s3cret-pass")

        response = post(client, DELETE_URL.format(pk=stamps[0].pk))

        assert response.status_code == 403
        assert Stamp.objects.count() == 3

    def test_apply_still_refuses_a_delete(self, staff_client, stamps) -> None:
        """The deletion path is the dialog, never the change set (S12)."""
        response = post(
            staff_client,
            APPLY_URL,
            {
                "changes": [
                    {
                        "model": "stamp",
                        "object_id": stamps[0].pk,
                        "op": "delete",
                        "patch": {},
                    }
                ]
            },
        )

        assert response.status_code == 409
        assert Stamp.objects.count() == 3


@pytest.mark.django_db
class TestTheGridOffersIt:
    """The row action exists in edit mode, carries its own URLs and nothing else."""

    def config_of(self, response) -> dict:
        content = response.content.decode()
        blob = content.split('id="stamp-config" type="application/json">')[1]
        return json.loads(blob.split("</script>")[0])

    def test_every_row_carries_its_two_urls(self, staff_client, series, stamps) -> None:
        config = self.config_of(staff_client.get(PAGE_URL.format(pk=series.pk)))

        row = config["data"][0]
        assert row["dependencies_url"] == DEPENDENCIES_URL.format(pk=row["id"])
        assert row["delete_url"] == DELETE_URL.format(pk=row["id"])

    def test_new_mode_has_neither(self, staff_client, series) -> None:
        """Nothing to delete before the series exists."""
        config = self.config_of(staff_client.get("/datadesk/issues/new/"))

        assert config["data"] == []

    def test_the_page_renders_the_dialog_and_the_texts(
        self, staff_client, series, stamps
    ) -> None:
        content = staff_client.get(PAGE_URL.format(pk=series.pk)).content.decode()
        config = self.config_of(staff_client.get(PAGE_URL.format(pk=series.pk)))

        assert 'id="stamp-delete-panel"' in content
        assert 'id="stamp-delete-confirm"' in content
        assert config["texts"]["deleteStamp"] == "Delete this stamp"
        assert config["texts"]["stampDeleted"] == "The stamp was deleted."
        assert config["countBadge"] == "stamp-count"
