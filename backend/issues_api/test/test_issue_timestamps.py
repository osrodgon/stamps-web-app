"""S5 acceptance: `Issue.updated_at` is internal bookkeeping.

The column exists for DataDesk's conflict detection, so it must be stamped on
every save, stay out of the public API and be read-only in the admin.
"""
from datetime import timedelta

import pytest
from django.contrib.admin.sites import site
from django.utils import timezone

from common.test.countries_api_test_data import countries_table  # noqa: F401
from common.test.issues_api_test_data import issues_table  # noqa: F401
from common.test.print_types_api_test_data import print_types_table  # noqa: F401
from common.test.stamp_types_api_test_data import stamp_types_table  # noqa: F401
from common.test.year_api_test_data import years_table  # noqa: F401
from issues_api.api.serializers.issue_response_serializer import IssueResponseSerializer
from issues_api.models import Issue


@pytest.mark.django_db
class TestIssueUpdatedAt:
    """Timestamp behaviour of the Issue model."""

    def test_a_new_issue_is_stamped(self, years_table) -> None:
        issue = Issue.objects.create(year=years_table[0], name="Nueva emisión")

        assert issue.updated_at is not None

    def test_saving_again_moves_the_timestamp(self, issues_table) -> None:
        issue = issues_table[0]
        old = timezone.now() - timedelta(days=1)
        Issue.objects.filter(pk=issue.pk).update(updated_at=old)

        issue.name = "Nombre corregido"
        issue.save()
        issue.refresh_from_db()

        assert issue.updated_at > old

    def test_the_api_response_does_not_expose_it(self, issues_table) -> None:
        data = IssueResponseSerializer(instance=issues_table[0]).data

        assert "updated_at" not in data

    def test_the_admin_shows_it_read_only(self) -> None:
        model_admin = site._registry[Issue]

        assert "updated_at" in model_admin.readonly_fields
