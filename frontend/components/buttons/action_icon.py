"""An icon action that greys out and takes its colour on hover.

The admin's series header and the collection's cards use the same action: a bare icon,
grey by default, coloured on hover, with a tooltip instead of a label. The styling lived as
a private helper of the admin's header; it is one component now so the two screens cannot
drift (edit first, then delete, as the admin draws them).
"""

from __future__ import annotations

from typing import Callable, Optional

import flet as ft

from components.colors import GREY_700
from components.constants import ISSUE_ACTION_ICON_SIZE


class ActionIcon(ft.IconButton):
    """A grey icon that turns `hover_color` and says what it does in a tooltip.

    Args:
        icon: the icon to paint.
        tooltip: the text shown on hover.
        hover_color: the colour the icon takes on hover.
        on_click: what it does.
        size: the icon's box, in pixels.
        visible: whether it is shown at all.
    """

    def __init__(
        self,
        icon: str,
        tooltip: str,
        hover_color: str,
        on_click: Optional[Callable] = None,
        size: int = ISSUE_ACTION_ICON_SIZE,
        visible: bool = True,
    ) -> None:
        super().__init__(
            icon=icon,
            icon_size=size,
            splash_radius=1,
            splash_color=ft.Colors.TRANSPARENT,
            width=size,
            height=size,
            padding=0,
            hover_color=ft.Colors.TRANSPARENT,
            visible=visible,
            style=ft.ButtonStyle(
                color={
                    ft.ControlState.DEFAULT: GREY_700,
                    ft.ControlState.HOVERED: hover_color,
                },
                overlay_color=ft.Colors.TRANSPARENT,
            ),
            tooltip=tooltip,
            on_click=on_click,
        )
