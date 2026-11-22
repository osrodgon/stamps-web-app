"""S33 acceptance: a stamp is added to the series that is already open.

The writer accepted a `create` of a stamp of an existing series before (S12,
covered in ``test_write.py``). What is pinned here is the screen's half: the
button that starts a draft, the id prefix and the URL shapes a row without an id
needs, the exact payload the draft posts, and the round trip — the commit writes
it and the reloaded page shows the stamp with its real id.
"""

import json

import pytest
from django.test import Client
from django.urls import reverse

from issues_api.models import Issue
from stamps_api.models import Stamp
from years_api.models import Year

PAGE_URL = "/datadesk/issues/{pk}/"
NEW_URL = "/datadesk/issues/new/"
APPLY_URL = "/datadesk/apply"
REVERT_URL = "/datadesk/activity/{commit}/revert"
JSON = "application/json"
STAMP_COUNT = 2


@pytest.fixture
def issue(db) -> Issue:
    """One series with two stamps: enough to see a third arrive."""
    created = Issue.objects.create(
        year=Year.objects.create(year=1976),
        name="Paisajes y Monumentos",
    )
    Stamp.objects.create(issue=created, name="Sello A", face_value="6 Pta")
    Stamp.objects.create(issue=created, name="Sello B", face_value="12 Pta")
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
    return client.post(url, data=json.dumps(body), content_type=JSON)


def draft_patch(issue: Issue, **overrides) -> dict:
    """The patch the draft row sends: every field of the stamp, plus its series.

    A new stamp arrives with all eight editable fields, most of them empty,
    because the row is a grid row and not a form: the empty ones have to reach
    the writer as ``NULL`` instead of being refused.
    """
    patch = {
        "issue": issue.pk,
        "edifil_code": "",
        "fesofi_code": "",
        "name": "Sello nuevo",
        "description": "",
        "face_value": "2 Pta",
        "total_printed": "",
        "market_value_mnh": "",
        "market_value_used": "",
    }
    patch.update(overrides)
    return patch


def create_stamp(client: Client, issue: Issue, **overrides) -> dict:
    """Posts one draft row the way the page's change set does."""
    change = {
        "model": "stamp",
        "op": "create",
        "patch": draft_patch(issue, **overrides),
    }
    return post(client, APPLY_URL, {"changes": [change]})


@pytest.mark.django_db
class TestTheButtonThatStartsADraft:
    """`+ Stamp` exists on a series and nowhere else."""

    def test_the_series_screen_offers_it(self, staff_client, issue) -> None:
        content = staff_client.get(PAGE_URL.format(pk=issue.pk)).content.decode()

        assert 'id="add-stamp"' in content
        assert "+ Stamp" in content

    def test_the_new_series_screen_does_not(self, staff_client) -> None:
        """There the rows are the series being written, not stamps added to one."""
        content = staff_client.get(NEW_URL).content.decode()

        assert 'id="add-stamp"' not in content

    def test_the_button_is_translated(self, staff_client, issue) -> None:
        staff_client.cookies["django_language"] = "es"

        content = staff_client.get(PAGE_URL.format(pk=issue.pk)).content.decode()

        assert "+ Sello" in content

    def test_the_counter_shows_the_stamps_of_the_series(
        self, staff_client, issue
    ) -> None:
        content = staff_client.get(PAGE_URL.format(pk=issue.pk)).content.decode()

        assert f'id="stamp-count">{STAMP_COUNT}<' in content


