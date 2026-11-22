"""S7 acceptance: the read layer answers with the expected queries and numbers."""
from datetime import date

import pytest
from django.apps import apps

from datadesk import service
from datadesk.registry import LOOKUPS


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


DAY = date(1998, 12, 29)
SECOND_DAY = date(1998, 12, 30)


@pytest.fixture
def same_day(db) -> dict:
    """Four series on one date (and a second day), only the code differs.

    The names and the creation order are deliberately against the code, so a test
    that expects the code to decide cannot pass by accident.
    """
    from issues_api.models import Issue
    from stamps_api.models import Stamp
    from years_api.models import Year

    year = Year.objects.create(year=1998)
    later = Issue.objects.create(
        year=year, date="1998-12-29", name="Zeta, la primera por código"
    )
    Stamp.objects.create(issue=later, name="A", face_value="1", fesofi_code="3649")
    sooner = Issue.objects.create(
        year=year, date="1998-12-29", name="Alfa, la segunda por código"
    )
    Stamp.objects.create(issue=sooner, name="B", face_value="1", fesofi_code="0022")
    long_code = Issue.objects.create(
        year=year, date="1998-12-29", name="Código largo"
    )
    Stamp.objects.create(
        issue=long_code, name="C", face_value="1", fesofi_code="1998042"
    )
    no_code = Issue.objects.create(year=year, date="1998-12-29", name="Sin código")
    Stamp.objects.create(issue=no_code, name="D", face_value="1")
    return {
        "later": later,
        "sooner": sooner,
        "long": long_code,
        "none": no_code,
        "year": year,
    }


@pytest.mark.django_db
class TestOrderInsideADate:
    """Two series of the same date are decided by the catalogue code (S36).

    The name was the old tiebreak, and it does not survive real data: on
    29-12-1998 there are fifteen series called "España 2000", all with the same
    date, so the order was whatever the database felt like — and with OFFSET
    pagination that can show one row twice and never show another.
    """

    def test_the_code_decides_and_not_the_name(self, same_day) -> None:
        rows = service.sort_issues(service.issue_queryset(), "year", "asc")

        names = [issue.name for issue in rows if issue.date == DAY]

        assert names[:2] == [
            "Alfa, la segunda por código",
            "Zeta, la primera por código",
        ]

    def test_a_shorter_code_comes_first(self, same_day) -> None:
        """``3649`` before ``1998042``: the number, not the text."""
        rows = service.sort_issues(service.issue_queryset(), "year", "asc")

        names = [issue.name for issue in rows if issue.date == DAY]

        assert names.index("Zeta, la primera por código") < names.index(
            "Código largo"
        )

    def test_a_series_without_a_code_goes_last(self, same_day) -> None:
        rows = service.sort_issues(service.issue_queryset(), "year", "asc")

        names = [issue.name for issue in rows if issue.date == DAY]

        assert names[-1] == "Sin código"

    def test_edifil_is_the_fallback(self, same_day) -> None:
        """Fesofi is on almost every stamp; Edifil is missing on a quarter."""
        from issues_api.models import Issue
        from stamps_api.models import Stamp

        only_edifil = Issue.objects.create(
            year=same_day["year"], date="1998-12-29", name="Solo Edifil"
        )
        Stamp.objects.create(
            issue=only_edifil, name="E", face_value="1", edifil_code="0010"
        )
        Stamp.objects.create(
            issue=only_edifil, name="F", face_value="1", fesofi_code=""
        )

        rows = service.sort_issues(service.issue_queryset(), "year", "asc")

        names = [issue.name for issue in rows if issue.date == DAY]

        assert names[0] == "Solo Edifil"

    def test_a_column_sort_also_ends_in_the_code(self, same_day) -> None:
        """Sorting by name leaves the same-name ties to the code, not to the pk."""
        from issues_api.models import Issue
        from stamps_api.models import Stamp

        twin = Issue.objects.create(
            year=same_day["year"], date="1998-12-29", name="Alfa, la segunda por código"
        )
        Stamp.objects.create(issue=twin, name="G", face_value="1", fesofi_code="0030")

        rows = service.sort_issues(service.issue_queryset(), "name", "asc")

        twins = [issue for issue in rows if issue.name == "Alfa, la segunda por código"]

        assert [issue.first_code for issue in twins] == ["0022", "0030"]

    def test_the_pk_makes_the_order_total(self, same_day) -> None:
        """Five identical series: paging by one still returns five rows."""
        from issues_api.models import Issue
        from stamps_api.models import Stamp

        for index in range(4):
            twin = Issue.objects.create(
                year=same_day["year"], date="1998-12-30", name="Gemelas"
            )
            Stamp.objects.create(
                issue=twin, name="H", face_value="1", fesofi_code="9000"
            )

        filters = service.IssueFilters(year_min=1998, year_max=1998)
        last_page = service.issue_page(filters, size=1).last_page
        seen = []
        for page in range(1, last_page + 1):
            rows = service.issue_page(filters, page=page, size=1)
            seen += [row["id"] for row in rows.data]

        twins = [
            issue.pk for issue in service.issue_queryset().filter(date=SECOND_DAY)
        ]
        assert len(set(seen)) == len(seen)
        assert set(twins).issubset(set(seen))

    def test_the_workspace_walks_the_same_order(self, same_day) -> None:
        """The arrows of a series follow the list, code included."""
        positions = service.issue_positions(service.IssueFilters())

        assert positions == [
            row["id"]
            for row in service.issue_page(service.IssueFilters(), size=50).data
        ]


@pytest.mark.django_db
class TestSortingByDate:
    """The one sortable column whose nulls have to go last, both ways."""

    def test_ascending_leaves_the_undated_series_at_the_end(self, dataset) -> None:
        rows = service.sort_issues(service.issue_queryset(), "date", "asc")

        assert [issue.name for issue in rows] == [
            "Exposición de Málaga",
            "Sin país",
            "Sin sellos",
            "Sin fecha",
        ]

    def test_descending_too(self, dataset) -> None:
        rows = service.sort_issues(service.issue_queryset(), "date", "desc")

        assert [issue.name for issue in rows] == [
            "Sin sellos",
            "Sin país",
            "Exposición de Málaga",
            "Sin fecha",
        ]


@pytest.mark.django_db
class TestMissingDataReport:
    """The six counters behind the "needs attention" selector."""

    def test_counts_match_the_dataset(self, dataset) -> None:
        report = service.missing_data_report()

        # One of the four stamps has a picture file, so three are "without".
        # The counter reads the folder, not ``Stamp.image``: that column is
        # empty in every row of the real database.
        assert report == {
            "issues_without_country": 1,
            "issues_without_date": 1,
            "issues_without_stamps": 1,
            "stamps_without_colors": 1,
            "stamps_without_face_value": 1,
            "stamps_without_image": 3,
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
