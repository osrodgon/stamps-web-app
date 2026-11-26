"""Unit tests for components/collection/collection_card.py.

Flet lets the component be built without a page, so the tests read what it built:
the pictures it chose, the summary it composed and the percentage it painted. The
files are mocked: whether a picture exists is the frontend's business, not the
test's.
"""

from unittest.mock import patch

import pytest

from components.collection.collection_card import CollectionCard
from settings import NO_STAMP


class Cards:
    """Building the data and the component these tests need."""

    @staticmethod
    def data(
        covers: int = 6, series: int = 3, stamps: int = 9, total: int = 14
    ) -> dict:
        """An overview row with as many covers as asked."""
        return {
            "id": 1,
            "name": "Isabel II",
            "series": series,
            "stamps": stamps,
            "total": total,
            "covers": [
                {"year": 1850, "code": f"C{index}"} for index in range(covers)
            ],
        }

    @staticmethod
    def build(
        data: dict,
        lang: str = "en",
        exists: bool = True,
        on_open=None,
    ) -> CollectionCard:
        """A card whose picture files are assumed to exist (or not)."""
        with patch(
            "components.collection.collection_card.os.path.exists", return_value=exists
        ):
            return CollectionCard(data, lang, on_open=on_open)


class TestCover:
    """The collage paints up to six existing files, or the placeholder."""

    def test_no_covers_shows_the_placeholder(self):
        card = Cards.build(Cards.data(covers=0))

        assert len(card._images) == 1
        assert card._images[0].src == NO_STAMP
        assert card._images[0].opacity == 0.55

    def test_one_cover_is_painted_big(self):
        card = Cards.build(Cards.data(covers=1))

        assert len(card._images) == 1
        assert card._images[0].height == CollectionCard.SINGLE_THUMBNAIL_HEIGHT
        assert card._images[0].src.endswith("C0.webp")

    def test_the_source_is_relative_to_the_assets_folder(self):
        card = Cards.build(Cards.data(covers=1))

        assert card._images[0].src.startswith("stamps")
        assert "1850" in card._images[0].src

    def test_six_covers_are_painted(self):
        card = Cards.build(Cards.data(covers=6))

        assert len(card._images) == 6
        assert all(
            image.height == CollectionCard.THUMBNAIL_HEIGHT for image in card._images
        )

    def test_more_than_six_covers_are_capped(self):
        card = Cards.build(Cards.data(covers=12))

        assert len(card._images) == CollectionCard.MAX_COVERS

    def test_missing_files_are_skipped(self):
        def only_one_file(path: str) -> bool:
            return path.endswith("C2.webp")

        with patch(
            "components.collection.collection_card.os.path.exists",
            side_effect=only_one_file,
        ):
            card = CollectionCard(Cards.data(covers=6), "en")

        assert len(card._images) == 1
        assert card._images[0].src.endswith("C2.webp")

    def test_no_existing_file_falls_back_to_the_placeholder(self):
        card = Cards.build(Cards.data(covers=6), exists=False)

        assert len(card._images) == 1
        assert card._images[0].src == NO_STAMP


class TestBody:
    """The name, the counts and the progress line."""

    def test_the_percentage_is_rounded(self):
        card = Cards.build(Cards.data(stamps=9, total=14))

        assert card._percentage.value == "64%"

    def test_the_progress_value_is_the_ratio(self):
        card = Cards.build(Cards.data(stamps=9, total=14))

        assert card._progress.value == pytest.approx(9 / 14)

    def test_an_empty_collection_has_no_percentage(self):
        card = Cards.build(Cards.data(stamps=0, total=0))

        assert card._percentage.value == "—"
        assert card._progress.value == 0

    def test_the_summary_carries_both_counts(self, mocker):
        mocker.patch(
            "components.collection.collection_card._",
            side_effect=lambda key, **values: (
                f"{key}:{values['series']}/{values['stamps']}"
            ),
        )

        card = Cards.build(Cards.data(series=3, stamps=9))

        assert card._summary.value == "collections.summary:3/9"

    def test_zero_counts_read_as_zero(self, mocker):
        mocker.patch(
            "components.collection.collection_card._",
            side_effect=lambda key, **values: f"{values['series']}/{values['stamps']}",
        )

        card = Cards.build(Cards.data(series=0, stamps=0, total=0))

        assert card._summary.value == "0/0"


class TestClick:
    """The card does not pretend to be a link until the route exists."""

    def test_it_is_not_clickable_yet(self):
        card = Cards.build(Cards.data())

        assert card.on_click is None

    def test_it_keeps_the_callback_for_later(self):
        def open_collection(collection_id: int) -> None:
            """Stand-in for the navigation B3 will add."""

        card = Cards.build(Cards.data(), on_open=open_collection)

        assert card._on_open is open_collection
