"""S13 acceptance: one row is edited and committed from the workspace.

The write itself is S12's; what these tests pin is the contract the page needs
to make the commit possible — the baseline (`updated_at`) travelling with every
row, the series row behind the strip, the column-to-field map the grid patches,
and the round trip: commit through ``/datadesk/apply`` and the reloaded page
shows the new value.
"""

import json

import pytest
from django.test import Client

from artists_api.models import Artist
from countries_api.models import Country
from issues_api.models import Issue
from stamp_types_api.models import StampType
from stamps_api.models import Stamp
from years_api.models import Year

PAGE_URL = "/datadesk/issues/{pk}/"
APPLY_URL = "/datadesk/apply"


@pytest.fixture
def issue(db) -> Issue:
    """One series with two stamps, the shortest useful case."""
    created = Issue.objects.create(
        year=Year.objects.create(year=1987),
        name="Exposición de Málaga",
        country=Country.objects.create(name="España"),
        stamp_type=StampType.objects.create(name="Serie conmemorativa"),
        artist=Artist.objects.create(name="Anónimo"),
        date="1987-05-12",
        total_printed=500_000,
        market_value_mnh="1.20",
        perforation="13 1/4",
    )
    Stamp.objects.create(
        issue=created, name="Sello A", face_value="6 Pta", edifil_code="2744"
    )
    Stamp.objects.create(
        issue=created, name="Sello B", face_value="12 Pta", edifil_code="2745"
    )
    return created


@pytest.fixture
def staff_client(mounted, django_user_model) -> Client:
    """A logged-in staff client."""
    django_user_model.objects.create_user(
        username="curator", password="s3cret-pass", is_staff=True
    )
    client = Client()
    client.login(username="curator", password="s3cret-pass")
    return client


def config_of(response) -> dict:
    """Returns the grid configuration the page ships."""
    content = response.content.decode()
    blob = content.split('id="stamp-config" type="application/json">')[1]
    return json.loads(blob.split("</script>")[0])


def post(client: Client, url: str, body) -> object:
    """Posts a JSON body the way the page script does."""
    return client.post(url, data=json.dumps(body), content_type="application/json")


@pytest.mark.django_db
class TestTheRowsCarryTheirBaseline:
    """Without `updated_at` the client cannot detect a row changed elsewhere."""

    def test_every_row_has_the_timestamp_it_was_read_at(
        self, staff_client, issue
    ) -> None:
        rows = config_of(staff_client.get(PAGE_URL.format(pk=issue.pk)))["data"]
        stamps = {stamp.pk: stamp for stamp in Stamp.objects.all()}

        assert [row["updated_at"] for row in rows] == [
            stamps[row["id"]].updated_at.isoformat() for row in rows
        ]

    def test_a_row_without_a_timestamp_still_travels(self, staff_client, issue) -> None:
        Stamp.objects.filter(issue=issue).update(updated_at=None)

        rows = config_of(staff_client.get(PAGE_URL.format(pk=issue.pk)))["data"]

        assert [row["updated_at"] for row in rows] == [None, None]


@pytest.mark.django_db
class TestTheGridKnowsWhatItMayEdit:
    """The column definitions decide which cells open an editor."""

    def test_the_stamp_fields_map_to_their_model_column(
        self, staff_client, issue
    ) -> None:
        columns = config_of(staff_client.get(PAGE_URL.format(pk=issue.pk)))["columns"]
        patches = {column["field"]: column.get("patch") for column in columns}

        assert patches["edifil"] == "edifil_code"
        assert patches["fesofi"] == "fesofi_code"
        assert patches["mnh"] == "market_value_mnh"
        assert patches["used"] == "market_value_used"

    def test_colours_and_the_picture_are_read_only(self, staff_client, issue) -> None:
        columns = config_of(staff_client.get(PAGE_URL.format(pk=issue.pk)))["columns"]

        read_only = {column["field"] for column in columns if not column.get("patch")}
        assert read_only == {"colors", "has_image"}

    def test_only_total_printed_uses_the_numeric_editor(
        self, staff_client, issue
    ) -> None:
        columns = config_of(staff_client.get(PAGE_URL.format(pk=issue.pk)))["columns"]

        numeric = [column["field"] for column in columns if column.get("editor")]
        assert numeric == ["total_printed"]


