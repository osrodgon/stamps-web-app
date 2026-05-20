"""Unit tests for components/colors.py — color constants and lighten_color utility."""

import re

import pytest

from components.colors import (
    BG_ALT,
    BG_GRADIENT_END,
    BG_GRADIENT_START,
    BG_LIGHT,
    BLUE_700,
    BLUE_GREY_100,
    DARK_BLUE_GREY,
    DARK_IMG_BG,
    DELETE_RED,
    EXPANSION_BG,
    GREY_700,
    HEADER_BG,
    ICON_GREY,
    NAVY_DARK,
    PRIMARY_ACCENT,
    RED,
    RED_DISABLED,
    RED_HOVER,
    ROW_BORDER,
    ROW_HOVER,
    SILVER_LIGHT,
    SKY_BLUE,
    SKY_BLUE_DISABLED,
    SKY_BLUE_HOVER,
    SLATE_DARK,
    SLATE_GREY,
    SLATE_GREY_HOVER,
    SLIDER_INACTIVE,
    TEXT_BLUE,
    lighten_color,
)

HEX_PATTERN = re.compile(r"^#[0-9a-fA-F]{6}$")


class TestLightenColor:
    """Tests for the lighten_color utility function."""

    def test_lighten_black(self) -> None:
        result = lighten_color("#000000", 0.5)
        assert result == "#7f7f7f"

    def test_lighten_white_unchanged(self) -> None:
        result = lighten_color("#ffffff", 0.5)
        assert result == "#ffffff"

    def test_lighten_red(self) -> None:
        result = lighten_color("#ff0000", 0.5)
        assert result == "#ff7f7f"

    def test_lighten_green(self) -> None:
        result = lighten_color("#00ff00", 0.5)
        assert result == "#7fff7f"

    def test_lighten_blue(self) -> None:
        result = lighten_color("#0000ff", 0.5)
        assert result == "#7f7fff"

    def test_lighten_default_amount(self) -> None:
        result = lighten_color("#000000", 0.2)
        assert result == "#333333"

    def test_lighten_full_amount(self) -> None:
        result = lighten_color("#5898d4", 1.0)
        assert result == "#ffffff"

    def test_lighten_zero_amount(self) -> None:
        result = lighten_color("#5898d4", 0.0)
        assert result == "#5898d4"

    def test_lighten_without_hash_prefix(self) -> None:
        result = lighten_color("5898d4", 0.0)
        assert result == "#5898d4"

    def test_lighten_sky_blue_10_percent(self) -> None:
        result = lighten_color(SKY_BLUE, 0.1)
        assert result == SKY_BLUE_HOVER

    def test_lighten_sky_blue_30_percent(self) -> None:
        result = lighten_color(SKY_BLUE, 0.3)
        assert result == SKY_BLUE_DISABLED

    def test_lighten_slate_grey_20_percent(self) -> None:
        result = lighten_color(SLATE_GREY, 0.2)
        assert result == SLATE_GREY_HOVER

    def test_result_is_valid_hex(self) -> None:
        result = lighten_color("#2c4869", 0.2)
        assert HEX_PATTERN.match(result) is not None

    def test_result_lowercase(self) -> None:
        result = lighten_color("#2C4869", 0.2)
        assert result == result.lower()


