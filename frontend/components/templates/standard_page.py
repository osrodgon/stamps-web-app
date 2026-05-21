import flet as ft
from core.base_ui import BaseUI
from core.urls import URLs
from core.translations import _
from components.buttons.alert_button import AlertButton
from components.buttons.default_button import DefaultButton

class StandardPage(ft.View, BaseUI):
    """
    A base page template with header and main content areas.
    
    Used as the base class for authenticated pages like:
    - Stamps Manager Page
    - Collections Page
    
    Layout:
    - Header: Contains AppHeader, fixed height (80px), expands horizontally
    - Main: Expands to fill remaining space (vertical & horizontal)
    
    Attributes:
        header (ft.Container): Header section containing AppHeader.
        main (ft.Container): Main content area that expands.
        main_page (ft.Page): The underlying Flet page instance.
    """
    
    header: ft.Container
    main: ft.Container
    main_page: ft.Page
    
    def __init__(self, page: ft.Page, header_height: int = 80):
        """
        Initialize StandardPage with header and main containers.
        
        Args:
            page: The Flet page instance.
            header_height: Height of the header in pixels. Default: 80.
        """
        self.main_page = page
        
        # Header - fixed height at top, contains AppHeader (to be created)
        self.header = ft.Container(
            height=header_height,
            expand=False,
        )
        
        # Main - expands to fill remaining space
        self.main = ft.Container(
            expand=True,
        )
        
        super().__init__(
            route=page.route,
            padding=0,
            controls=[
                ft.Column(
                    controls=[self.header, self.main],
                    expand=True,
                    spacing=0
                )
            ]
        )
    
    def set_app_header(self, app_header: ft.Container) -> ft.Container:
        """Set the AppHeader control in the header container.
        
        Args:
            app_header: The AppHeader control to display in the header.
            
        Returns:
            The app_header that was set.
        """
        self.header.content = app_header
        return app_header
    
    def update_header(self):
        """Update the header to reflect any changes made via add_* methods.
        
        Call this AFTER the page is fully initialized and after using
        add_left(), add_center(), or add_right() methods on the AppHeader.
        """
        if self.header.content and self.page:
            self.page.update()
            
    def request_settings(self) -> None:
        """Handle settings request from the header menu.
        
        Logs the event and is intended to be overridden by subclasses
        to provide navigation or modal behavior.
        """
        self.log.debug("Settings requested.")
        
    def request_profile(self) -> None:
        """Handle profile request from the header menu.
        
        Logs the event and is intended to be overridden by subclasses
        to provide navigation or modal behavior.
        """
        self.log.debug("Profile requested.")
        
    async def logout(self) -> None:
        """Perform logout by pushing the logout route.
        
        Delegates to the authentication system via URL routing and
        should trigger token invalidation on the backend.
        """
        self.log.debug("Logging out...")
        await self.main_page.push_route(URLs.Frontend.logout)

    def request_logout(self, e: ft.ControlEvent) -> None:
        """Show a confirmation dialog before logging out.
        
        Args:
            e: The Flet control event that triggered the logout request.
        """
        self.log.debug("Logout requested.")
        
        # 1. Create the 'Yes' action
        async def confirm_action(e: ft.ControlEvent) -> None:
            self.confirm_dialog.open = False
            self.main_page.update()
            await self.logout()

        # 2. Create the 'No' action
        def cancel_action(e: ft.ControlEvent) -> None:
            self.confirm_dialog.open = False
            self.main_page.update()

        # 3. Define the Dialog
        self.confirm_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(_("auth.logout_confirm"), font_family="Roboto-Bold"),
            content=ft.Text(_("auth.logout_confirm_message"), font_family="Roboto"),
            shape=ft.RoundedRectangleBorder(radius=8),
            actions=[
                DefaultButton(_("ui.cancel").upper(), on_click=cancel_action),
                AlertButton(_("auth.logout").upper(), on_click=confirm_action)
            ],
            actions_alignment="end",
        )
        
        if self.confirm_dialog not in self.page.overlay:
            self.page.overlay.append(self.confirm_dialog)

        # 4. Show the Dialog
        self.main_page.dialog = self.confirm_dialog
        self.confirm_dialog.open = True
        self.main_page.update()