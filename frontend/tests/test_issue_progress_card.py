"""Unit tests for components/collection/issue_progress_card.py.

Flet builds the row without a page, so the tests read what it painted: the cover it
chose, the progress it shows and the two figures.
"""

from unittest.mock import patch

from components.collection.issue_progress_card import IssueProgressCard
from core.translations import _
from components.table.column_def import fmt_currency
from settings import NO_STAMP


class Rows:
    """Building the data and the component these tests need."""

    @staticmethod
    def data(**overrides) -> dict:
        """One row of the series endpoint."""
        row = {
            "id": 1,
            "year": 1850,
            "date": "1850-01-01",
            "name": "Isabel II",
            "country": "España",
            "stamp_type": "Sello de correo ordinario",
            "cover": {"year": 1850, "code": "1"},
            "total_stamps": 5,
            "owned_stamps": 3,
            "paid": "315.00",
            "catalogue_mnh": "24850.00",
        }
        row.update(overrides)
        return row

    @staticmethod
    def build(data: dict, lang: str = "en", exists: bool = True) -> IssueProgressCard:
        """A row whose cover file is assumed to exist (or not)."""
        with patch(
            "components.collection.issue_progress_card.os.path.exists",
            return_value=exists,
        ):
            return IssueProgressCard(data, lang)


class TestCover:
    """The thumbnail is the cover file, or the placeholder."""

    def test_it_paints_the_cover(self):
        row = Rows.build(Rows.data())

        assert row._image.src.endswith("1.webp")
        assert "1850" in row._image.src
        assert row._image.opacity == 1

    def test_without_a_cover_it_uses_the_placeholder(self):
        row = Rows.build(Rows.data(cover=None))

        assert row._image.src == NO_STAMP
        assert row._image.opacity == 0.55

    def test_a_missing_file_uses_the_placeholder(self):
        row = Rows.build(Rows.data(), exists=False)

        assert row._image.src == NO_STAMP


class TestProgress:
    """The progress text, the bar and the percentage."""

    def test_the_percentage(self):
        row = Rows.build(Rows.data(owned_stamps=3, total_stamps=5))

        assert row._percentage.value == "60%"

    def test_the_bar_value(self):
        row = Rows.build(Rows.data(owned_stamps=3, total_stamps=5))

        assert row._progress_bar.value == 0.6

    def test_a_series_without_stamps_has_no_percentage(self):
        row = Rows.build(Rows.data(owned_stamps=0, total_stamps=0))

        assert row._percentage.value == "—"
        assert row._progress_bar.value == 0

    def test_the_progress_text_comes_from_the_key(self, mocker):
        mocker.patch(
            "components.collection.issue_progress_card._",
            side_effect=lambda key, **values: (
                f"{key}:{values.get('owned')}/{values.get('total')}"
            ),
        )

        row = Rows.build(Rows.data(owned_stamps=3, total_stamps=5))

        assert row._progress_text.value == "collections.progress:3/5"


class TestFigures:
    """What the user paid and what the catalogue says."""

    def test_the_paid_figure(self):
        row = Rows.build(Rows.data(paid="315.00"))

        assert fmt_currency(315.00, "en") in self.__texts(row)

    def test_the_catalogue_figure(self):
        row = Rows.build(Rows.data(catalogue_mnh="24850.00"))

        assert fmt_currency(24850.00, "en") in self.__texts(row)

    def test_a_missing_price_reads_as_a_dash(self):
        row = Rows.build(Rows.data(paid=None))

        assert "-" in self.__texts(row)

    @staticmethod
    def __texts(row: IssueProgressCard) -> list[str]:
        """Every text the row painted."""
        figures = row.content.controls[0].content.controls[3]
        return [
            control.value
            for figure in figures.controls
            for control in figure.controls
        ]


class TestLink:
    """The columns are the link; the bin is outside it, so it cannot open."""

    def test_it_is_not_clickable_without_a_handler(self):
        row = Rows.build(Rows.data())

        assert row._open_area.on_click is None

    def test_it_opens_the_series(self):
        opened = []

        row = IssueProgressCard(Rows.data(), "en", on_open=opened.append)
        row._open_area.on_click(None)

        assert opened == [1]

    def test_the_bin_is_only_there_when_the_page_asks(self):
        plain = Rows.build(Rows.data())
        with_bin = IssueProgressCard(
            Rows.data(), "en", on_open=lambda _id: None, on_remove=lambda _row: None
        )

        assert plain._remove_icon is None
        assert with_bin._remove_icon is not None
        assert with_bin._remove_icon.tooltip == _("collections.remove_series")

    def test_the_bin_reports_the_row_and_does_not_open_it(self):
        removed = []
        opened = []

        row = IssueProgressCard(
            Rows.data(),
            "en",
            on_open=opened.append,
            on_remove=removed.append,
        )
        row._remove_icon.on_click(None)

        assert removed == [Rows.data()]
        assert opened == []
