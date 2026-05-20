"""Unit tests for button components."""

from unittest.mock import MagicMock, patch

import flet as ft
import pytest

from components.buttons.alert_button import AlertButton
from components.buttons.default_button import DefaultButton
from components.buttons.icon_button import IconButton
from components.buttons.link_button import LinkButton
from components.buttons.primary_button import PrimaryButton
from components.buttons.text_button import TextButton
from components.colors import (
    RED,
    RED_HOVER,
    RED_DISABLED,
    SKY_BLUE,
    SKY_BLUE_HOVER,
    SKY_BLUE_DISABLED,
    SLATE_GREY,
    SLATE_GREY_HOVER,
    DARK_BLUE_GREY,
    lighten_color,
)


class TestAlertButton:
    """Tests for the AlertButton component."""

    @patch("components.buttons.alert_button.ft.Text")
    @patch("components.buttons.alert_button.ft.ButtonStyle")
    def test_initialization_sets_red_colors(
        self, mock_style: MagicMock, mock_text: MagicMock
    ) -> None:
        """AlertButton sets RED as default bgcolor."""
        btn = AlertButton(text="Delete")
        assert btn.bgcolor[ft.ControlState.DEFAULT] == RED
        assert btn.bgcolor[ft.ControlState.DISABLED] == RED_DISABLED

    @patch("components.buttons.alert_button.ft.Text")
    @patch("components.buttons.alert_button.ft.ButtonStyle")
    def test_height_is_40(self, mock_style: MagicMock, mock_text: MagicMock) -> None:
        """AlertButton height is 40."""
        btn = AlertButton(text="Delete")
        assert btn.height == 40

    @patch("components.buttons.alert_button.ft.Text")
    @patch("components.buttons.alert_button.ft.ButtonStyle")
    def test_on_click_assigned(
        self, mock_style: MagicMock, mock_text: MagicMock
    ) -> None:
        """AlertButton assigns on_click callback."""
        callback = MagicMock()
        btn = AlertButton(text="Delete", on_click=callback)
        assert btn.on_click is callback

    @patch("components.buttons.alert_button.ft.Text")
    @patch("components.buttons.alert_button.ft.ButtonStyle")
    def test_hover_changes_bgcolor(
        self, mock_style: MagicMock, mock_text: MagicMock
    ) -> None:
        """AlertButton changes bgcolor on hover."""
        btn = AlertButton(text="Delete")
        btn.update = MagicMock()
        hover_event = MagicMock()
        hover_event.data = "true"
        btn._on_hover(hover_event)
        assert btn.bgcolor[ft.ControlState.DEFAULT] == RED_HOVER
        btn.update.assert_called_once()

    @patch("components.buttons.alert_button.ft.Text")
    @patch("components.buttons.alert_button.ft.ButtonStyle")
    def test_hover_out_restores_bgcolor(
        self, mock_style: MagicMock, mock_text: MagicMock
    ) -> None:
        """AlertButton restores bgcolor when not hovered."""
        btn = AlertButton(text="Delete")
        btn.update = MagicMock()
        # First simulate hover to change state
        hover_event = MagicMock()
        hover_event.data = "true"
        btn._on_hover(hover_event)
        # Then simulate hover-out (empty string = not hovered)
        hover_event.data = ""
        btn._on_hover(hover_event)
        assert btn.bgcolor[ft.ControlState.DEFAULT] == RED


class TestDefaultButton:
    """Tests for the DefaultButton component."""

    @patch("components.buttons.default_button.ft.Text")
    @patch("components.buttons.default_button.ft.ButtonStyle")
    def test_initialization_sets_sky_blue_color(
        self, mock_style: MagicMock, mock_text: MagicMock
    ) -> None:
        """DefaultButton sets SKY_BLUE as text color."""
        btn = DefaultButton(text="Cancel")
        assert btn.color == SKY_BLUE

    @patch("components.buttons.default_button.ft.Text")
    @patch("components.buttons.default_button.ft.ButtonStyle")
    def test_height_is_40(self, mock_style: MagicMock, mock_text: MagicMock) -> None:
        """DefaultButton height is 40."""
        btn = DefaultButton(text="Cancel")
        assert btn.height == 40

    @patch("components.buttons.default_button.ft.Text")
    @patch("components.buttons.default_button.ft.ButtonStyle")
    def test_on_click_assigned(
        self, mock_style: MagicMock, mock_text: MagicMock
    ) -> None:
        """DefaultButton assigns on_click callback."""
        callback = MagicMock()
        btn = DefaultButton(text="Cancel", on_click=callback)
        assert btn.on_click is callback

    @patch("components.buttons.default_button.ft.Text")
    @patch("components.buttons.default_button.ft.ButtonStyle")
    def test_data_assigned(self, mock_style: MagicMock, mock_text: MagicMock) -> None:
        """DefaultButton assigns data attribute."""
        btn = DefaultButton(text="Cancel", data={"key": "value"})
        assert btn.data == {"key": "value"}

    @patch("components.buttons.default_button.ft.Text")
    @patch("components.buttons.default_button.ft.ButtonStyle")
    def test_expand_defaults_true(
        self, mock_style: MagicMock, mock_text: MagicMock
    ) -> None:
        """DefaultButton expand defaults to True."""
        btn = DefaultButton(text="Cancel")
        assert btn.expand is True


