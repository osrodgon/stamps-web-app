"""Unit tests for layout components."""

import flet as ft

from components.layout.horizontal_line import HorizontalLine
from components.layout.vertical_line import VerticalLine
from components.colors import SILVER_LIGHT


class TestHorizontalLine:
    """Tests for the HorizontalLine component."""

    def test_default_thickness_is_2(self) -> None:
        """HorizontalLine default height (thickness) is 2."""
        line = HorizontalLine()
        assert line.height == 2

    def test_default_length_is_10(self) -> None:
        """HorizontalLine default width (length) is 10."""
        line = HorizontalLine()
        assert line.width == 10

    def test_custom_thickness_and_length(self) -> None:
        """HorizontalLine accepts custom thickness and length."""
        line = HorizontalLine(thickness=3, length=48)
        assert line.height == 3
        assert line.width == 48

    def test_default_color_is_black(self) -> None:
        """HorizontalLine default bgcolor is BLACK."""
        line = HorizontalLine()
        assert line.bgcolor == ft.Colors.BLACK

    def test_custom_color(self) -> None:
        """HorizontalLine accepts custom color."""
        line = HorizontalLine(color=SILVER_LIGHT)
        assert line.bgcolor == SILVER_LIGHT

    def test_border_radius_is_5(self) -> None:
        """HorizontalLine has border_radius of 5 for rounded edges."""
        line = HorizontalLine()
        assert line.border_radius == 5

    def test_extends_container(self) -> None:
        """HorizontalLine extends ft.Container."""
        line = HorizontalLine()
        assert isinstance(line, ft.Container)


class TestVerticalLine:
    """Tests for the VerticalLine component."""

    def test_default_thickness_is_2(self) -> None:
        """VerticalLine default width (thickness) is 2."""
        line = VerticalLine()
        assert line.width == 2

    def test_default_length_is_100(self) -> None:
        """VerticalLine default height (length) is 100."""
        line = VerticalLine()
        assert line.height == 100

    def test_custom_thickness_and_length(self) -> None:
        """VerticalLine accepts custom thickness and length."""
        line = VerticalLine(thickness=3, length=50)
        assert line.width == 3
        assert line.height == 50

    def test_default_color_is_black(self) -> None:
        """VerticalLine default bgcolor is BLACK."""
        line = VerticalLine()
        assert line.bgcolor == ft.Colors.BLACK

    def test_custom_color(self) -> None:
        """VerticalLine accepts custom color."""
        line = VerticalLine(color=ft.Colors.GREY_300)
        assert line.bgcolor == ft.Colors.GREY_300

    def test_border_radius_is_5(self) -> None:
        """VerticalLine has border_radius of 5 for rounded edges."""
        line = VerticalLine()
        assert line.border_radius == 5

    def test_extends_container(self) -> None:
        """VerticalLine extends ft.Container."""
        line = VerticalLine()
        assert isinstance(line, ft.Container)
