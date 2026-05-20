"""Unit tests for components/form/year_range_selector.py — Canvas-drawn two-thumb slider."""

from unittest.mock import MagicMock, patch

import pytest

from components.form.year_range_selector import YearRangeSelector


class TestCoordinateConversion:
    """Tests for _year_to_x and _x_to_year pure math methods."""

    @pytest.fixture
    def selector(self) -> YearRangeSelector:
        return YearRangeSelector(
            min_year=1850,
            max_year=1950,
            width=300,
            track_height=3,
            thumb_radius=6,
            step=5,
            left_padding=20,
            right_padding=20,
        )

    def test_year_to_x_start(self, selector: YearRangeSelector) -> None:
        x = selector._year_to_x(1850.0)

        assert x == pytest.approx(float(selector._aura_margin))

    def test_year_to_x_end(self, selector: YearRangeSelector) -> None:
        x = selector._year_to_x(1950.0)

        expected = selector._inner_width - selector._aura_margin
        assert x == pytest.approx(float(expected))

    def test_year_to_x_midpoint(self, selector: YearRangeSelector) -> None:
        x = selector._year_to_x(1900.0)

        expected = selector._aura_margin + selector._track_width() / 2
        assert x == pytest.approx(expected)

    def test_x_to_year_clamps_below_min(self, selector: YearRangeSelector) -> None:
        year = selector._x_to_year(0.0)

        assert year == 1850

    def test_x_to_year_clamps_above_max(self, selector: YearRangeSelector) -> None:
        year = selector._x_to_year(9999.0)

        assert year == 1950

    def test_x_to_year_snaps_to_step(self, selector: YearRangeSelector) -> None:
        year = selector._x_to_year(selector._year_to_x(1873.0))

        assert year % 5 == 0

    def test_x_to_year_round_trip(self, selector: YearRangeSelector) -> None:
        original = 1900
        x = selector._year_to_x(float(original))
        result = selector._x_to_year(x)

        assert result == original


class TestSetRange:
    """Tests for the set_range public method."""

    @pytest.fixture
    def selector(self) -> YearRangeSelector:
        return YearRangeSelector(
            min_year=1850,
            max_year=1900,
            width=300,
        )

    def test_set_range_updates_min_max(self, selector: YearRangeSelector) -> None:
        with patch.object(selector._label, "update"), \
             patch.object(selector._canvas, "update"):
            selector.set_range(1800, 2000, 1820, 1980)

        assert selector._min_year == 1800
        assert selector._max_year == 2000

    def test_set_range_updates_thumb_positions(self, selector: YearRangeSelector) -> None:
        with patch.object(selector._label, "update"), \
             patch.object(selector._canvas, "update"):
            selector.set_range(1800, 2000, 1820, 1980)

        assert selector._start == 1820.0
        assert selector._end == 1980.0

    def test_set_range_updates_label_text(self, selector: YearRangeSelector) -> None:
        with patch.object(selector._label, "update"), \
             patch.object(selector._canvas, "update"):
            selector.set_range(1800, 2000, 1850, 1950)

        assert selector._label.spans[1].text == "1850 - 1950"


class TestSelectorProperties:
    """Tests for sel_min_year and sel_max_year properties."""

    def test_sel_min_year_returns_min(self) -> None:
        selector = YearRangeSelector(min_year=1840, max_year=2000)

        assert selector.sel_min_year == 1840

    def test_sel_max_year_returns_max(self) -> None:
        selector = YearRangeSelector(min_year=1840, max_year=2000)

        assert selector.sel_max_year == 2000

    def test_properties_reflect_set_range(self) -> None:
        selector = YearRangeSelector(min_year=1850, max_year=1900)

        with patch.object(selector._label, "update"), \
             patch.object(selector._canvas, "update"):
            selector.set_range(1800, 2000, 1800, 2000)

        assert selector.sel_min_year == 1800
        assert selector.sel_max_year == 2000


class TestTrackWidth:
    """Tests for _track_width calculation."""

    def test_track_width_excludes_auras(self) -> None:
        selector = YearRangeSelector(
            min_year=1850,
            max_year=1950,
            width=300,
            thumb_radius=6,
            left_padding=20,
            right_padding=20,
        )

        expected = selector._inner_width - 2 * selector._aura_margin
        assert selector._track_width() == expected