class TestPrimaryButton:
    """Tests for the PrimaryButton component."""

    @patch("components.buttons.primary_button.ft.Text")
    @patch("components.buttons.primary_button.ft.ButtonStyle")
    def test_initialization_sets_sky_blue_bg(
        self, mock_style: MagicMock, mock_text: MagicMock
    ) -> None:
        """PrimaryButton sets SKY_BLUE as default bgcolor."""
        btn = PrimaryButton(text="Submit")
        assert btn.bgcolor[ft.ControlState.DEFAULT] == SKY_BLUE
        assert btn.bgcolor[ft.ControlState.DISABLED] == SKY_BLUE_DISABLED

    @patch("components.buttons.primary_button.ft.Text")
    @patch("components.buttons.primary_button.ft.ButtonStyle")
    def test_text_color_is_white(
        self, mock_style: MagicMock, mock_text: MagicMock
    ) -> None:
        """PrimaryButton text color is WHITE."""
        btn = PrimaryButton(text="Submit")
        assert btn.color == ft.Colors.WHITE

    @patch("components.buttons.primary_button.ft.Text")
    @patch("components.buttons.primary_button.ft.ButtonStyle")
    def test_hover_changes_bgcolor(
        self, mock_style: MagicMock, mock_text: MagicMock
    ) -> None:
        """PrimaryButton changes bgcolor on hover."""
        btn = PrimaryButton(text="Submit")
        btn.update = MagicMock()
        hover_event = MagicMock()
        hover_event.data = "true"
        btn._on_hover(hover_event)
        assert btn.bgcolor[ft.ControlState.DEFAULT] == SKY_BLUE_HOVER
        btn.update.assert_called_once()

    @patch("components.buttons.primary_button.ft.Text")
    @patch("components.buttons.primary_button.ft.ButtonStyle")
    def test_hover_out_restores_bgcolor(
        self, mock_style: MagicMock, mock_text: MagicMock
    ) -> None:
        """PrimaryButton restores bgcolor when not hovered."""
        btn = PrimaryButton(text="Submit")
        btn.update = MagicMock()
        # First simulate hover to change state
        hover_event = MagicMock()
        hover_event.data = "true"
        btn._on_hover(hover_event)
        # Then simulate hover-out (empty string = not hovered)
        hover_event.data = ""
        btn._on_hover(hover_event)
        assert btn.bgcolor[ft.ControlState.DEFAULT] == SKY_BLUE

    @patch("components.buttons.primary_button.ft.Text")
    @patch("components.buttons.primary_button.ft.ButtonStyle")
    def test_height_is_40(self, mock_style: MagicMock, mock_text: MagicMock) -> None:
        """PrimaryButton height is 40."""
        btn = PrimaryButton(text="Submit")
        assert btn.height == 40


class TestTextButton:
    """Tests for the TextButton component."""

    @patch("components.buttons.text_button.ft.TextButton")
    def test_initialization_sets_slate_grey_color(
        self, mock_text_button: MagicMock
    ) -> None:
        """TextButton sets SLATE_GREY as default color."""
        btn = TextButton(text="Cancel")
        assert btn.style.color["default"] == SLATE_GREY

    @patch("components.buttons.text_button.ft.TextButton")
    def test_hover_color_is_slate_grey_hover(
        self, mock_text_button: MagicMock
    ) -> None:
        """TextButton hover color is SLATE_GREY_HOVER."""
        btn = TextButton(text="Cancel")
        assert btn.style.color["hovered"] == SLATE_GREY_HOVER

    @patch("components.buttons.text_button.ft.TextButton")
    def test_overlay_color_is_transparent(
        self, mock_text_button: MagicMock
    ) -> None:
        """TextButton overlay color is TRANSPARENT."""
        btn = TextButton(text="Cancel")
        assert btn.style.overlay_color == ft.Colors.TRANSPARENT

    @patch("components.buttons.text_button.ft.TextButton")
    def test_on_click_assigned(self, mock_text_button: MagicMock) -> None:
        """TextButton assigns on_click callback."""
        callback = MagicMock()
        btn = TextButton(text="Cancel", on_click=callback)
        assert btn.on_click is callback

    @patch("components.buttons.text_button.ft.TextButton")
    def test_data_assigned(self, mock_text_button: MagicMock) -> None:
        """TextButton assigns data attribute."""
        btn = TextButton(text="Cancel", data={"id": 1})
        assert btn.data == {"id": 1}


