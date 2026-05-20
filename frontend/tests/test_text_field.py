"""Unit tests for components/form/text_field.py."""

from unittest.mock import MagicMock, patch

import flet as ft
import pytest

from components.colors import BLUE_GREY_100, BLUE_700
from components.form.text_field import APP_HEADER, DEFAULT, FieldStyle, TextField


class TestFieldStyle:
    """Tests for the FieldStyle dataclass."""

    def test_default_border_is_underline(self) -> None:
        """FieldStyle default border is UNDERLINE."""
        style = FieldStyle()
        assert style.border == ft.InputBorder.UNDERLINE

    def test_default_expand_is_true(self) -> None:
        """FieldStyle default expand is True."""
        style = FieldStyle()
        assert style.expand is True

    def test_default_border_color_is_blue_grey_100(self) -> None:
        """FieldStyle default border_color is BLUE_GREY_100."""
        style = FieldStyle()
        assert style.border_color == BLUE_GREY_100

    def test_default_focused_border_color_is_blue_700(self) -> None:
        """FieldStyle default focused_border_color is BLUE_700."""
        style = FieldStyle()
        assert style.focused_border_color == BLUE_700

    def test_default_text_size_is_14(self) -> None:
        """FieldStyle default text_size is 14."""
        style = FieldStyle()
        assert style.text_size == 14

    def test_default_color_is_none(self) -> None:
        """FieldStyle default color is None."""
        style = FieldStyle()
        assert style.color is None

    def test_custom_values_override_defaults(self) -> None:
        """FieldStyle accepts custom values that override defaults."""
        style = FieldStyle(
            expand=False,
            border_color="red",
            text_size=16,
        )
        assert style.expand is False
        assert style.border_color == "red"
        assert style.text_size == 16


class TestDefaultPreset:
    """Tests for the DEFAULT FieldStyle preset."""

    def test_default_is_fieldstyle_instance(self) -> None:
        """DEFAULT is a FieldStyle instance."""
        assert isinstance(DEFAULT, FieldStyle)

    def test_default_uses_underline_border(self) -> None:
        """DEFAULT uses UNDERLINE border."""
        assert DEFAULT.border == ft.InputBorder.UNDERLINE

    def test_default_expands(self) -> None:
        """DEFAULT has expand=True."""
        assert DEFAULT.expand is True


class TestAppHeaderPreset:
    """Tests for the APP_HEADER FieldStyle preset."""

    def test_app_header_is_fieldstyle_instance(self) -> None:
        """APP_HEADER is a FieldStyle instance."""
        assert isinstance(APP_HEADER, FieldStyle)

    def test_app_header_does_not_expand(self) -> None:
        """APP_HEADER has expand=False."""
        assert APP_HEADER.expand is False

    def test_app_header_border_color_is_grey_500(self) -> None:
        """APP_HEADER border_color is GREY_500."""
        assert APP_HEADER.border_color == ft.Colors.GREY_500

    def test_app_header_focused_border_color_is_grey_500(self) -> None:
        """APP_HEADER focused_border_color is GREY_500."""
        assert APP_HEADER.focused_border_color == ft.Colors.GREY_500

    def test_app_header_text_color_is_white(self) -> None:
        """APP_HEADER color is WHITE."""
        assert APP_HEADER.color == ft.Colors.WHITE

    def test_app_header_cursor_color_is_grey_500(self) -> None:
        """APP_HEADER cursor_color is GREY_500."""
        assert APP_HEADER.cursor_color == ft.Colors.GREY_500

    def test_app_header_border_width_is_1(self) -> None:
        """APP_HEADER border_width is 1."""
        assert APP_HEADER.border_width == 1

    def test_app_header_focused_border_width_is_2(self) -> None:
        """APP_HEADER focused_border_width is 2."""
        assert APP_HEADER.focused_border_width == 2

    def test_app_header_has_content_padding(self) -> None:
        """APP_HEADER has content_padding set."""
        assert APP_HEADER.content_padding is not None
        assert APP_HEADER.content_padding.bottom == 0
        assert APP_HEADER.content_padding.top == 0


