"""Unit tests for the stamp card with the user's copy (plan step B4).

The card is built on a mocked `ft.Page` (the date picker needs its overlay). The
callbacks are mocked: what is checked is what the card paints, the six fields it
sends and what it does with the answer.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import flet as ft
import pytest

from components.collection.collection_stamp_card import CollectionStampCard
from settings import NO_STAMP


class Texts:
    """Every visible string of a control tree."""

    @classmethod
    def of(cls, control) -> list[str]:
        """Walk the controls and collect the `Text` values."""
        found: list[str] = []
        if isinstance(control, ft.Text):
            found.append(control.value or "")
        for child in (getattr(control, "controls", None) or []):
            found.extend(cls.of(child))
        content = getattr(control, "content", None)
        if content is not None and not isinstance(content, (str, int, float)):
            found.extend(cls.of(content))
        return found


class Cards:
    """Building the data and the card these tests need."""

    ITEM = {
        "id": 4,
        "condition_type": {"id": 1, "name": "Mint"},
        "location": {"id": 2, "name": "Album 1"},
        "quantity": 2,
        "price_paid": "120.00",
        "acquisition_date": "2024-03-12",
        "note": "Small thin on the back",
    }

    @staticmethod
    def stamp(item: dict = None) -> dict:
        """One detail row."""
        return {
            "id": 10,
            "name": "6 cuartos",
            "edifil_code": "1",
            "fesofi_code": "0001",
            "face_value": "6 cuartos",
            "color": ["Negro"],
            "market_value_mnh": "300.00",
            "market_value_used": "30.00",
            "issue_year": "1850",
            "item": item,
        }

    @staticmethod
    def page() -> MagicMock:
        """A page with an overlay and no rendering."""
        page = MagicMock(spec=ft.Page)
        page.overlay = []
        page.update = MagicMock()
        return page

    @classmethod
    def build(cls, item: dict = None, **callbacks) -> CollectionStampCard:
        """A card with the callbacks the test needs."""
        return CollectionStampCard(
            cls.page(),
            cls.stamp(item),
            "en",
            condition_types=[{"id": 1, "name": "Mint"}, {"id": 2, "name": "Used"}],
            locations=[{"id": 2, "name": "Album 1"}],
            **callbacks,
        )


class TestDisplay:
    """The copy, or the button to create it."""

    def test_an_owned_stamp_shows_its_copy(self):
        card = Cards.build(Cards.ITEM)

        texts = Texts.of(card._copy_box)

        assert "Mint" in texts
        assert "Album 1" in texts
        assert "Small thin on the back" in texts

    def test_a_stamp_without_a_copy_offers_to_add_it(self):
        card = Cards.build()

        texts = Texts.of(card._copy_box)

        assert "collections.add_my_copy" in texts

    def test_set_item_repaints_and_reports(self):
        changed = MagicMock()
        card = Cards.build(on_changed=changed)

        card.set_item(Cards.ITEM)

        assert card.item == Cards.ITEM
        assert "Mint" in Texts.of(card._copy_box)
        changed.assert_called_once_with()

    def test_set_item_can_go_back_to_no_copy(self):
        card = Cards.build(Cards.ITEM)

        card.set_item(None)

        assert card.item is None
        assert "collections.add_my_copy" in Texts.of(card._copy_box)


class TestPicture:
    """The picture is the file, or the placeholder."""

    def test_it_paints_the_picture_when_the_file_exists(self):
        with patch(
            "components.collection.collection_stamp_card.os.path.exists",
            return_value=True,
        ):
            card = Cards.build()

        assert card._image.src.endswith("0001.webp")

    def test_a_missing_file_uses_the_placeholder(self):
        with patch(
            "components.collection.collection_stamp_card.os.path.exists",
            return_value=False,
        ):
            card = Cards.build()

        assert card._image.src == NO_STAMP


class TestForm:
    """The six fields, and their two validations."""

    def test_the_form_starts_with_the_current_values(self):
        card = Cards.build(Cards.ITEM)

        card._start_edit(None)

        assert card._quantity.value == "2"
        assert card._paid.value == "120.00"
        assert card._condition.value == "1"
        assert card._location.value == "2"

    def test_the_payload_has_the_six_fields(self):
        card = Cards.build(Cards.ITEM)
        card._start_edit(None)
        card._quantity.value = "3"
        card._note.value = "  a note  "

        payload = card._payload()

        assert payload == {
            "condition_type": 1,
            "quantity": 3,
            "price_paid": "120.00",
            "acquisition_date": "2024-03-12",
            "location": 2,
            "note": "a note",
        }

    def test_a_quantity_below_one_is_refused(self):
        card = Cards.build(Cards.ITEM)
        card._start_edit(None)
        card._quantity.value = "0"

        assert card._payload() is None
        assert card._error.visible is True

    def test_a_non_numeric_price_is_refused(self):
        card = Cards.build(Cards.ITEM)
        card._start_edit(None)
        card._paid.value = "doce"

        assert card._payload() is None
        assert card._error.visible is True


class TestWrites:
    """The card sends and adopts what the API answered."""

    async def test_save_adopts_the_answer(self):
        saved = dict(Cards.ITEM, quantity=3)
        on_save = AsyncMock(return_value=saved)
        card = Cards.build(Cards.ITEM, on_save=on_save)
        card._start_edit(None)
        card._quantity.value = "3"

        await card._save(None)

        assert card.item == saved
        assert on_save.await_count == 1

    async def test_a_refused_save_keeps_the_form(self):
        on_save = AsyncMock(return_value=None)
        card = Cards.build(Cards.ITEM, on_save=on_save)
        card._start_edit(None)

        await card._save(None)

        assert card._editing is True
        assert card._error.visible is True

    async def test_add_adopts_the_new_item(self):
        on_add = AsyncMock(return_value=Cards.ITEM)
        card = Cards.build(on_add=on_add)

        await card._add(None)

        assert card.item == Cards.ITEM

    async def test_remove_asks_once(self):
        card = Cards.build(Cards.ITEM)

        card._confirm_remove(None)

        assert len(card._page.overlay) == 1
        assert card._confirm_dialog.open is True