class TestLinkButton:
    """Tests for the LinkButton component."""

    @patch("components.buttons.link_button.ft.TextButton")
    def test_initialization_sets_sky_blue_color(
        self, mock_text_button: MagicMock
    ) -> None:
        """LinkButton sets SKY_BLUE as default color."""
        btn = LinkButton(text="Sign Up")
        assert btn.style.color["default"] == SKY_BLUE

    @patch("components.buttons.link_button.ft.TextButton")
    def test_hover_color_is_sky_blue_hover(
        self, mock_text_button: MagicMock
    ) -> None:
        """LinkButton hover color is SKY_BLUE_HOVER."""
        btn = LinkButton(text="Sign Up")
        assert btn.style.color["hovered"] == SKY_BLUE_HOVER

    @patch("components.buttons.link_button.ft.TextButton")
    def test_overlay_color_is_transparent(
        self, mock_text_button: MagicMock
    ) -> None:
        """LinkButton overlay color is TRANSPARENT."""
        btn = LinkButton(text="Sign Up")
        assert btn.style.overlay_color == ft.Colors.TRANSPARENT

    @patch("components.buttons.link_button.ft.TextButton")
    def test_text_decoration_is_underline(
        self, mock_text_button: MagicMock
    ) -> None:
        """LinkButton text style has UNDERLINE decoration."""
        btn = LinkButton(text="Sign Up")
        assert btn.style.text_style.decoration == ft.TextDecoration.UNDERLINE

    @patch("components.buttons.link_button.ft.TextButton")
    def test_on_click_assigned(self, mock_text_button: MagicMock) -> None:
        """LinkButton assigns on_click callback."""
        callback = MagicMock()
        btn = LinkButton(text="Sign Up", on_click=callback)
        assert btn.on_click is callback


class TestIconButton:
    """Tests for the IconButton component."""

    @patch("components.buttons.icon_button.ft.Container")
    def test_initialization_sets_size(
        self, mock_container: MagicMock
    ) -> None:
        """IconButton sets width and height to size."""
        btn = IconButton(icon="add", bgcolor="#333333", size=50)
        assert btn.width == 50
        assert btn.height == 50

    @patch("components.buttons.icon_button.ft.Container")
    def test_border_radius_makes_circular(
        self, mock_container: MagicMock
    ) -> None:
        """IconButton border_radius is half the size (circular)."""
        btn = IconButton(icon="add", bgcolor="#333333", size=40)
        assert btn.border_radius == 20

    @patch("components.buttons.icon_button.ft.Container")
    def test_on_click_assigned(self, mock_container: MagicMock) -> None:
        """IconButton assigns on_click callback."""
        callback = MagicMock()
        btn = IconButton(icon="add", bgcolor="#333333", on_click=callback)
        assert btn.on_click is callback

    @patch("components.buttons.icon_button.ft.Container")
    def test_hover_lightens_bgcolor(self, mock_container: MagicMock) -> None:
        """IconButton lightens bgcolor on hover."""
        btn = IconButton(icon="add", bgcolor=DARK_BLUE_GREY)
        btn.update = MagicMock()
        hover_event = MagicMock()
        hover_event.data = "true"
        btn._on_hover(hover_event)
        expected = lighten_color(DARK_BLUE_GREY, 0.2)
        assert btn.bgcolor == expected
        btn.update.assert_called_once()

    @patch("components.buttons.icon_button.ft.Container")
    def test_hover_out_restores_bgcolor(self, mock_container: MagicMock) -> None:
        """IconButton restores bgcolor when not hovered."""
        btn = IconButton(icon="add", bgcolor=DARK_BLUE_GREY)
        btn.update = MagicMock()
        # First simulate hover to change state
        hover_event = MagicMock()
        hover_event.data = "true"
        btn._on_hover(hover_event)
        # Then simulate hover-out (empty string = not hovered)
        hover_event.data = ""
        btn._on_hover(hover_event)
        assert btn.bgcolor == DARK_BLUE_GREY
