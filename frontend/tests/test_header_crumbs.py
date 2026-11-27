"""Tests for the breadcrumb that lives in the header (plan D1)."""

from typing import Callable, Optional

import flet as ft
import pytest

from components.buttons.link_button import LinkButton
from components.layout.header_crumbs import LINK_COLOR, HeaderCrumbs


def back(event=None) -> None:
    """A handler for the links the tests build."""
    return None


class Build:
    """The crumb rows these tests read."""

    @staticmethod
    def three() -> HeaderCrumbs:
        """`Collections › Test › Isabel II`, the shape of the detail screen."""
        return HeaderCrumbs(
            [
                ("Collections", back),
                ("Test", back),
                ("Isabel II", None),
            ]
        )


class TestLook:
    """Links in the closures' blue, the current screen in white and bold."""

    def test_the_type_is_the_header_own(self):
        """20px, the size the title had before it carried a path."""
        crumbs = Build.three()

        assert HeaderCrumbs.SIZE == 20
        assert crumbs._steps[0].content.size == 20

    def test_the_links_are_house_links_in_the_header_colour(self):
        crumbs = Build.three()

        link = crumbs._steps[0]

        assert isinstance(link, LinkButton)
        assert link.style.color["default"] == LINK_COLOR
        assert link.style.text_style.decoration == ft.TextDecoration.NONE

    def test_the_current_screen_is_white_and_bold(self):
        label = Build.three()._steps[2]

        assert isinstance(label, ft.Text)
        assert label.value == "Isabel II"
        assert label.color == ft.Colors.WHITE
        assert label.weight == ft.FontWeight.BOLD

    def test_a_step_without_a_handler_is_a_label(self):
        crumbs = HeaderCrumbs([("Only", back), ("Current", None)])

        assert isinstance(crumbs._steps[1], ft.Text)

    def test_separators_go_between_the_steps_only(self):
        crumbs = Build.three()

        separators = [
            control
            for control in crumbs.controls
            if isinstance(control, ft.Text) and control.value == "›"
        ]

        assert len(separators) == 2
        assert crumbs._steps[2].value == "Isabel II"

    def test_a_long_name_is_cut_instead_of_pushing_the_header(self):
        crumbs = Build.three()

        label = crumbs._steps[2]
        assert label.max_lines == 1
        assert label.overflow == ft.TextOverflow.ELLIPSIS
        assert crumbs._steps[0].content.max_lines == 1

    def test_only_the_last_step_takes_the_leftover_width(self):
        """So the path stays contiguous and the tail is what truncates."""
        crumbs = Build.three()

        assert crumbs.expand is True
        assert crumbs.controls[0].expand is False
        assert crumbs.controls[4].expand is True


class TestTexts:
    """The pages fill the names when the API answers."""

    def test_set_text_writes_the_step_and_its_tooltip(self):
        crumbs = Build.three()

        crumbs.set_text(2, "Escudo de España")

        assert crumbs.text(2) == "Escudo de España"
        assert crumbs._steps[2].tooltip == "Escudo de España"

    def test_a_link_can_be_renamed_too(self):
        """The detail's second step is a link and takes the collection's name."""
        crumbs = Build.three()

        crumbs.set_text(1, "Test")

        assert crumbs.text(1) == "Test"
        assert crumbs._steps[1].tooltip == "Test"

    def test_an_index_without_a_step_is_ignored(self):
        crumbs = Build.three()

        crumbs.set_text(9, "nope")

        assert crumbs.text(9) == ""
        assert len(crumbs.controls) == 5

    def test_the_root_screen_is_one_step(self):
        crumbs = HeaderCrumbs([("Collections", None)])

        assert len(crumbs.controls) == 1
        assert crumbs.text(0) == "Collections"