class TestTextField:
    """Tests for the TextField component."""

    @patch("components.form.text_field.ft.TextField")
    def test_label_is_set(self, mock_tf: MagicMock) -> None:
        """TextField sets the label attribute."""
        tf = TextField(label="Username")
        assert tf.label == "Username"

    @patch("components.form.text_field.ft.TextField")
    def test_password_mode_disabled_by_default(self, mock_tf: MagicMock) -> None:
        """TextField password is False by default."""
        tf = TextField(label="Username")
        assert tf.password is False

    @patch("components.form.text_field.ft.TextField")
    def test_password_mode_enabled(self, mock_tf: MagicMock) -> None:
        """TextField password is True when specified."""
        tf = TextField(label="Password", password=True)
        assert tf.password is True

    @patch("components.form.text_field.ft.TextField")
    def test_can_reveal_password(self, mock_tf: MagicMock) -> None:
        """TextField can_reveal_password is set when specified."""
        tf = TextField(label="Password", password=True, can_reveal_password=True)
        assert tf.can_reveal_password is True

    @patch("components.form.text_field.ft.TextField")
    def test_font_family_is_roboto(self, mock_tf: MagicMock) -> None:
        """TextField font_family is Roboto."""
        tf = TextField(label="Username")
        assert tf.font_family == "Roboto"

    @patch("components.form.text_field.ft.TextField")
    def test_uses_default_field_style(self, mock_tf: MagicMock) -> None:
        """TextField uses DEFAULT FieldStyle when no field_style provided."""
        tf = TextField(label="Username")
        assert tf.border_color == BLUE_GREY_100
        assert tf.focused_border_color == BLUE_700
        assert tf.text_size == 14
        assert tf.expand is True
        assert tf.border == ft.InputBorder.UNDERLINE

    @patch("components.form.text_field.ft.TextField")
    def test_uses_app_header_field_style(self, mock_tf: MagicMock) -> None:
        """TextField uses APP_HEADER FieldStyle when specified."""
        tf = TextField(label="Search", field_style=APP_HEADER)
        assert tf.expand is False
        assert tf.border_color == ft.Colors.GREY_500
        assert tf.focused_border_color == ft.Colors.GREY_500
        assert tf.color == ft.Colors.WHITE

    @patch("components.form.text_field.ft.TextField")
    def test_explicit_border_color_overrides_field_style(
        self, mock_tf: MagicMock
    ) -> None:
        """Explicit border_color overrides FieldStyle defaults."""
        tf = TextField(label="Username", border_color="red")
        assert tf.border_color == "red"

    @patch("components.form.text_field.ft.TextField")
    def test_explicit_focused_border_color_overrides_field_style(
        self, mock_tf: MagicMock
    ) -> None:
        """Explicit focused_border_color overrides FieldStyle defaults."""
        tf = TextField(label="Username", focused_border_color="green")
        assert tf.focused_border_color == "green"

    @patch("components.form.text_field.ft.TextField")
    def test_explicit_text_size_overrides_field_style(
        self, mock_tf: MagicMock
    ) -> None:
        """Explicit text_size overrides FieldStyle defaults."""
        tf = TextField(label="Username", text_size=18)
        assert tf.text_size == 18

    @patch("components.form.text_field.ft.TextField")
    def test_explicit_expand_overrides_field_style(
        self, mock_tf: MagicMock
    ) -> None:
        """Explicit expand overrides FieldStyle defaults."""
        tf = TextField(label="Username", expand=False)
        assert tf.expand is False

    @patch("components.form.text_field.ft.TextField")
    def test_explicit_border_overrides_field_style(
        self, mock_tf: MagicMock
    ) -> None:
        """Explicit border overrides FieldStyle defaults."""
        tf = TextField(label="Username", border=ft.InputBorder.OUTLINE)
        assert tf.border == ft.InputBorder.OUTLINE

    @patch("components.form.text_field.ft.TextField")
    def test_on_click_assigned(self, mock_tf: MagicMock) -> None:
        """TextField assigns on_click callback."""
        callback = MagicMock()
        tf = TextField(label="Username", on_click=callback)
        assert tf.on_click is callback

    @patch("components.form.text_field.ft.TextField")
    def test_on_change_assigned(self, mock_tf: MagicMock) -> None:
        """TextField assigns on_change callback."""
        callback = MagicMock()
        tf = TextField(label="Username", on_change=callback)
        assert tf.on_change is callback

    @patch("components.form.text_field.ft.TextField")
    def test_width_assigned(self, mock_tf: MagicMock) -> None:
        """TextField assigns width when specified."""
        tf = TextField(label="Username", width=200)
        assert tf.width == 200
