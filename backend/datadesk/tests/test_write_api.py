"""S12 acceptance for the endpoints themselves: gate, CSRF and status codes.

The transactions are proven in ``test_write.py``. What is left here is the part
that only exists at the HTTP boundary: who may call, what happens with a body
that is not JSON, and which status code each refusal gets.
"""

import json

import pytest
from django.test import Client, override_settings

from datadesk.models import DataDeskChange
from datadesk.write import MAX_CHANGES
from issues_api.models import Issue

APPLY_URL = "/datadesk/apply"
BACKUP_URL = "/datadesk/backup"
CREATE_URL = "/datadesk/issues/create"
LOOKUP_URL = "/datadesk/lookups/{key}/create"
JSON = "application/json"


@pytest.fixture
def staff_client(mounted, django_user_model) -> Client:
    """A logged-in staff client."""
    django_user_model.objects.create_user(
        username="curator", password="s3cret-pass", is_staff=True
    )
    client = Client()
    client.login(username="curator", password="s3cret-pass")
    return client


@pytest.fixture
def payload(db) -> dict:
    """The smallest series the create endpoint accepts."""
    return {
        "issue": {"year": 1987, "name": "Serie de prueba"},
        "stamps": [{"name": "Sello 1", "face_value": "6 Pta"}],
    }


def post(client: Client, url: str, body) -> object:
    """Posts a JSON body the way the page scripts do."""
    return client.post(url, data=json.dumps(body), content_type=JSON)


@pytest.mark.django_db
class TestAccess:
    """The endpoints are exactly as protected as the rest of DataDesk."""

    def test_anonymous_gets_401(self, mounted, payload) -> None:
        client = Client(HTTP_ACCEPT=JSON)
        response = post(client, CREATE_URL, payload)

        assert response.status_code == 401
        assert response.json()["success"] is False
        assert Issue.objects.count() == 0

    def test_an_anonymous_browser_is_sent_to_the_login(self, mounted, payload) -> None:
        response = post(Client(), CREATE_URL, payload)

        assert response.status_code == 302
        assert response["Location"].startswith("/datadesk/login/")
        assert Issue.objects.count() == 0

    def test_a_non_staff_user_gets_403(
        self, mounted, django_user_model, payload
    ) -> None:
        django_user_model.objects.create_user(
            username="visitor", password="s3cret-pass", is_staff=False
        )
        client = Client()
        client.login(username="visitor", password="s3cret-pass")

        response = post(client, CREATE_URL, payload)

        assert response.status_code == 403
        assert Issue.objects.count() == 0

    def test_without_csrf_the_write_is_refused(
        self, mounted, django_user_model, payload
    ) -> None:
        django_user_model.objects.create_user(
            username="curator", password="s3cret-pass", is_staff=True
        )
        client = Client(enforce_csrf_checks=True)
        client.login(username="curator", password="s3cret-pass")

        response = post(client, CREATE_URL, payload)

        assert response.status_code == 403
        assert Issue.objects.count() == 0

    def test_the_flag_being_off_hides_the_endpoints(
        self, reload_urlconf, payload
    ) -> None:
        with override_settings(DATADESK_ENABLED=False):
            reload_urlconf()
            response = Client().post(CREATE_URL, data="{}", content_type=JSON)

        assert response.status_code == 404


@pytest.mark.django_db
class TestCreateEndpoint:
    """The series endpoint answers with the ids the client needs."""

    def test_writes_the_series(self, staff_client, payload) -> None:
        response = post(staff_client, CREATE_URL, payload)
        body = response.json()

        assert response.status_code == 200
        assert body["success"] is True
        assert body["applied"] == 2
        assert body["rejected"] == []
        assert body["data"]["issue"]["id"] == Issue.objects.get().pk
        assert body["data"]["issue"]["updated_at"] is not None
        assert len(body["data"]["stamps"]) == 1
        changes = DataDeskChange.objects.filter(commit_id=body["commit_id"])
        assert changes.count() == 2

    def test_a_bad_stamp_answers_400_and_writes_nothing(
        self, staff_client, payload
    ) -> None:
        payload["stamps"][0]["name"] = ""

        response = post(staff_client, CREATE_URL, payload)
        body = response.json()

        assert response.status_code == 400
        assert body["success"] is False
        assert body["errors"]["stamps"]["0"]["name"]
        assert Issue.objects.count() == 0

    def test_a_body_that_is_not_json_answers_400(self, staff_client) -> None:
        response = staff_client.post(CREATE_URL, data="{", content_type=JSON)

        assert response.status_code == 400
        assert response.json()["message"] == "The body is not valid JSON."

    def test_a_body_that_is_not_an_object_answers_400(self, staff_client) -> None:
        response = post(staff_client, CREATE_URL, ["not", "an", "object"])

        assert response.status_code == 400

    def test_get_is_not_allowed(self, staff_client) -> None:
        assert staff_client.get(CREATE_URL).status_code == 405


