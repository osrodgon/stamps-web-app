"""Unit tests for components/form/auto_complete_field.py — AutoCompleteField."""

from typing import Optional

import flet as ft

from components.form.auto_complete_field import AutoCompleteField


sample_items: list[dict] = [
    {"id": 1, "name": "Spain"},
    {"id": 2, "name": "France"},
    {"id": 3, "name": "Germany"},
]


class TestAutoCompleteFieldInit:
    """Tests for AutoCompleteField initialization."""

    def test_selected_id_none_by_default(self) -> None:
        field = AutoCompleteField(items=sample_items)
        assert field.selected_id is None

    def test_text_empty_by_default(self) -> None:
        field = AutoCompleteField(items=sample_items)
        assert field.text == ""

    def test_empty_items_list(self) -> None:
        field = AutoCompleteField(items=[])
        assert field.selected_id is None
        assert field.text == ""

    def test_expand_default_true(self) -> None:
        field = AutoCompleteField(items=sample_items)
        assert field.expand is True

    def test_expand_false(self) -> None:
        field = AutoCompleteField(items=sample_items, expand=False)
        assert field.expand is False

    def test_content_is_dropdown(self) -> None:
        field = AutoCompleteField(items=sample_items)
        assert field.content is field._dropdown

    def test_dropdown_height(self) -> None:
        field = AutoCompleteField(items=sample_items)
        assert field._dropdown.height == 20

    def test_dropdown_text_size(self) -> None:
        field = AutoCompleteField(items=sample_items)
        assert field._dropdown.text_size == 14

    def test_dropdown_dense(self) -> None:
        field = AutoCompleteField(items=sample_items)
        assert field._dropdown.dense is True

    def test_dropdown_no_border(self) -> None:
        field = AutoCompleteField(items=sample_items)
        assert field._dropdown.border == ft.InputBorder.NONE

    def test_dropdown_not_filled(self) -> None:
        field = AutoCompleteField(items=sample_items)
        assert field._dropdown.filled is False

    def test_dropdown_zero_padding(self) -> None:
        field = AutoCompleteField(items=sample_items)
        padding: Optional[ft.Padding] = field._dropdown.content_padding
        assert padding is not None
        assert padding.left == 0
        assert padding.top == 0
        assert padding.right == 0
        assert padding.bottom == 0

    def test_dropdown_editable(self) -> None:
        field = AutoCompleteField(items=sample_items)
        assert field._dropdown.editable is True

    def test_dropdown_enable_filter(self) -> None:
        field = AutoCompleteField(items=sample_items)
        assert field._dropdown.enable_filter is True

    def test_dropdown_enable_search(self) -> None:
        field = AutoCompleteField(items=sample_items)
        assert field._dropdown.enable_search is True

    def test_builds_options_from_items(self) -> None:
        field = AutoCompleteField(items=sample_items)
        options = field._dropdown.options
        assert len(options) == 3
        assert options[0].key == "1"
        assert options[0].text == "Spain"
        assert options[1].key == "2"
        assert options[1].text == "France"

    def test_builds_id_to_name_dict(self) -> None:
        field = AutoCompleteField(items=sample_items)
        assert field._id_to_name == {"1": "Spain", "2": "France", "3": "Germany"}

    def test_dropdown_menu_height(self) -> None:
        field = AutoCompleteField(items=sample_items)
        assert field._dropdown.menu_height == 200

    def test_custom_menu_height(self) -> None:
        field = AutoCompleteField(items=sample_items, suggestions_max_height=150)
        assert field._dropdown.menu_height == 150

    def test_dropdown_menu_style_alignment(self) -> None:
        field = AutoCompleteField(items=sample_items)
        assert field._dropdown.menu_style is not None
        assert field._dropdown.menu_style.alignment == ft.Alignment.BOTTOM_LEFT


class TestAutoCompleteFieldSelectedId:
    """Tests for the selected_id property."""

    def test_selected_id_from_dropdown_value(self) -> None:
        field = AutoCompleteField(items=sample_items)
        field._on_select(ft.ControlEvent(data="2", control=field._dropdown, name="select"))
        assert field.selected_id == 2

    def test_selected_id_none_when_value_empty(self) -> None:
        field = AutoCompleteField(items=sample_items)
        field._on_select(ft.ControlEvent(data="", control=field._dropdown, name="select"))
        assert field.selected_id is None

    def test_selected_id_none_when_data_none(self) -> None:
        field = AutoCompleteField(items=sample_items)
        field._on_select(ft.ControlEvent(data=None, control=field._dropdown, name="select"))
        assert field.selected_id is None

    def test_selected_id_none_for_free_text(self) -> None:
        field = AutoCompleteField(items=sample_items)
        field._on_select(ft.ControlEvent(data=None, control=field._dropdown, name="select"))
        assert field.selected_id is None


class TestAutoCompleteFieldSetText:
    """Tests for set_text()."""

    def test_set_text_matches_option(self) -> None:
        field = AutoCompleteField(items=sample_items)
        field.set_text("France")
        assert field._dropdown.value == "2"
        assert field.selected_id == 2

    def test_set_text_falls_back_to_raw(self) -> None:
        field = AutoCompleteField(items=sample_items)
        field.set_text("Custom stamp type")
        assert field._dropdown.value == "Custom stamp type"
        assert field.selected_id is None

    def test_set_text_empty_string(self) -> None:
        field = AutoCompleteField(items=sample_items)
        field.set_text("")
        assert field._dropdown.value == ""
        assert field.selected_id is None
