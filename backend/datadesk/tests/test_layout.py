"""S2 acceptance: the shared page shell and the assets it pulls in."""
import re

import pytest
from django.conf import settings
from django.test import Client, RequestFactory, override_settings
from django.template.loader import render_to_string

from datadesk.tests.helpers import UNHASHED_STATIC_STORAGES

VENDOR_ASSETS = (
    "datadesk/vendor/htmx.min.js",
    "datadesk/vendor/alpine.min.js",
    "datadesk/vendor/tabulator.min.js",
    "datadesk/vendor/tabulator.min.css",
)


@pytest.fixture
def base_html(reload_urlconf) -> str:
    """Renders ``base.html`` with the app mounted and a real request."""
    with override_settings(
        DATADESK_ENABLED=True, STORAGES=UNHASHED_STATIC_STORAGES
    ):
        reload_urlconf()
        request = RequestFactory().get("/datadesk/")
        return render_to_string("datadesk/base.html", request=request)


class TestBaseLayout:
    """The layout every DataDesk screen is built on."""

    def test_renders_the_topbar_with_the_brand(self, base_html: str) -> None:
        assert 'class="dd-topbar"' in base_html
        assert "dd-brand" in base_html

    def test_links_the_vendored_assets(self, base_html: str) -> None:
        for asset in VENDOR_ASSETS:
            assert asset in base_html

    def test_links_the_datadesk_stylesheet(self, base_html: str) -> None:
        assert "datadesk/datadesk.css" in base_html

    def test_body_carries_the_csrf_header_for_htmx(self, base_html: str) -> None:
        match = re.search(r'"X-CSRFToken": "([^"]*)"', base_html)

        assert match is not None
        assert len(match.group(1)) == 64


class TestDashboardOnTheBaseLayout:
    """``dashboard.html`` extends the shell instead of duplicating it."""

    @pytest.mark.django_db
    def test_dashboard_renders_inside_the_shell(
        self, reload_urlconf, django_user_model
    ) -> None:
        django_user_model.objects.create_user(
            username="curator", password="s3cret-pass", is_staff=True
        )
        with override_settings(
            DATADESK_ENABLED=True, STORAGES=UNHASHED_STATIC_STORAGES
        ):
            reload_urlconf()
            client = Client()
            client.login(username="curator", password="s3cret-pass")
            response = client.get("/datadesk/")

        content = response.content.decode()
        assert response.status_code == 200
        assert 'class="dd-topbar"' in content
        assert "dd-main" in content
        assert "<b>Dashboard</b>" in content


class TestTheRefusedCellMark:
    """The ring is painted inside the cell, so the next row covered its bottom.

    A paint-order bug cannot be proven by a test — it is verified by eye on a
    series with more than one stamp. What this pins is the reason the rule
    carries a stacking hint, so a tidy-up pass does not delete the line that
    makes the mark visible.
    """

    def stylesheet(self) -> str:
        path = settings.BASE_DIR / "datadesk" / "static" / "datadesk"
        return (path / "datadesk.css").read_text(encoding="utf-8")

    def test_the_refused_cell_is_lifted_above_the_next_row(self) -> None:
        rule = self.stylesheet().split(".dd-cell-invalid {", 1)[1].split("}", 1)[0]

        assert "position: relative" in rule
        assert "z-index" in rule

    def test_the_ring_inside_a_refused_row_is_lifted_too(self) -> None:
        rule = self.stylesheet().split(".dd-row-error .dd-cell-invalid {", 1)[1]
        rule = rule.split("}", 1)[0]

        assert "z-index" in rule

class TestButtons:
    """A button that happens to be an <a> is still a button.

    Without the reset the browser underlines it and the label sits on the text
    baseline instead of the middle of the box, so the same-looking control was
    underlined and short on the dashboard and clean inside the workspace. The
    local patches S17 added hid the cause instead of fixing the class.
    """

    def stylesheet(self) -> str:
        path = settings.BASE_DIR / "datadesk" / "static" / "datadesk"
        return (path / "datadesk.css").read_text(encoding="utf-8")

    def rule(self, selector: str) -> str:
        return self.stylesheet().split(selector + " {", 1)[1].split("}", 1)[0]

    def test_the_button_class_removes_the_underline(self) -> None:
        assert "text-decoration: none" in self.rule(".dd-btn")

    def test_the_label_is_centred_in_the_box(self) -> None:
        rule = self.rule(".dd-btn")

        assert "display: inline-flex" in rule
        assert "align-items: center" in rule
        assert "justify-content: center" in rule

    def test_the_height_comes_from_the_class_not_from_a_variant(self) -> None:
        """Every button is the same height, including side by side.

        The height is fixed on the base class and does not depend on the
        variant's padding or on how long the label is: a ghost button next to a
        dark one cannot end up shorter.
        """
        assert "height: var(--dd-btn-height)" in self.rule(".dd-btn")
        assert "height" not in self.rule(".dd-btn-ghost")