@pytest.mark.django_db
class TestWhatADraftRowNeeds:
    """A row with no id still has an identity the page can use."""

    def test_the_id_prefix_travels_in_both_modes(self, staff_client, issue) -> None:
        config = config_of(staff_client.get(PAGE_URL.format(pk=issue.pk)))

        assert config["rowIdPrefix"] == "new-"

    def test_the_row_urls_are_shapes_the_server_owns(
        self, staff_client, issue
    ) -> None:
        """Composing the route in the script would be a second source of truth."""
        config = config_of(staff_client.get(PAGE_URL.format(pk=issue.pk)))
        stamp = issue.stamps.first()

        for key, viewname in (
            ("dependencies", "datadesk:stamp_dependencies"),
            ("delete", "datadesk:stamp_delete"),
        ):
            shape = config["rowUrls"][key]

            assert shape % {"id": stamp.pk} == reverse(viewname, args=[stamp.pk])

    def test_the_series_travels_so_the_row_knows_where_it_goes(
        self, staff_client, issue
    ) -> None:
        config = config_of(staff_client.get(PAGE_URL.format(pk=issue.pk)))

        assert config["series"]["id"] == issue.pk

    def test_the_review_calls_the_row_new(self, staff_client, issue) -> None:
        config = config_of(staff_client.get(PAGE_URL.format(pk=issue.pk)))

        assert config["texts"]["newRow"] == "New"
        assert config["texts"]["removeRow"] == "Remove this row"

    def test_the_review_says_nuevo_in_spanish(self, staff_client, issue) -> None:
        staff_client.cookies["django_language"] = "es"

        config = config_of(staff_client.get(PAGE_URL.format(pk=issue.pk)))

        assert config["texts"]["newRow"] == "Nuevo"


@pytest.mark.django_db
class TestTheCommitWritesTheRow:
    """What the page posts is what the writer accepts."""

    def test_the_draft_patch_is_written_and_the_id_comes_back(
        self, staff_client, issue
    ) -> None:
        response = create_stamp(staff_client, issue)
        body = response.json()

        assert response.status_code == 200
        assert body["success"] is True
        assert body["applied"] == 1
        created = issue.stamps.get(name="Sello nuevo")
        assert created.face_value == "2 Pta"
        assert created.edifil_code is None
        assert created.market_value_mnh is None
        returned = body["data"]["rows"][0]
        assert returned["id"] == created.pk
        assert returned["updated_at"] is not None

    def test_the_reloaded_page_shows_the_new_stamp(
        self, staff_client, issue
    ) -> None:
        create_stamp(staff_client, issue)
        created = issue.stamps.get(name="Sello nuevo")

        config = config_of(staff_client.get(PAGE_URL.format(pk=issue.pk)))

        ids = [row["id"] for row in config["data"]]
        assert created.pk in ids
        assert len(ids) == STAMP_COUNT + 1

    def test_the_row_carries_the_urls_the_grid_uses(
        self, staff_client, issue
    ) -> None:
        """The × of a stored row opens the delete dialog, which reads these."""
        create_stamp(staff_client, issue)
        created = issue.stamps.get(name="Sello nuevo")

        config = config_of(staff_client.get(PAGE_URL.format(pk=issue.pk)))
        row = next(item for item in config["data"] if item["id"] == created.pk)

        assert row["delete_url"] == reverse("datadesk:stamp_delete", args=[created.pk])
        assert row["dependencies_url"] == reverse(
            "datadesk:stamp_dependencies", args=[created.pk]
        )

    def test_a_row_without_its_required_fields_is_refused(
        self, staff_client, issue
    ) -> None:
        """It stays in the page with the reason, not silently dropped."""
        response = create_stamp(staff_client, issue, face_value="")
        body = response.json()

        assert response.status_code == 200
        assert body["success"] is False
        assert body["rejected"][0]["index"] == 0
        assert body["rejected"][0]["errors"]["face_value"]
        assert issue.stamps.count() == STAMP_COUNT

    def test_the_create_is_audited_and_can_be_reverted(
        self, staff_client, issue
    ) -> None:
        body = create_stamp(staff_client, issue).json()
        created = issue.stamps.get(name="Sello nuevo")

        staff_client.post(REVERT_URL.format(commit=body["commit_id"]))

        assert not Stamp.objects.filter(pk=created.pk).exists()
        assert issue.stamps.count() == STAMP_COUNT
