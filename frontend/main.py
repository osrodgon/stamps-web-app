"""
Main entry point for the Stamps web application (Flet frontend).

This module initializes the Flet application, sets up routing, and
configures the initial page state including language preferences.

The application uses client_storage for persisting user session data
and supports dynamic language switching via the translation module.
"""

import flet as ft
from core.base_ui import BaseUI
from core.utils import _read_client_timezone, validate_jwt_token
from pages.auth.signup_page import SignupPage
from pages.auth.login_page import LoginPage
from pages.not_found_page import NotFoundPage
from pages.collection.collections_page import CollectionsPage
from pages.admin.stamps_manager_page import StampsManagerPage
from core.urls import URLs
from core.log_setup import log_setup
from core.translations import init_language, get_language


from settings import    APP_NAME, ASSETS_DIR, FONT_REGULAR, FONT_BOLD, FONT_BLACK, FRONTEND_PORT, \
                        USER_JWT_TOKEN, USER_IS_ADMIN, FAV_ICON

from components.colors import SKY_BLUE
from components.constants import BUTTON_BORDER_RADIUS


def _locale_config(lang: str) -> ft.LocaleConfiguration:
    """Build a ``LocaleConfiguration`` for the given language code.

    Args:
        lang: Two-letter language code (``"en"`` or ``"es"``).

    Returns:
        A ``LocaleConfiguration`` with the current locale set and both
        English and Spanish listed as supported locales.
    """
    mapping: dict[str, ft.Locale] = {
        "en": ft.Locale("en", "US"),
        "es": ft.Locale("es", "ES"),
    }
    return ft.LocaleConfiguration(
        current_locale=mapping.get(lang, mapping["en"]),
        supported_locales=list(mapping.values()),
    )

# Route handlers for implemented pages
ROUTE_HANDLERS = {
    URLs.Frontend.login: LoginPage,
    URLs.Frontend.signup: SignupPage,
    URLs.Frontend.collections: CollectionsPage,
    URLs.Frontend.stamps_manager: StampsManagerPage,
    # TODO: Implement these pages
    # URLs.Frontend.logout: LogoutPage,
}


def configure_page(page: ft.Page):
    """Configure page properties including title, fonts, theme, and icon.

    Sets up the fundamental page configuration:
    - Page title from APP_NAME setting
    - Custom fonts (Roboto variants)
    - Theme with Linux page transition disabled
    - Window favicon icon

    Args:
        page (ft.Page): The Flet page instance to configure.
    """
    page.title = APP_NAME
    page.expand = True
    page.fonts = {
        "Roboto": FONT_REGULAR,
        "Roboto-Bold": FONT_BOLD,
        "Roboto-Black": FONT_BLACK
    }
    
    # Remove the "Zoom" animation for Linux
    page.theme = ft.Theme(
        page_transitions=ft.PageTransitionsTheme(
            linux=ft.PageTransitionTheme.NONE
        ),
        font_family="Roboto",
        date_picker_theme=ft.DatePickerTheme(
            confirm_button_style=ft.ButtonStyle(
                bgcolor=SKY_BLUE,
                color=ft.Colors.WHITE,
                overlay_color=ft.Colors.with_opacity(0.2, SKY_BLUE),
                shape=ft.RoundedRectangleBorder(radius=BUTTON_BORDER_RADIUS),
            ),
            cancel_button_style=ft.ButtonStyle(
                color=SKY_BLUE,
                overlay_color=ft.Colors.with_opacity(0.1, SKY_BLUE),
                shape=ft.RoundedRectangleBorder(radius=BUTTON_BORDER_RADIUS),
            ),
            day_overlay_color=ft.Colors.with_opacity(0.15, SKY_BLUE),
            year_overlay_color=ft.Colors.with_opacity(0.15, SKY_BLUE),
            today_bgcolor=SKY_BLUE,
            today_foreground_color=ft.Colors.WHITE,
            day_shape=ft.RoundedRectangleBorder(radius=BUTTON_BORDER_RADIUS),
            shape=ft.RoundedRectangleBorder(radius=BUTTON_BORDER_RADIUS),
        ),
    )

    page.window.icon = FAV_ICON

    page.locale_configuration = _locale_config(get_language())


async def route_change(e: ft.RouteChangeEvent):
    """Handle route changes and render the appropriate view."""
    page = e.page
    route = page.route
    prefs = ft.SharedPreferences()
        
    if route == URLs.Frontend.root:
        auth_token = await prefs.get(USER_JWT_TOKEN)
        if auth_token:
            user_is_admin = await prefs.get(USER_IS_ADMIN)
            if user_is_admin:
                await page.push_route(URLs.Frontend.stamps_manager)
            else:
                await page.push_route(URLs.Frontend.collections)
        else:
            await page.push_route(URLs.Frontend.login)
        return

    page.views.clear()
    handler = ROUTE_HANDLERS.get(route)

    if handler:
        page.views.append(handler(page))
    else:
        if route == URLs.Frontend.logout:
            logout = BaseUI()
            
            await logout._delete_user()
            await page.push_route(URLs.Frontend.login)
        else:
            page.views.append(NotFoundPage(page))

    page.update()


async def view_pop(e: ft.ViewPopEvent):
    """Handle browser back button navigation."""
    page = e.page
    if e.view is not None:
        page.views.remove(e.view)
        if page.views:
            top_view = page.views[-1]
            await page.push_route(top_view.route)


async def main(page: ft.Page):
    """Main async entry point for the Flet application."""
    configure_page(page)

    await _read_client_timezone()

    try:
        await init_language()
    except Exception as e:
        page.add(ft.Text(f"Failed to initialize language: {e}"))
        page.update()

    # Sync locale after language init — init_language() may have loaded
    # a persisted language preference different from the default.
    page.locale_configuration = _locale_config(get_language())

    page.on_route_change = route_change
    page.on_view_pop = view_pop
    
    # Handle initial route directly
    route = URLs.Frontend.root
    prefs = ft.SharedPreferences()

    if route == URLs.Frontend.root:
        auth_token = await prefs.get(USER_JWT_TOKEN)
        if validate_jwt_token(auth_token):
            user_is_admin = await prefs.get(USER_IS_ADMIN)
            if user_is_admin:
                route = URLs.Frontend.stamps_manager
            else:
                route = URLs.Frontend.collections
        else:
            route = URLs.Frontend.login

    page.route = route
    handler = ROUTE_HANDLERS.get(route)
    if handler:
        page.views.append(handler(page))
    else:
        page.views.append(NotFoundPage(page))
    page.update()


if __name__ == "__main__":
    """Script entry point - sets up logging and launches the app."""
    log_setup()
    ft.run(main, assets_dir=ASSETS_DIR, view=ft.AppView.WEB_BROWSER, port=FRONTEND_PORT)