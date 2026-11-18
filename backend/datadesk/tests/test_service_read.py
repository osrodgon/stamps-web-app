"""S7 acceptance: the read layer answers with the expected queries and numbers."""
import pytest
from django.apps import apps

from colors_api.models import Color
from countries_api.models import Country
from datadesk import service
from datadesk.registry import LOOKUPS
from issues_api.models import Issue
from stamps_api.models import Stamp
from years_api.models import Year


@pytest.fixture
def dataset(db) -> dict:
    """Small, explicit dataset: every counter has rows and gaps."""
    year = Year.objects.create(year=1987)
    spain = Country.objects.create(name="España")
    color = Color.objects.create(name="Carmín")

    complete = Issue.objects.create(
        year=year, date="1987-05-12", name="Exposición de Málaga", country=spain
    )
    no_country = Issue.objects.create(
        year=year, date="1987-06-01", name="Sin país"
    )
    no_date = Issue.objects.create(year=year, name="Sin fecha", country=spain)
    no_stamps = Issue.objects.create(
        year=year, date="1987-07-01", name="Sin sellos", country=spain
    )

    good = Stamp.objects.create(
        issue=complete, face_value="15 Ptas", name="Retrato", image="stamps/a.jpg"
    )
    good.colors.set([color])
    no_color = Stamp.objects.create(
        issue=complete, face_value="5 Ptas", name="Sin color"
    )
    no_face_value = Stamp.objects.create(
        issue=no_country, face_value="", name="Sin facial", image="stamps/c.jpg"
    )
    no_face_value.colors.set([color])
    dated = Stamp.objects.create(
        issue=no_date, face_value="1 Pta", name="Serie con fecha", image="stamps/d.jpg"
    )
    dated.colors.set([color])

    return {
        "issues": (complete, no_country, no_date, no_stamps),
        "stamps": (good, no_color, no_face_value),
    }


@pytest.mark.django_db
class TestIssueQueryset:
    """The workbench grid is one query, ordered chronologically."""

    def test_the_whole_grid_is_one_query(self, dataset, django_assert_num_queries) -> None:
        with django_assert_num_queries(1):
            rows = list(service.issue_queryset())

        assert len(rows) == 4
        assert rows[0].stamp_count >= 0

    def test_touching_the_lookups_needs_no_extra_query(
        self, dataset, django_assert_num_queries
    ) -> None:
        with django_assert_num_queries(1):
            for issue in service.issue_queryset():
                _ = (issue.year.year, issue.country, issue.name)

    def test_undated_issues_go_last(self, dataset) -> None:
        names = [issue.name for issue in service.issue_queryset()]

        assert names[-1] == "Sin fecha"


@pytest.mark.django_db
class TestPageCost:
    """S9: the page costs the same number of queries whatever its size."""

    def test_page_size_does_not_add_queries(
        self, dataset, django_assert_num_queries
    ) -> None:
        with django_assert_num_queries(2):
            small = service.issue_page(service.IssueFilters(), size=1)
        with django_assert_num_queries(2):
            large = service.issue_page(service.IssueFilters(), size=100)

        assert len(small.data) == 1
        assert len(large.data) == len(dataset["issues"])


@pytest.mark.django_db
class TestStampQueryset:
    """The workspace grid prefetches colors: one query per concern."""

    def test_stamps_and_colors_are_two_queries(
        self, dataset, django_assert_num_queries
    ) -> None:
        issue = dataset["issues"][0]

        with django_assert_num_queries(2):
            stamps = list(service.stamp_queryset(issue.pk))
            for stamp in stamps:
                _ = list(stamp.colors.all())

        assert len(stamps) == 2

    def test_only_the_requested_issue_comes_back(self, dataset) -> None:
        issue, no_country, _, _ = dataset["issues"]

        stamps = list(service.stamp_queryset(issue.pk))

        assert {stamp.issue_id for stamp in stamps} == {issue.pk}
        assert no_country.pk not in {stamp.issue_id for stamp in stamps}


@pytest.mark.django_db
class TestMissingDataReport:
    """The six counters behind the "needs attention" selector."""

    def test_counts_match_the_dataset(self, dataset) -> None:
        report = service.missing_data_report()

        assert report == {
            "issues_without_country": 1,
            "issues_without_date": 1,
            "issues_without_stamps": 1,
            "stamps_without_colors": 1,
            "stamps_without_face_value": 1,
            "stamps_without_image": 1,
        }

    def test_every_report_key_is_covered(self, dataset) -> None:
        assert set(service.missing_data_report()) == set(service.REPORT_KEYS)


class TestLookupRegistry:
    """Every registered lookup exists and points at real relations."""

    def test_the_eight_editable_lookups_are_registered(self) -> None:
        assert set(LOOKUPS) == {
            "year",
            "country",
            "color",
            "artist",
            "printer",
            "paper_type",
            "print_type",
            "stamp_type",
        }

    def test_condition_type_stays_out(self) -> None:
        assert "condition_type" not in LOOKUPS

    def test_each_lookup_points_at_a_real_column(self) -> None:
        for key, lookup in LOOKUPS.items():
            assert lookup.model._meta.get_field(lookup.name_field) is not None, key

    def test_each_declared_reference_exists(self) -> None:
        for key, lookup in LOOKUPS.items():
            for model_label, field_name in lookup.refs:
                model = apps.get_model(model_label)
                assert model._meta.get_field(field_name) is not None, key

    def test_only_years_are_numeric(self) -> None:
        numeric = {key for key, lookup in LOOKUPS.items() if lookup.numeric}

        assert numeric == {"year"}