class TestTheTypeScale:
    """One scale, in tokens, and nothing below 11 px.

    "The GUI feels dated" was, measured, a stylesheet where `--dd-base-size` was
    declared and then bypassed by fifty hardcoded sizes. These tests keep the
    scale from drifting back: a new screen can pick a token, not a number.
    """

    def stylesheet(self) -> str:
        path = settings.BASE_DIR / "datadesk" / "static" / "datadesk"
        return (path / "datadesk.css").read_text(encoding="utf-8")

    def tokens(self) -> dict[str, int]:
        pairs = re.findall(
            r"(--dd-text[a-z-]*|--dd-label):\s*(\d+)px;", self.stylesheet()
        )
        return {name: int(size) for name, size in pairs}

    def test_no_rule_writes_its_own_pixel_size(self) -> None:
        assert re.search(r"font-size:\s*\d", self.stylesheet()) is None

    def test_every_size_comes_from_a_token(self) -> None:
        used = set(re.findall(r"font-size:\s*var\((--dd-[a-z-]+)\)", self.stylesheet()))

        assert used
        assert used <= set(self.tokens())

    def test_nothing_is_below_eleven_pixels(self) -> None:
        assert min(self.tokens().values()) >= 11

    def test_the_body_uses_the_scale(self) -> None:
        assert "font: var(--dd-text) /" in self.stylesheet()


class TestTheWorkbenchFitsTheWindow:
    """S30's filter bar pushed the pagination below the fold.

    The grid used to carry `calc(100vh - 300px)`, a number tuned to a two-row
    filter bar. Adding five selects made the bar four rows and the footer ended
    up at 899px in a 900px window. The card is now a column as tall as the
    window and the grid takes what is left, so the number does not exist.
    """

    def stylesheet(self) -> str:
        path = settings.BASE_DIR / "datadesk" / "static" / "datadesk"
        return (path / "datadesk.css").read_text(encoding="utf-8")

    def rule(self, selector: str) -> str:
        return self.stylesheet().split(selector + " {", 1)[1].split("}", 1)[0]

    def test_the_page_is_a_column_as_tall_as_the_window(self) -> None:
        rule = self.rule(".dd-workbench-page")

        assert "display: flex" in rule
        assert "flex-direction: column" in rule
        assert "height: calc(100vh" in rule

    def test_the_grid_takes_what_the_filters_leave(self) -> None:
        rule = self.rule(".dd-workbench-page > #workbench")

        assert "flex: 1 1 auto" in rule
        assert "min-height" in rule

    def test_the_script_does_not_guess_the_height(self) -> None:
        path = settings.BASE_DIR / "datadesk" / "static" / "datadesk"
        script = (path / "workbench.js").read_text(encoding="utf-8")

        assert 'height: "100%"' in script
        assert 'height: "calc(100vh - 300px)"' not in script

    def test_a_hidden_element_is_hidden(self) -> None:
        """`.dd-active-filters { display: flex }` used to beat the attribute and
        leave an empty 17px strip even with no filters on."""
        stylesheet = self.stylesheet()

        assert re.search(r"\[hidden\]\s*\{[^}]*display:\s*none", stylesheet)


class TestTheS28Look:
    """The shelved polish: typeface, controls, motion, elevation, rhythm.

    Each of these is one decision that a later tidy-up could quietly undo —
    a system font back, the navy header back, a solid outline back — so each
    gets a line here.
    """

    def stylesheet(self) -> str:
        path = settings.BASE_DIR / "datadesk" / "static" / "datadesk"
        return (path / "datadesk.css").read_text(encoding="utf-8")

    def rule(self, selector: str) -> str:
        return self.stylesheet().split(selector + " {", 1)[1].split("}", 1)[0]

    def test_the_font_is_self_hosted_and_first_in_the_stack(self) -> None:
        assert '@font-face' in self.stylesheet()
        assert 'url("vendor/inter-latin-var.woff2")' in self.stylesheet()
        assert '"Inter", system-ui' in self.rule(":root")

    def test_the_grid_header_is_light_and_the_navy_stays_on_the_topbar(self) -> None:
        header = self.stylesheet().split(
            "#workbench .tabulator-header .tabulator-col,", 1
        )[1].split("}", 1)[0]

        assert "background: #f8f9fb" in header
        assert "var(--dd-navy)" not in header

    def test_focus_on_a_control_is_a_soft_ring(self) -> None:
        rule = self.rule(".dd-filter input,\n.dd-filter select")

        assert "height: var(--dd-input-height)" in rule
        focus = self.stylesheet().split(".dd-filter input:focus,", 1)[1].split("}", 1)[0]
        assert "outline: none" in focus
        assert "box-shadow: var(--dd-ring)" in focus

    def test_the_row_grew_to_thirty_eight(self) -> None:
        assert "--dd-row-height: 38px" in self.stylesheet()

    def test_an_empty_cell_says_so(self) -> None:
        assert ".tabulator-cell:empty::after" in self.stylesheet()

    def test_motion_can_be_turned_off(self) -> None:
        stylesheet = self.stylesheet()

        assert "--dd-ease: 120ms ease" in stylesheet
        assert "prefers-reduced-motion: reduce" in stylesheet
