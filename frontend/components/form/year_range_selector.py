"""
Two-thumb year range selector using Canvas for custom track thickness.

Draws the track bar and thumbs via ft.canvas primitives for full
control over track height, colors, and thumb appearance.
"""

import asyncio
import flet as ft
import flet.canvas as cv
from typing import Callable, Optional

from components.colors import SLIDER_INACTIVE, AURA_RADIUS_MULTIPLIER, AURA_OPACITY, DRAG_THUMB_SCALE
from core.translations import _
from components.constants import FONT_SIZE_DEFAULT, SLIDER_CANVAS_HEIGHT, SLIDER_TRACK_HEIGHT, SLIDER_THUMB_RADIUS, SLIDER_DEFAULT_MIN_YEAR


class YearRangeSelector(ft.Container):
    """A year range selector with a Canvas-drawn slider.

    Track appearance (height, thumb radius) is configurable via
    constructor params. Drag interaction via GestureDetector.
    """

    _canvas_height: int = SLIDER_CANVAS_HEIGHT

    def __init__(
        self,
        min_year: int = SLIDER_DEFAULT_MIN_YEAR,
        max_year: int = 1975,
        start_value: int = None,
        end_value: int = None,
        width: int = 300,
        track_height: int = SLIDER_TRACK_HEIGHT,
        thumb_radius: int = SLIDER_THUMB_RADIUS,
        step: int = 1,
        top_padding: int = 10,
        left_padding: int = 20,
        right_padding: int = 20,
        bottom_padding: int = 0,
        on_change: Optional[Callable[[int, int], None]] = None,
    ) -> None:
        """Initialize the year range selector.

        Args:
            min_year: Earliest selectable year.
            max_year: Latest selectable year.
            start_value: Initial value of the left thumb.
            end_value: Initial value of the right thumb.
            width: Total width of the component in pixels.
            track_height: Height of the track bar in pixels (default 3).
            thumb_radius: Radius of the thumb circles in pixels (default 6).
            step: Snap interval for thumb movement (default 1). step=10 jumps in decades.
            top_padding: Internal padding above the label in pixels (default 10).
            left_padding: Internal padding on the left in pixels (default 20).
            right_padding: Internal padding on the right in pixels (default 20).
            bottom_padding: Internal padding below the slider in pixels (default 0).
            on_change: Called with (start_year, end_year) when thumbs move via drag or tap.
            Note: start_value/end_value default to min_year/max_year when set to None.
        """
        super().__init__()
        
        if start_value is None:
            start_value = min_year
        if end_value is None:
            end_value = max_year

        self._min_year: int = min_year
        self._max_year: int = max_year
        self._start: float = float(start_value)
        self._end: float = float(end_value)
        self._inner_width: int = width - left_padding - right_padding
        self._track_height: int = track_height
        self._thumb_radius: int = thumb_radius
        self._step: int = step
        self._aura_margin: int = thumb_radius * 3
        self._top_padding: int = top_padding
        self._left_padding: int = left_padding
        self._right_padding: int = right_padding
        self._bottom_padding: int = bottom_padding
        self._on_change: Optional[Callable[[int, int], None]] = on_change
        self._dragging: Optional[str] = None
        self._hovered: bool = False

        self._label: ft.Text = ft.Text(
            spans=[
                ft.TextSpan(
                    f"{_("filter.years_available")}: ",
                    ft.TextStyle(
                        color=ft.Colors.GREY_500, 
                        size=FONT_SIZE_DEFAULT, 
                        font_family="Roboto"
                    ),
                ),
                ft.TextSpan(
                    f"{start_value} - {end_value}",
                    ft.TextStyle(
                        color=ft.Colors.GREY_500, 
                        size=FONT_SIZE_DEFAULT,
                        font_family="Roboto"
                    ),
                ),
            ],
        )

        self._canvas: cv.Canvas = cv.Canvas(
            width=self._inner_width,
            height=self._canvas_height,
        )
        self._draw()

        self.content = ft.Column(
            controls=[
                ft.Container(content=self._label, alignment=ft.Alignment.CENTER),
                ft.Container(
                    content=ft.GestureDetector(
                        content=ft.Container(
                            content=self._canvas,
                            height=self._canvas_height,
                            width=self._inner_width,
                        ),
                        width=self._inner_width,
                        height=self._canvas_height,
                        mouse_cursor=ft.MouseCursor.CLICK,
                        on_tap=self._on_tap,
                        on_horizontal_drag_start=self._on_drag_start,
                        on_horizontal_drag_update=self._on_drag_update,
                        on_horizontal_drag_end=self._on_drag_end,
                    ),
                    width=self._inner_width,
                    height=self._canvas_height,
                    on_hover=self._on_hover,
                ),
            ],
            spacing=0,
        )
        self.width = width
        self.padding = ft.Padding(
            left=self._left_padding,
            right=self._right_padding,
            top=self._top_padding,
            bottom=self._bottom_padding,
        )

    # -- Coordinate conversion --

    def _track_width(self) -> int:
        """Usable track width minus aura margins on each side."""
        return self._inner_width - 2 * self._aura_margin

    def _year_to_x(self, year: float) -> float:
        """Convert a year value to a pixel x-coordinate."""
        fraction: float = (year - self._min_year) / (self._max_year - self._min_year)
        return float(self._aura_margin) + fraction * self._track_width()

    def _x_to_year(self, x: float) -> int:
        """Convert a pixel x-coordinate to the nearest year, snapped to step."""
        clamped: float = max(
            float(self._aura_margin),
            min(float(self._inner_width - self._aura_margin), x),
        )
        fraction: float = (clamped - self._aura_margin) / self._track_width()
        raw: int = round(self._min_year + fraction * (self._max_year - self._min_year))
        return round(raw / self._step) * self._step

    def _notify_change(self) -> None:
        """Fire the on_change callback with current start and end values.

        Supports both sync callbacks and async coroutines.
        """
        if self._on_change:
            result = self._on_change(int(self._start), int(self._end))
            if asyncio.iscoroutine(result):
                asyncio.create_task(result)

    def set_range(self, min_year: int, max_year: int, start: int, end: int) -> None:
        """Update the year range and selected thumb positions in-place.

        Called after construction when the available year range is
        fetched from the API. Updates internal state, label, and
        canvas without recreating the widget.

        Args:
            min_year: New minimum selectable year.
            max_year: New maximum selectable year.
            start: New left thumb position.
            end: New right thumb position.
        """
        self._min_year = min_year
        self._max_year = max_year
        self._start = float(start)
        self._end = float(end)
        self._label.spans[1].text = f"{start} - {end}"
        self._label.update()
        self._draw()
        self._canvas.update()
    
    @property
    def sel_min_year(self) -> int:
        """Return the current minimum year of the slider range.

        This value is set at construction via min_year and may be
        updated later via set_range(). Used by external code to
        determine the full range bounds.
        """
        return self._min_year

    @property
    def sel_max_year(self) -> int:
        """Return the current maximum year of the slider range.

        This value is set at construction via max_year and may be
        updated later via set_range(). Used by external code to
        determine the full range bounds.
        """
        return self._max_year

    # -- Drawing --

    def _draw(self) -> None:
        """Rebuild the canvas shapes from current thumb positions."""
        track_top: int = (self._canvas_height - self._track_height) // 2
        track_center: float = track_top + self._track_height / 2
        x1: float = self._year_to_x(self._start)
        x2: float = self._year_to_x(self._end)
        active_start: bool = self._dragging == "start"
        active_end: bool = self._dragging == "end"
        aura_radius: float = self._thumb_radius * AURA_RADIUS_MULTIPLIER
        aura_paint: ft.Paint = ft.Paint(
            color=ft.Colors.with_opacity(AURA_OPACITY, ft.Colors.WHITE),
        )

        shapes: list = []

        # Background track
        shapes.append(cv.Rect(
            self._aura_margin,
            track_top,
            self._track_width(),
            self._track_height,
            paint=ft.Paint(color=SLIDER_INACTIVE),
        ))

        # Active segment
        shapes.append(cv.Rect(
            x1,
            track_top,
            x2 - x1,
            self._track_height,
            paint=ft.Paint(color=ft.Colors.GREY_500),
        ))

        # Aura circles (hover or drag feedback)
        if self._hovered or self._dragging:
            if active_start or (self._hovered and not self._dragging):
                shapes.append(cv.Circle(x1, track_center, aura_radius, paint=aura_paint))
            if active_end or (self._hovered and not self._dragging):
                shapes.append(cv.Circle(x2, track_center, aura_radius, paint=aura_paint))

        # Left thumb
        shapes.append(cv.Circle(
            x1, track_center,
            self._thumb_radius * DRAG_THUMB_SCALE if active_start else self._thumb_radius,
            paint=ft.Paint(color=ft.Colors.GREY_500),
        ))

        # Right thumb
        shapes.append(cv.Circle(
            x2, track_center,
            self._thumb_radius * DRAG_THUMB_SCALE if active_end else self._thumb_radius,
            paint=ft.Paint(color=ft.Colors.GREY_500),
        ))

        self._canvas.shapes = shapes

    # -- Tap handling --

    def _on_tap(self, e: ft.TapEvent) -> None:
        """Click on the track moves the nearest thumb to that position."""
        x: float = e.local_position.x
        x1: float = self._year_to_x(self._start)
        x2: float = self._year_to_x(self._end)
        year: int = self._x_to_year(x)
        if abs(x - x1) <= abs(x - x2):
            self._start = min(float(year), self._end - self._step)
        else:
            self._end = max(float(year), self._start + self._step)
        self._label.spans[1].text = f"{int(self._start)} - {int(self._end)}"
        self._label.update()
        self._draw()
        self._canvas.update()
        self._notify_change()

    # -- Drag handling --

    def _on_drag_start(self, e: ft.DragStartEvent) -> None:
        """Determine which thumb the user clicked near."""
        x: float = e.local_position.x
        x1: float = self._year_to_x(self._start)
        x2: float = self._year_to_x(self._end)
        d1: float = abs(x - x1)
        d2: float = abs(x - x2)
        threshold: float = self._thumb_radius * 2
        if d2 <= d1 and d2 < threshold:
            self._dragging = "end"
        elif d1 < threshold:
            self._dragging = "start"
        else:
            self._dragging = None

    def _on_drag_update(self, e: ft.DragUpdateEvent) -> None:
        """Move the dragged thumb and redraw."""
        if not self._dragging:
            return
        year: int = self._x_to_year(e.local_position.x)
        if self._dragging == "start":
            self._start = min(float(year), self._end - self._step)
        else:
            self._end = max(float(year), self._start + self._step)

        self._label.spans[1].text = f"{int(self._start)} - {int(self._end)}"
        self._label.update()
        self._draw()
        self._canvas.update()
        self._notify_change()

    def _on_drag_end(self, e: ft.DragEndEvent) -> None:
        """Stop dragging and redraw thumbs in idle state."""
        self._dragging = None
        self._draw()
        self._canvas.update()
        self._notify_change()

    # -- Hover handling --

    def _on_hover(self, e: ft.HoverEvent) -> None:
        """Show/hide aura circles when mouse enters/leaves the slider."""
        self._hovered = bool(e.data)
        self._draw()
        self._canvas.update()
