"""Unit tests for components/layout/app_header.py — three-area header component."""

import flet as ft

from components.layout.app_header import AppHeader
from components.colors import DARK_BLUE_GREY


class TestAppHeaderInit:
    """Tests for AppHeader initialization and default state."""

    def test_initial_areas_empty(self) -> None:
        header = AppHeader()

        assert header.left_area.controls == []
        assert header.center_area.controls == []
        assert header.right_area.controls == []

    def test_default_height_and_bgcolor(self) -> None:
        header = AppHeader()

        assert header.height == 80
        assert header.bgcolor == DARK_BLUE_GREY

    def test_custom_height(self) -> None:
        header = AppHeader(height=100)

        assert header.height == 100


class TestAppHeaderLeftArea:
    """Tests for left area management."""

    def test_add_left_appends_control(self) -> None:
        header = AppHeader()
        control = ft.Container()

        header.add_left(control)

        assert len(header.left_area.controls) == 1
        assert header.left_area.controls[0] is control

    def test_clear_left_removes_all(self) -> None:
        header = AppHeader()
        header.add_left(ft.Container())
        header.add_left(ft.Container())

        header.clear_left()

        assert header.left_area.controls == []


class TestAppHeaderCenterArea:
    """Tests for center area management."""

    def test_add_center_appends_control(self) -> None:
        header = AppHeader()
        control = ft.Container()

        header.add_center(control)

        assert len(header.center_area.controls) == 1
        assert header.center_area.controls[0] is control

    def test_clear_center_removes_all(self) -> None:
        header = AppHeader()
        header.add_center(ft.Container())

        header.clear_center()

        assert header.center_area.controls == []


class TestAppHeaderRightArea:
    """Tests for right area management."""

    def test_add_right_appends_control(self) -> None:
        header = AppHeader()
        control = ft.Container()

        header.add_right(control)

        assert len(header.right_area.controls) == 1
        assert header.right_area.controls[0] is control

    def test_clear_right_removes_all(self) -> None:
        header = AppHeader()
        header.add_right(ft.Container())
        header.add_right(ft.Container())

        header.clear_right()

        assert header.right_area.controls == []


class TestAppHeaderLayout:
    """Tests for the overall layout structure."""

    def test_content_is_row_with_three_areas(self) -> None:
        header = AppHeader()

        assert isinstance(header.content, ft.Row)
        assert len(header.content.controls) == 3
        assert header.content.controls[0] is header.left_area
        assert header.content.controls[1] is header.center_area
        assert header.content.controls[2] is header.right_area

    def test_center_area_expands(self) -> None:
        header = AppHeader()

        assert header.center_area.expand is True

    def test_left_and_right_do_not_expand(self) -> None:
        header = AppHeader()

        assert header.left_area.expand is not True
        assert header.right_area.expand is not True
