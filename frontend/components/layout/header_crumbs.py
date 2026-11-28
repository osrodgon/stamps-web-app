"""`Collections › Test › Isabel II`, written for the dark header (plan D1).

The collection screens used to spend a whole row under the header on the breadcrumb,
and the header itself only said "Collections" — the same word the breadcrumb
repeated. This component moves the path into the header, at 14px instead of 12, and
keeps the current screen in white so the eye lands on it.

It is fed with `(text, handler)` pairs: a pair with a handler is a link, the last one
is the current screen and is not. The pages keep the texts up to date with `set_text`,
which is what fills the collection's name when the API answers.
"""

from __future__ import annotations

from typing import Callable, Optional

import flet as ft

from components.buttons.link_button import LinkButton

#: The colour of a crate in the header: a light blue over DARK_BLUE_GREY.
LINK_COLOR: str = ft.Colors.BLUE_200
#: The separator and the muted parts.
SEPARATOR_COLOR: str = ft.Colors.BLUE_GREY_200


class HeaderCrumbs(ft.Row):
    """The path of the screen, in the header, one step per pair.

    The type is the header's own — 20px, the size the title had before it carried
    a path. The last step is the one that takes the leftover width, with an ellipsis
    and a tooltip, so a long collection name truncates instead of pushing the
    header's right side out of the window and the path stays contiguous.

    Args:
        parts: `(text, on_click)` for each step; `None` as the handler makes it a
            label instead of a link. The last one is always the current screen.
    """

    SIZE: int = 20

    def __init__(self, parts: list[tuple[str, Optional[Callable]]]) -> None:
        """Build the row from the steps it is given."""
        super().__init__(
            spacing=6,
            expand=True,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
        #: Every step by index: a `Text` for a label, a `LinkButton` for a link.
        self._steps: dict[int, ft.Control] = {}
        self._paint(parts)

    def _paint(self, parts: list[tuple[str, Optional[Callable]]]) -> None:
        """Turn the pairs into links, labels and separators."""
        controls: list[ft.Control] = []
        for index, (text, handler) in enumerate(parts):
            last = index == len(parts) - 1
            if last or handler is None:
                label = ft.Text(
                    text,
                    size=self.SIZE,
                    color=ft.Colors.WHITE if last else SEPARATOR_COLOR,
                    weight=(
                        ft.FontWeight.BOLD if last else ft.FontWeight.NORMAL
                    ),
                    max_lines=1,
                    overflow=ft.TextOverflow.ELLIPSIS,
                    tooltip=text or None,
                )
                self._steps[index] = label
                controls.append(
                    ft.Container(
                        expand=last,
                        alignment=ft.Alignment.CENTER_LEFT,
                        content=label,
                    )
                )
            else:
                link = LinkButton(
                    text,
                    on_click=handler,
                    size=self.SIZE,
                    underline=False,
                    padding=ft.Padding.all(0),
                    color=LINK_COLOR,
                )
                link.content.max_lines = 1
                link.content.overflow = ft.TextOverflow.ELLIPSIS
                self._steps[index] = link
                controls.append(
                    ft.Container(
                        expand=last,
                        alignment=ft.Alignment.CENTER_LEFT,
                        content=link,
                    )
                )
            if not last:
                controls.append(
                    ft.Text("›", size=self.SIZE, color=SEPARATOR_COLOR)
                )
        self.controls = controls

    def text(self, index: int) -> str:
        """What one step says right now.

        Args:
            index: which step, from zero.

        Returns:
            The step's text, or an empty string when there is no such step.
        """
        step = self._steps.get(index)
        if isinstance(step, ft.Text):
            return step.value or ""
        if isinstance(step, LinkButton):
            return step.content.value or ""
        return ""

    def set_text(self, index: int, text: str) -> None:
        """Write one step, for a name that only arrives when the API answers.

        A step can be a link — the collection's own crumb opens its list — so the
        text is written where that kind of control keeps it.

        Args:
            index: which step, from zero.
            text: what to show; an empty text hides the tooltip.
        """
        step = self._steps.get(index)
        if isinstance(step, ft.Text):
            step.value = text
            step.tooltip = text or None
        elif isinstance(step, LinkButton):
            step.content.value = text
            step.tooltip = text or None
