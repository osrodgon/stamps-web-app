"""S5 acceptance: `Stamp.updated_at` is internal bookkeeping.

The column exists for DataDesk's conflict detection, so it must be stamped on
every save, stay out of the public API and be read-only in the admin.
"""
from datetime import timedelta

import pytest
from django.contrib.admin.sites import site
from django.utils import timezone

from common.test.colors_api_test_data import colors_table  # noqa: F401
from common.test.countries_api_test_data import countries_table  # noqa: F401
from common.test.issues_api_test_data import issues_table  # noqa: F401
from common.test.print_types_api_test_data import print_types_table  # noqa: F401
from common.test.stamp_types_api_test_data import stamp_types_table  # noqa: F401
from common.test.stamps_api_test_data import stamps_table  # noqa: F401
from common.test.year_api_test_data import years_table  # noqa: F401
from stamps_api.api.serializers.stamp_response_serializer import StampResponseSerializer
from stamps_api.models import Stamp


@pytest.mark.django_db
class TestStampUpdatedAt:
    """Timestamp behaviour of the Stamp model."""

    def test_a_new_stamp_is_stamped(self, issues_table) -> None:
        stamp = Stamp.objects.create(
            issue=issues_table[0], face_value="10 Ptas", name="Sello nuevo"
        )

        assert stamp.updated_at is not None

    def test_saving_again_moves_the_timestamp(self, stamps_table) -> None:
        stamp = stamps_table[0]
        old = timezone.now() - timedelta(days=1)
        Stamp.objects.filter(pk=stamp.pk).update(updated_at=old)

        stamp.name = "Nombre corregido"
        stamp.save()
        stamp.refresh_from_db()

        assert stamp.updated_at > old

    def test_the_api_response_does_not_expose_it(self, stamps_table) -> None:
        data = StampResponseSerializer(instance=stamps_table[0]).data

        assert "updated_at" not in data

    def test_the_admin_shows_it_read_only(self) -> None:
        model_admin = site._registry[Stamp]

        assert "updated_at" in model_admin.readonly_fields
