"""
Login card component for user authentication.

This module provides the LoginCard component for user login with
username and password fields, including validation and error display.
"""

import flet as ft
from core.translations import _
from components.buttons.primary_button import PrimaryButton
from components.form.text_field import TextField
from components.buttons.link_button import LinkButton
from components.colors import GREY_700, DELETE_RED
from core.base_ui import BaseUI


class LoginCard(ft.Container, BaseUI):
    """A login card with username/password fields, sign-in button, and sign-up link.

    Composes text fields, buttons, and labels into a styled card layout.
    All translatable text is refreshed via update() when the locale changes.
    Supports validation feedback and error display.

    Attributes:
        username: Input field for the username.
        password: Input field for the password (with reveal toggle).
        sign_in: Button to trigger the login action.
        sign_in_header: Header text displaying 'Sign In'.
        sign_in_desc: Description text prompting username/password entry.
        sign_up_text: Text prompting users without an account.
        sign_up_button: Link button navigating to sign-up.
        error_message: Text control for displaying login errors.
        size: Default font size for text elements.
    """

    username: TextField
    password: TextField
    sign_in: PrimaryButton
    sign_in_header: ft.Text
    sign_in_desc: ft.Text
    sign_up_text: ft.Text
    sign_up_button: LinkButton
    error_message: ft.Text
    size: int = 14
    
    def __init__(self, on_login_click: callable, on_sign_up_click: callable) -> None:
        """Build the login card with text fields, buttons, and layout.

        The sign-in button's data property holds references to the username
        and password fields so the handler can read their values via
        ``e.control.data``.

        Args:
            on_login_click: Called when the sign-in button is clicked.
            on_sign_up_click: Called when the sign-up link is clicked.
        """
        self.log.debug("Initializing LoginCard...")
        
        super().__init__()
        
        self.on_login_click = on_login_click
        self.on_sign_up_click = on_sign_up_click
        
        self.sign_in_header = ft.Text(
            _("auth.sign_in"),
            size=24,
            font_family="Roboto-Bold",
            color=ft.Colors.BLACK,
        )
        self.sign_in_desc = ft.Text(
            _("auth.username_and_password"),
            size=self.size,
            font_family="Roboto",
            color=GREY_700,
            no_wrap=True
        )
        self.username = TextField(label=_('auth.username'))
        self.password = TextField(label=_('auth.password'), password=True, can_reveal_password=True)
        
        self.sign_in = PrimaryButton(
            text=_("auth.sign_in").upper(),
            on_click=self._handle_login_click,
            data={
                "username": self.username,
                "password": self.password
            }
        )
        
        self.sign_up_text = ft.Text(_("auth.no_account"), color=GREY_700, size=self.size, font_family="Roboto")
        self.sign_up_button = LinkButton(_("auth.sign_up"), on_click=self.on_sign_up_click, size=self.size)
        
        self.error_message = ft.Text(
            "",
            size=12,
            color=DELETE_RED,
            font_family="Roboto",
            visible=False
        )
        
        self.content = ft.Column(
            controls=[
                ft.Row(controls=[self.sign_in_header], tight=True),
                ft.Row(controls=[self.sign_in_desc], tight=True),
                ft.Row(controls=[self.username], tight=True),
                ft.Row(controls=[self.password], tight=True),
                ft.Row(controls=[self.error_message], tight=True),
                ft.Row(controls=[self.sign_in], tight=True),
                ft.Row(controls=[self.sign_up_text, self.sign_up_button], 
                        alignment=ft.MainAxisAlignment.CENTER
                )
            ],
            spacing=15,
            tight=True,
            intrinsic_width=True,
        )
        
        self.bgcolor = ft.Colors.WHITE
        self.padding = 20
        self.border_radius = 8
        self.shadow = ft.BoxShadow(blur_radius=15, color=ft.Colors.with_opacity(0.2, ft.Colors.BLACK))

    async def _handle_login_click(self, e: ft.ControlEvent) -> None:
        """Handle login button click with validation."""
        self.log.debug("Handling login button click...")
        
        self.clear_errors()
        
        if not self.is_valid():
            self._show_validation_errors()
            self.update()
            return
        
        self.update()
        await self.on_login_click(e)

    def _show_validation_errors(self) -> None:
        """Show error styling on invalid fields."""
        self.log.debug("Showing validation errors on login form")

        if not self.username.value:
            self.username.border_color = DELETE_RED
            self.username.focused_border_color = DELETE_RED
        
        if not self.password.value:
            self.password.border_color = DELETE_RED
            self.password.focused_border_color = DELETE_RED

    def clear_errors(self) -> None:
        """Clear all error states and messages."""
        self.log.debug("Clearing all error states and messages")
        
        self.error_message.value = ""
        self.error_message.visible = False
        self.username.border_color = None
        self.password.border_color = None

    def update(self) -> None:
        """Refresh all translatable text to match the current locale.

        Updates labels, button text, header, description, and sign-up prompt.
        Call ``page.update()`` afterward to re-render the component.
        """
        self.log.debug("Updating LoginCard text...")
        
        self.username.label = _('auth.username')
        self.password.label = _('auth.password')
        self.sign_in.content = ft.Text(_("auth.sign_in").upper())
        self.sign_in_header.value = _("auth.sign_in")
        self.sign_in_desc.value = _("auth.username_and_password")
        self.sign_up_text.value = _("auth.no_account")
        self.sign_up_button.content = ft.Text(_("auth.sign_up"))
        self.page.update()
    
    def is_valid(self) -> bool:
        """Check that both username and password are filled in."""
        valid = bool(self.username.value and self.username.value.strip()) and \
                bool(self.password.value and self.password.value.strip())
        self.log.debug(f"Login form validation result: {valid}")
        return valid
    
    def get_payload(self) -> dict[str, str]:
        """Return the current username and password as a dict."""
        self.log.debug("Getting login form payload...")
        
        return {
            "username": self.username.value,
            "password": self.password.value
        }