@pytest.mark.django_db
class TestTheSeriesStripIsAForm:
    """The strip edits the series row, with the same fifteen fields as S11."""

    def test_the_fields_arrive_with_the_stored_value(self, staff_client, issue) -> None:
        response = staff_client.get(PAGE_URL.format(pk=issue.pk))
        fields = {field["name"]: field for field in response.context["form_fields"]}

        assert fields["year"]["value"] == 1987
        assert fields["name"]["value"] == "Exposición de Málaga"
        assert fields["date"]["value"] == "1987-05-12"
        assert fields["country"]["value"] == issue.country_id
        assert fields["total_printed"]["value"] == 500_000
        assert fields["market_value_mnh"]["value"] == "1.20"
        assert fields["perforation"]["value"] == "13 1/4"

    def test_the_current_lookup_is_selected(self, staff_client, issue) -> None:
        response = staff_client.get(PAGE_URL.format(pk=issue.pk))
        fields = {field["name"]: field for field in response.context["form_fields"]}
        selected = [
            option for option in fields["country"]["options"] if option["selected"]
        ]

        assert [option["value"] for option in selected] == [issue.country_id]

    def test_the_config_carries_the_series_baseline(self, staff_client, issue) -> None:
        config = config_of(staff_client.get(PAGE_URL.format(pk=issue.pk)))

        assert config["series"] == {
            "id": issue.pk,
            "updated_at": issue.updated_at.isoformat(),
        }
        assert config["applyUrl"] == APPLY_URL

    def test_the_commit_texts_come_from_the_server(self, staff_client, issue) -> None:
        texts = config_of(staff_client.get(PAGE_URL.format(pk=issue.pk)))["texts"]

        assert set(texts) == {
            "saved",
            "rejected",
            "noChanges",
            "saving",
            "backupSaved",
            "backupFailed",
            "cloning",
            "cloneFailed",
            "deleting",
            "deleteFailed",
            "previewFailed",
            "commitFirst",
            "confirmYear",
        }

    def test_the_plurals_are_resolved_by_the_server(self, staff_client, issue) -> None:
        plurals = config_of(staff_client.get(PAGE_URL.format(pk=issue.pk)))["plurals"]

        assert plurals["changes"] == {
            "one": "%(count)s change",
            "other": "%(count)s changes",
        }
        assert set(plurals) == {"changes", "recover", "commit"}
        assert plurals["commit"] == {
            "one": "Commit %(count)s change",
            "other": "Commit %(count)s changes",
        }

    def test_the_plurals_follow_the_language(self, staff_client, issue) -> None:
        staff_client.cookies["django_language"] = "es"

        plurals = config_of(staff_client.get(PAGE_URL.format(pk=issue.pk)))["plurals"]

        assert plurals["changes"] == {
            "one": "%(count)s cambio",
            "other": "%(count)s cambios",
        }

    def test_the_field_labels_come_from_the_editor(self, staff_client, issue) -> None:
        labels = config_of(staff_client.get(PAGE_URL.format(pk=issue.pk)))[
            "fieldLabels"
        ]

        assert len(labels["issue"]) == 15
        assert labels["issue"]["name"] == "Name"
        assert labels["issue"]["market_value_mnh"] == "Market value MNH"
        assert labels["stamp"] == {
            "edifil_code": "Edifil",
            "fesofi_code": "Fesofi",
            "name": "Name",
            "face_value": "Face value",
            "total_printed": "Total printed",
            "market_value_mnh": "MNH",
            "market_value_used": "Used",
        }

    def test_the_model_labels_are_translated(self, staff_client, issue) -> None:
        config = config_of(staff_client.get(PAGE_URL.format(pk=issue.pk)))

        assert config["modelLabels"] == {"issue": "Series", "stamp": "Stamps"}

    def test_the_config_carries_the_backup_settings(self, staff_client, issue) -> None:
        config = config_of(staff_client.get(PAGE_URL.format(pk=issue.pk)))

        assert config["backupUrl"] == "/datadesk/backup"
        assert config["backupThreshold"] == 20

    def test_the_config_carries_the_draft_settings(self, staff_client, issue) -> None:
        config = config_of(staff_client.get(PAGE_URL.format(pk=issue.pk)))

        assert config["storageKey"] == f"datadesk:buffer:edit:{issue.pk}"
        assert config["schemaVersion"] == 1
        assert config["undoLimit"] == 200

    def test_the_page_offers_the_shortcut_and_the_button(
        self, staff_client, issue
    ) -> None:
        content = staff_client.get(PAGE_URL.format(pk=issue.pk)).content.decode()

        assert 'id="commit-status"' in content
        assert 'id="commit-button"' in content
        assert 'name="csrf-token"' in content

    def test_the_footer_carries_the_change_set_controls(
        self, staff_client, issue
    ) -> None:
        content = staff_client.get(PAGE_URL.format(pk=issue.pk)).content.decode()

        for element in (
            "change-count",
            "undo-button",
            "redo-button",
            "discard-button",
            "recovery-bar",
            "recover-button",
            "recovery-discard",
            "tab-notice",
        ):
            assert f'id="{element}"' in content

    def test_the_review_panel_is_rendered(self, staff_client, issue) -> None:
        content = staff_client.get(PAGE_URL.format(pk=issue.pk)).content.decode()

        for element in (
            "review-panel",
            "review-button",
            "review-body",
            "review-close",
            "backup-button",
            "backup-status",
        ):
            assert f'id="{element}"' in content

        # The commit lives in the panel now, not in the footer.
        assert content.index('id="review-panel"') < content.index('id="commit-button"')
        assert "Save changes" not in content
        assert "Review changes" in content

    def test_the_controls_start_disabled(self, staff_client, issue) -> None:
        content = staff_client.get(PAGE_URL.format(pk=issue.pk)).content.decode()

        for element in ("commit-button", "discard-button", "undo-button"):
            marker = content.split(f'id="{element}"')[1].split(">")[0]
            assert "disabled" in marker


