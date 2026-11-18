"""S6 acceptance: the audit trail snapshots rows and groups them by commit."""
import json

import pytest
from django.contrib.admin.sites import site
from django.test import RequestFactory

from common.test.colors_api_test_data import colors_table  # noqa: F401
from common.test.countries_api_test_data import countries_table  # noqa: F401
from common.test.issues_api_test_data import issues_table  # noqa: F401
from common.test.print_types_api_test_data import print_types_table  # noqa: F401
from common.test.stamp_types_api_test_data import stamp_types_table  # noqa: F401
from common.test.stamps_api_test_data import stamps_table  # noqa: F401
from common.test.year_api_test_data import years_table  # noqa: F401
from datadesk import audit
from datadesk.models import DataDeskChange
from issues_api.models import Issue
from stamps_api.models import Stamp


@pytest.mark.django_db
class TestSnapshot:
    """`snapshot()` describes a row completely and JSON-safely."""

    def test_bookkeeping_fields_stay_out(self, issues_table) -> None:
        data = audit.snapshot(issues_table[0])

        assert "id" not in data
        assert "updated_at" not in data
        assert data["name"] == "Nacimiento de la monarquía"

    def test_decimals_are_stored_as_strings(self, issues_table) -> None:
        issue = Issue.objects.get(pk=issues_table[0].pk)

        data = audit.snapshot(issue)

        assert data["market_value_mnh"] == "5.75"

    def test_dates_are_stored_as_iso_8601(self, issues_table) -> None:
        data = audit.snapshot(issues_table[0])

        assert data["date"] == "1980-05-15"

    def test_foreign_keys_are_stored_as_ids(self, issues_table) -> None:
        issue = issues_table[0]

        data = audit.snapshot(issue)

        assert data["year_id"] == issue.year_id
        assert data["country_id"] == issue.country_id

    def test_colors_are_a_sorted_list_of_ids(self, stamps_table) -> None:
        stamp = stamps_table[0]

        data = audit.snapshot(stamp)

        assert data["colors"] == sorted(stamp.colors.values_list("pk", flat=True))

    def test_the_snapshot_survives_a_json_round_trip(self, stamps_table) -> None:
        data = audit.snapshot(stamps_table[0])

        assert json.loads(json.dumps(data)) == data


@pytest.mark.django_db
class TestRecord:
    """`record()` writes the trail rows the activity screen will read."""

    def test_writes_one_row_with_the_actor(self, stamps_table, django_user_model) -> None:
        user = django_user_model.objects.create_user(
            username="curator", password="s3cret-pass", is_staff=True
        )
        stamp = stamps_table[0]
        commit_id = audit.new_commit_id()

        change = audit.record(
            commit_id,
            user,
            stamp,
            DataDeskChange.UPDATE,
            before=audit.snapshot(stamp),
            after=audit.snapshot(stamp),
        )

        assert change.pk is not None
        assert change.user == user
        assert change.commit_id == commit_id
        assert change.model_label == "stamps_api.Stamp"
        assert change.object_id == stamp.pk

    def test_groups_rows_by_commit_id(self, stamps_table, django_user_model) -> None:
        user = django_user_model.objects.create_user(
            username="curator", password="s3cret-pass", is_staff=True
        )
        commit_id = audit.new_commit_id()

        for stamp in stamps_table:
            audit.record(
                commit_id, user, stamp, DataDeskChange.UPDATE, before=None, after=None
            )

        assert DataDeskChange.objects.filter(commit_id=commit_id).count() == 2

    def test_an_anonymous_actor_is_stored_as_null(self, stamps_table) -> None:
        from django.contrib.auth.models import AnonymousUser

        change = audit.record(
            audit.new_commit_id(),
            AnonymousUser(),
            stamps_table[0],
            DataDeskChange.UPDATE,
            before=None,
            after=None,
        )

        assert change.user is None

    def test_an_unknown_operation_is_rejected(self, stamps_table) -> None:
        with pytest.raises(ValueError):
            audit.record(
                audit.new_commit_id(),
                None,
                stamps_table[0],
                "explode",
                before=None,
                after=None,
            )


class TestAdminIsReadOnly:
    """The trail is consulted in /admin/ but never written or deleted there."""

    def test_add_is_refused(self) -> None:
        model_admin = site._registry[DataDeskChange]
        request = RequestFactory().get("/admin/")

        assert model_admin.has_add_permission(request) is False

    def test_change_is_refused(self) -> None:
        model_admin = site._registry[DataDeskChange]
        request = RequestFactory().get("/admin/")

        assert model_admin.has_change_permission(request) is False

    def test_delete_is_refused(self) -> None:
        model_admin = site._registry[DataDeskChange]
        request = RequestFactory().get("/admin/")

        assert model_admin.has_delete_permission(request) is False


@pytest.mark.django_db
class TestRevertContract:
    """A deleted row can be rebuilt from its snapshot alone (S21)."""

    def test_a_stamp_is_rebuilt_from_its_snapshot(self, stamps_table) -> None:
        stamp = stamps_table[0]
        data = audit.snapshot(stamp)
        colors = data.pop("colors")
        stamp.delete()

        rebuilt = Stamp(**data)
        rebuilt.save()
        rebuilt.colors.set(colors)

        rebuilt.refresh_from_db()
        assert rebuilt.name == stamp.name
        assert rebuilt.face_value == stamp.face_value
        assert rebuilt.market_value_mnh == stamp.market_value_mnh
        assert sorted(rebuilt.colors.values_list("pk", flat=True)) == colors