@pytest.mark.django_db
class TestApplyEndpoint:
    """The batch endpoint reports what it refused instead of failing whole."""

    def test_applies_a_change(self, staff_client, payload) -> None:
        post(staff_client, CREATE_URL, payload)
        issue = Issue.objects.get()

        response = post(
            staff_client,
            APPLY_URL,
            {
                "changes": [
                    {
                        "model": "issue",
                        "object_id": issue.pk,
                        "op": "update",
                        "patch": {"name": "Otro nombre"},
                    }
                ]
            },
        )
        body = response.json()

        assert response.status_code == 200
        assert body["success"] is True
        assert body["applied"] == 1
        written = body["data"]["rows"][0]
        assert written["index"] == 0
        assert written["id"] == issue.pk
        assert written["updated_at"] is not None
        issue.refresh_from_db()
        assert issue.name == "Otro nombre"

    def test_a_rejected_row_answers_200_with_the_problem(
        self, staff_client, payload
    ) -> None:
        post(staff_client, CREATE_URL, payload)
        issue = Issue.objects.get()
        change = {
            "model": "issue",
            "object_id": issue.pk,
            "op": "update",
            "patch": {"market_value_mnh": "no es un número"},
        }

        response = post(staff_client, APPLY_URL, {"changes": [change]})
        body = response.json()

        assert response.status_code == 200
        assert body["success"] is False
        assert body["applied"] == 0
        assert body["rejected"][0]["index"] == 0

    def test_a_delete_answers_409_and_changes_nothing(
        self, staff_client, payload
    ) -> None:
        post(staff_client, CREATE_URL, payload)
        issue = Issue.objects.get()
        change = {
            "model": "issue",
            "object_id": issue.pk,
            "op": "delete",
            "patch": {},
        }

        response = post(staff_client, APPLY_URL, {"changes": [change]})
        body = response.json()

        assert response.status_code == 409
        assert body["needs_confirmation"] is True
        assert Issue.objects.filter(pk=issue.pk).exists()

    def test_too_many_changes_answer_400(self, staff_client) -> None:
        changes = [{"model": "issue", "object_id": 1, "op": "update", "patch": {}}] * (
            MAX_CHANGES + 1
        )

        response = post(staff_client, APPLY_URL, {"changes": changes})

        assert response.status_code == 400

    def test_a_missing_change_set_answers_400(self, staff_client) -> None:
        assert post(staff_client, APPLY_URL, {}).status_code == 400


@pytest.mark.django_db
class TestLookupEndpoint:
    """A lookup typed into a cell is created once and reused afterwards."""

    def test_creates_the_lookup(self, staff_client) -> None:
        response = post(
            staff_client, LOOKUP_URL.format(key="country"), {"value": "Portugal"}
        )
        body = response.json()

        assert response.status_code == 200
        assert body["created"] is True
        assert body["data"]["name"] == "Portugal"
        assert body["data"]["created"] is True

    def test_a_duplicate_returns_the_existing_row(self, staff_client) -> None:
        post(staff_client, LOOKUP_URL.format(key="country"), {"value": "Portugal"})
        response = post(
            staff_client, LOOKUP_URL.format(key="country"), {"value": "Portugal"}
        )
        body = response.json()

        assert response.status_code == 200
        assert body["created"] is False
        assert DataDeskChange.objects.count() == 1

    def test_an_unknown_lookup_answers_404(self, staff_client) -> None:
        response = post(
            staff_client, LOOKUP_URL.format(key="planet"), {"value": "Marte"}
        )

        assert response.status_code == 404


@pytest.mark.django_db
class TestBackupEndpoint:
    """S15: a dump before a large commit, on demand."""

    @pytest.fixture
    def backups(self, tmp_path, settings):
        """Points BASE_DIR at a scratch folder so the dump lands there."""
        settings.BASE_DIR = tmp_path
        (tmp_path / "backups").mkdir()
        return tmp_path / "backups"

    def test_writes_the_dump_and_names_it(
        self, staff_client, backups, monkeypatch
    ) -> None:
        def fake_call(command, name, mode, stdout) -> None:
            assert command == "stamps_db_backup"
            assert mode == "stamps"
            (backups / f"{name}__stamps.json").write_text("[]")

        monkeypatch.setattr("datadesk.views.write_api.call_command", fake_call)

        response = post(staff_client, BACKUP_URL, {})
        body = response.json()

        assert response.status_code == 200
        assert body["success"] is True
        assert body["data"]["file"].startswith("backups/datadesk-")
        assert body["data"]["file"].endswith("__stamps.json")
        assert (backups / body["data"]["file"].split("/")[-1]).exists()

    def test_a_failing_command_is_reported(
        self, staff_client, backups, monkeypatch
    ) -> None:
        def explode(*args, **kwargs) -> None:
            raise RuntimeError("disco lleno")

        monkeypatch.setattr("datadesk.views.write_api.call_command", explode)

        response = post(staff_client, BACKUP_URL, {})
        body = response.json()

        assert response.status_code == 500
        assert body["success"] is False
        assert "disco lleno" in body["message"]

    def test_a_command_that_writes_nothing_is_reported(
        self, staff_client, backups, monkeypatch
    ) -> None:
        monkeypatch.setattr(
            "datadesk.views.write_api.call_command", lambda *a, **k: None
        )

        response = post(staff_client, BACKUP_URL, {})
        body = response.json()

        assert response.status_code == 500
        assert "did not write a file" in body["message"]

    def test_anonymous_callers_get_401(self, mounted) -> None:
        client = Client(HTTP_ACCEPT=JSON)

        assert client.post(BACKUP_URL).status_code == 401

    def test_a_non_staff_user_is_refused(self, mounted, django_user_model) -> None:
        django_user_model.objects.create_user(username="pepe", password="s3cret-pass")
        client = Client()
        client.login(username="pepe", password="s3cret-pass")

        assert client.post(BACKUP_URL).status_code == 403

    def test_get_is_not_allowed(self, staff_client) -> None:
        assert staff_client.get(BACKUP_URL).status_code == 405