class TestColorConstants:
    """Tests for color constant definitions."""

    def test_all_constants_are_strings(self) -> None:
        constants = [
            SKY_BLUE, SKY_BLUE_HOVER, SKY_BLUE_DISABLED,
            SLATE_GREY, SLATE_GREY_HOVER,
            RED, RED_HOVER, RED_DISABLED,
            GREY_700, BLUE_GREY_100, BLUE_700,
            NAVY_DARK, SLATE_DARK, SILVER_LIGHT,
            DARK_BLUE_GREY, PRIMARY_ACCENT, TEXT_BLUE,
            DELETE_RED, BG_LIGHT, BG_GRADIENT_START,
            BG_GRADIENT_END, BG_ALT, HEADER_BG,
            ROW_BORDER, ICON_GREY, EXPANSION_BG,
            ROW_HOVER, SLIDER_INACTIVE, DARK_IMG_BG,
        ]
        for color in constants:
            assert isinstance(color, str)

    def test_all_constants_are_valid_hex_or_flet_color(self) -> None:
        constants = [
            SKY_BLUE, SKY_BLUE_HOVER, SKY_BLUE_DISABLED,
            SLATE_GREY, SLATE_GREY_HOVER,
            RED, RED_HOVER, RED_DISABLED,
            NAVY_DARK, SLATE_DARK, SILVER_LIGHT,
            DARK_BLUE_GREY, PRIMARY_ACCENT, TEXT_BLUE,
            DELETE_RED, BG_LIGHT, BG_GRADIENT_START,
            BG_GRADIENT_END, BG_ALT, HEADER_BG,
            ROW_BORDER, ICON_GREY, EXPANSION_BG,
            ROW_HOVER, SLIDER_INACTIVE, DARK_IMG_BG,
        ]
        for color in constants:
            assert HEX_PATTERN.match(color) is not None, f"Invalid hex: {color}"

    def test_sky_blue_value(self) -> None:
        assert SKY_BLUE == "#5898d4"

    def test_sky_blue_hover_is_lighter(self) -> None:
        assert SKY_BLUE_HOVER != SKY_BLUE

    def test_sky_blue_disabled_is_lighter_than_hover(self) -> None:
        assert SKY_BLUE_DISABLED != SKY_BLUE_HOVER

    def test_red_value(self) -> None:
        assert RED.upper() == "#E53935"

    def test_red_hover_is_darker(self) -> None:
        assert RED_HOVER.upper() == "#C62828"

    def test_red_disabled_is_grey(self) -> None:
        assert RED_DISABLED.upper() == "#BDBDBD"

    def test_slate_grey_value(self) -> None:
        assert SLATE_GREY == "#707282"

    def test_navy_dark_value(self) -> None:
        assert NAVY_DARK == "#2c4869"

    def test_slate_dark_value(self) -> None:
        assert SLATE_DARK == "#364153"

    def test_silver_light_value(self) -> None:
        assert SILVER_LIGHT == "#99a1af"

    def test_dark_blue_grey_value(self) -> None:
        assert DARK_BLUE_GREY == "#1e2b3c"

    def test_primary_accent_value(self) -> None:
        assert PRIMARY_ACCENT == "#00bfa5"

    def test_text_blue_value(self) -> None:
        assert TEXT_BLUE == "#1976d2"

    def test_delete_red_value(self) -> None:
        assert DELETE_RED == "#ef5350"

    def test_bg_light_value(self) -> None:
        assert BG_LIGHT == "#f8fafc"

    def test_bg_alt_value(self) -> None:
        assert BG_ALT == "#f1f5f9"

    def test_header_bg_value(self) -> None:
        assert HEADER_BG.upper() == "#232F3E"

    def test_row_border_value(self) -> None:
        assert ROW_BORDER.upper() == "#D0D0D0"

    def test_icon_grey_value(self) -> None:
        assert ICON_GREY == "#666666"

    def test_expansion_bg_value(self) -> None:
        assert EXPANSION_BG.upper() == "#FAFAFA"

    def test_row_hover_value(self) -> None:
        assert ROW_HOVER.upper() == "#E8E8E8"

    def test_slider_inactive_value(self) -> None:
        assert SLIDER_INACTIVE == "#3d4c5d"

    def test_dark_img_bg_value(self) -> None:
        assert DARK_IMG_BG == "#1a1a1a"

    def test_bg_gradient_start_value(self) -> None:
        assert BG_GRADIENT_START == "#f0f4f8"

    def test_bg_gradient_end_value(self) -> None:
        assert BG_GRADIENT_END == "#e2e8f0"
