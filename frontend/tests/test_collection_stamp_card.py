"""Unit tests for the stamp card with the user's copy (plan step B4).

The card is built on a mocked `ft.Page` (the date picker needs its overlay). The
callbacks are mocked: what is checked is what the card paints, the six fields it
sends and what it does with the answer.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import flet as ft
import pytest

from components.collection.collection_stamp_card import CollectionStampCard
from components.form.dropdown import Dropdown as HouseDropdown
from components.form.text_field import TextField as HouseTextField
from core.translations import _
from settings import NO_STAMP


class Texts:
    """Every visible string of a control tree."""

    @classmethod
    def walk(cls, control) -> list:
        """Every control of the tree, containers included."""
        found: list = [control]
        for child in (getattr(control, "controls", None) or []):
            found.extend(cls.walk(child))
        content = getattr(control, "content", None)
        if content is not None and not isinstance(content, (str, int, float)):
            found.extend(cls.walk(content))
        return found

    @classmethod
    def of(cls, control) -> list[str]:
        """Walk the controls and collect the `Text` values."""
        found: list[str] = []
        if isinstance(control, ft.Text):
            found.append(control.value or "")
            found.extend(span.text for span in (control.spans or []))
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
            "colors": ["Negro"],
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

        assert _("collections.add_my_copy") in texts

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
        assert _("collections.add_my_copy") in Texts.of(card._copy_box)


class TestCatalogue:
    """The read-only half, as the mockup: codes, face value, colour and pills."""

    def test_it_shows_the_codes_face_value_and_colour(self):
        card = Cards.build(Cards.ITEM)

        texts = " · ".join(Texts.of(card.content))

        assert "FESOFI " in texts
        assert "0001 · " in texts
        assert "6 cuartos" in texts
        assert "Negro" in texts

    def test_the_picture_is_big_enough_to_read(self):
        """The mockup's 96 read small in a two-column card; it is 128 now."""
        assert CollectionStampCard.PLATE_SIZE == 128

    def test_it_shows_both_values_as_pills(self):
        card = Cards.build(Cards.ITEM)

        texts = Texts.of(card.content)

        assert any("Mint" in text and "300" in text for text in texts)
        assert any("Used" in text and "30" in text for text in texts)


class TestFormLook:
    """The form uses the house controls, like the rest of the collection screens."""

    def test_the_text_fields_are_the_house_ones(self):
        card = Cards.build(Cards.ITEM)
        card._start_edit(None)

        assert isinstance(card._quantity, HouseTextField)
        assert isinstance(card._paid, HouseTextField)
        assert isinstance(card._note, HouseTextField)

    def test_the_selects_are_the_house_dropdowns(self):
        card = Cards.build(Cards.ITEM)
        card._start_edit(None)

        assert isinstance(card._condition, HouseDropdown)
        assert isinstance(card._location, HouseDropdown)

    def test_a_select_without_reference_rows_is_disabled(self):
        card = CollectionStampCard(
            Cards.page(), Cards.stamp(Cards.ITEM), "en", condition_types=[], locations=[]
        )
        card._start_edit(None)

        assert card._condition.disabled is True
        assert card._location.disabled is True


class TestCopyGrid:
    """Six fields in two rows of three, under the `YOUR COPY` caption."""

    def test_it_is_a_grid_of_six_cells(self):
        card = Cards.build(Cards.ITEM)

        rows = [
            control
            for control in card._copy_box.content.controls
            if isinstance(control, ft.Row)
            and control.controls
            and all(isinstance(cell, ft.Column) for cell in control.controls)
        ]

        assert len(rows) == 2
        assert all(len(row.controls) == 3 for row in rows)

    def test_it_offers_the_pencil_then_the_bin(self):
        """Both icons, the app's look, edit before delete."""
        card = Cards.build(Cards.ITEM)

        actions = [
            control
            for control in Texts.walk(card._copy_box)
            if isinstance(control, ft.IconButton)
        ]

        assert [action.icon for action in actions] == [
            ft.Icons.EDIT,
            ft.Icons.DELETE,
        ]
        assert actions[0].tooltip == _("collections.edit")
        assert actions[1].tooltip == _("collections.remove")

    def test_a_stamp_without_a_copy_offers_no_actions(self):
        """Nothing to edit and nothing to delete: only the button to add it."""
        card = Cards.build()

        actions = [
            control
            for control in Texts.walk(card._copy_box)
            if isinstance(control, ft.IconButton)
        ]

        assert actions == []

    def test_the_form_does_not_carry_the_remove_button(self):
        """Removing is the bin beside the pencil, not a button under the fields."""
        card = Cards.build(Cards.ITEM)
        card._start_edit(None)

        texts = " · ".join(Texts.of(card._copy_box))

        assert _("collections.remove") not in texts


class TestLayout:
    """A wrapping Row with an expand child breaks Flutter; these rows do not wrap."""

    def test_the_card_row_does_not_wrap(self):
        card = Cards.build(Cards.ITEM)

        assert card.content.wrap is not True

    def test_the_form_rows_do_not_wrap(self):
        card = Cards.build(Cards.ITEM)
        card._start_edit(None)

        rows = [
            control
            for control in card._copy_box.content.controls
            if isinstance(control, ft.Row)
        ]

        assert rows
        assert all(row.wrap is not True for row in rows)


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
