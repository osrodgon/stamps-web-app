"""
Two-thumb year range selector for filtering by year.

Provides a compact RangeSlider with a dynamic label showing the
selected year range. Designed for use in page headers or filter bars.
"""

import flet as ft

from components.colors import SLIDER_INACTIVE


class YearRangeSelector(ft.Container):
    """A year range selector with label and RangeSlider.

    Displays "Years: {start} - {end}" above a two-thumb slider that
    increments in single-year steps.

    Attributes:
        label: The Text control showing the current range.
        slider: The RangeSlider control.
    """

    def __init__(
        self,
        min_year: int = 1850,
        max_year: int = 1975,
        start_value: int = 1860,
        end_value: int = 1940,
        width: int = 300,
    ) -> None:
        """Initialize the year range selector.

        Args:
            min_year: Earliest selectable year.
            max_year: Latest selectable year.
            start_value: Initial value of the left thumb.
            end_value: Initial value of the right thumb.
            width: Total width of the component in pixels.
        """
        super().__init__()

        self._min_year: int = min_year
        self._max_year: int = max_year

        self._label: ft.Text = ft.Text(
            spans=[
                ft.TextSpan(
                    "Years: ",
                    ft.TextStyle(
                        color=ft.Colors.GREY_500,
                        size=14,
                    ),
                ),
                ft.TextSpan(
                    f"{start_value} - {end_value}",
                    ft.TextStyle(
                        color=ft.Colors.WHITE,
                        size=14,
                        weight=ft.FontWeight.BOLD,
                    ),
                ),
            ],
        )

        self._slider: ft.RangeSlider = ft.RangeSlider(
            min=float(min_year),
            max=float(max_year),
            start_value=float(start_value),
            end_value=float(end_value),
            divisions=max_year - min_year,
            active_color=ft.Colors.WHITE70,
            inactive_color=SLIDER_INACTIVE,
            on_change=self._on_slider_change,
        )

        self.content = ft.Column(
            controls=[
                ft.Container(
                    content=self._label,
                    alignment=ft.Alignment.CENTER,
                ),
                self._slider,
            ],
            spacing=0,
        )
        self.width = width
        self.padding = ft.Padding(left=20, right=20, top=0, bottom=0)

    def _on_slider_change(self, e: ft.ControlEvent) -> None:
        """Update the label text when the slider thumbs move."""
        start: int = int(e.control.start_value)
        end: int = int(e.control.end_value)
        self._label.spans[1].text = f"{start} - {end}"
        self._label.update()