@pytest.mark.django_db
class TestTheCommitRoundTrip:
    """The value committed is the value the page shows on the next load."""

    def test_a_stamp_change_lands_and_the_page_shows_it(
        self, staff_client, issue
    ) -> None:
        row = config_of(staff_client.get(PAGE_URL.format(pk=issue.pk)))["data"][0]
        change = {
            "model": "stamp",
            "object_id": row["id"],
            "op": "update",
            "patch": {"edifil_code": "2744A"},
            "expected_updated_at": row["updated_at"],
        }

        response = post(staff_client, APPLY_URL, {"changes": [change]})
        body = response.json()
        rows = config_of(staff_client.get(PAGE_URL.format(pk=issue.pk)))["data"]

        assert response.status_code == 200
        assert body["applied"] == 1
        assert body["data"]["rows"][0]["index"] == 0
        assert body["data"]["rows"][0]["updated_at"] is not None
        assert rows[0]["edifil"] == "2744A"

    def test_the_returned_timestamp_is_the_new_baseline(
        self, staff_client, issue
    ) -> None:
        row = config_of(staff_client.get(PAGE_URL.format(pk=issue.pk)))["data"][0]
        first = post(
            staff_client,
            APPLY_URL,
            {
                "changes": [
                    {
                        "model": "stamp",
                        "object_id": row["id"],
                        "op": "update",
                        "patch": {"edifil_code": "1"},
                        "expected_updated_at": row["updated_at"],
                    }
                ]
            },
        ).json()
        baseline = first["data"]["rows"][0]["updated_at"]

        second = post(
            staff_client,
            APPLY_URL,
            {
                "changes": [
                    {
                        "model": "stamp",
                        "object_id": row["id"],
                        "op": "update",
                        "patch": {"edifil_code": "2"},
                        "expected_updated_at": baseline,
                    }
                ]
            },
        ).json()

        assert second["applied"] == 1
        assert second["rejected"] == []

    def test_a_stale_baseline_is_refused(self, staff_client, issue) -> None:
        row = config_of(staff_client.get(PAGE_URL.format(pk=issue.pk)))["data"][0]
        body = post(
            staff_client,
            APPLY_URL,
            {
                "changes": [
                    {
                        "model": "stamp",
                        "object_id": row["id"],
                        "op": "update",
                        "patch": {"edifil_code": "2744B"},
                        "expected_updated_at": "2020-01-01T00:00:00+00:00",
                    }
                ]
            },
        ).json()

        assert body["applied"] == 0
        assert "expected_updated_at" in body["rejected"][0]["errors"]

    def test_a_series_change_lands_and_the_page_shows_it(
        self, staff_client, issue
    ) -> None:
        config = config_of(staff_client.get(PAGE_URL.format(pk=issue.pk)))
        body = post(
            staff_client,
            APPLY_URL,
            {
                "changes": [
                    {
                        "model": "issue",
                        "object_id": config["series"]["id"],
                        "op": "update",
                        "patch": {"perforation": "14"},
                        "expected_updated_at": config["series"]["updated_at"],
                    }
                ]
            },
        ).json()

        reloaded = staff_client.get(PAGE_URL.format(pk=issue.pk))
        fields = {field["name"]: field for field in reloaded.context["form_fields"]}

        assert body["applied"] == 1
        assert config_of(reloaded)["series"]["updated_at"] == (
            body["data"]["rows"][0]["updated_at"]
        )
        assert fields["perforation"]["value"] == "14"
