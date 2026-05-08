"""
Main entry point for the Stamps web application (Flet frontend).

This module initializes the Flet application, sets up routing, and
configures the initial page state including language preferences.

The application uses client_storage for persisting user session data
and supports dynamic language switching via the translation module.
"""

import flet as ft
from base.base_ui import BaseUI
from pages.auth.login_page import LoginPage
from pages.not_found_page import NotFoundPage
from core.urls import URLs
from core.log_setup import log_setup
from core.translations import init_language
from settings import    APP_NAME, ASSETS_DIR, FONT_REGULAR, FONT_BOLD, FONT_BLACK, FRONTEND_PORT, \
                        USER_JWT_TOKEN, USER_IS_ADMIN, FAV_ICON

# Route handlers for implemented pages
ROUTE_HANDLERS = {
    URLs.Frontend.login: LoginPage,
    # TODO: Implement these pages
    # URLs.Frontend.signup: SignupPage,
    # URLs.Frontend.logout: LogoutPage,
    # URLs.Frontend.collections: CollectionsPage,
    # URLs.Frontend.stamps_manager: StampsManagerPage,
}


def configure_page(page: ft.Page):
    """Configure page title, fonts, and expansion."""
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
        font_family="Roboto"
    )
    
    page.window.icon = FAV_ICON


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

    try:
        await init_language()
    except Exception as e:
        page.add(ft.Text(f"Failed to initialize language: {e}"))
        page.update()

    page.on_route_change = route_change
    page.on_view_pop = view_pop
    
    # Handle initial route directly
    route = URLs.Frontend.root
    prefs = ft.SharedPreferences()

    if route == URLs.Frontend.root:
        auth_token = await prefs.get(USER_JWT_TOKEN)
        if auth_token:
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