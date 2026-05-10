import flet as ft
from core.translations import _
from components.buttons.primary_button import PrimaryButton
from components.form.text_field import TextField
from components.buttons.link_button import LinkButton
from components.colors import GREY_700
from core.base_ui import BaseUI


class LoginCard(ft.Container, BaseUI):
    """A login card with username/password fields, sign-in button, and sign-up link.

    Composes text fields, buttons, and labels into a styled card layout.
    All translatable text is refreshed via update() when the locale changes.

    Attributes:
        username: Input field for the username.
        password: Input field for the password (with reveal toggle).
        sign_in: Button to trigger the login action.
        sign_in_header: Header text displaying 'Sign In'.
        sign_in_desc: Description text prompting username/password entry.
        sign_up_text: Text prompting users without an account.
        sign_up_button: Link button navigating to sign-up.
        size: Default font size for text elements.
    """

    username: TextField
    password: TextField
    sign_in: PrimaryButton
    sign_in_header: ft.Text
    sign_in_desc: ft.Text
    sign_up_text: ft.Text
    sign_up_button: LinkButton
    size = 14
    
    def __init__(self, on_login_click, on_sign_up_click):
        """Build the login card with text fields, buttons, and layout.

        The sign-in button's data property holds references to the username
        and password fields so the handler can read their values via
        ``e.control.data``.

        Args:
            on_login_click: Called when the sign-in button is clicked.
            on_sign_up_click: Called when the sign-up link is clicked.
        """
        super().__init__()
        
        # Assign the on_login_click callback to an instance variable so it can be used in the button
        self.on_login_click = on_login_click
        self.on_sign_up_click = on_sign_up_click
        
        # Create the UI elements
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
            on_click=self.on_login_click,
            data={
                "username": self.username,
                "password": self.password
            }
        )
        self.sign_up_text = ft.Text(_("auth.no_account"), color=GREY_700, size=self.size, font_family="Roboto")
        self.sign_up_button = LinkButton(_("auth.sign_up"), on_click=self.on_sign_up_click, size=self.size)
        
        # Layout the elements in a column
        self.content = ft.Column(
            controls=[
                ft.Row(controls=[self.sign_in_header], tight=True),
                ft.Row(controls=[self.sign_in_desc], tight=True),
                ft.Row(controls=[self.username], tight=True),
                ft.Row(controls=[self.password], tight=True),
                ft.Row(controls=[self.sign_in], tight=True),
                ft.Row(controls=[self.sign_up_text, self.sign_up_button], 
                        alignment=ft.MainAxisAlignment.CENTER
                )
            ],
            spacing=15,
            tight=True,
            intrinsic_width=True,
        )
        
        # Style the container
        self.bgcolor = ft.Colors.WHITE
        self.padding = 20
        self.border_radius = 8
        self.shadow = ft.BoxShadow(blur_radius=15, color=ft.Colors.with_opacity(0.2, ft.Colors.BLACK))
        
    def update(self):
        """Refresh all translatable text to match the current locale.

        Updates labels, button text, header, description, and sign-up prompt.
        Call ``page.update()`` afterward to re-render the component.
        """
        self.username.label = _('auth.username')
        self.password.label = _('auth.password')
        self.sign_in.content = _("auth.sign_in").upper()
        self.sign_in_header.value = _("auth.sign_in")
        self.sign_in_desc.value = _("auth.username_and_password")
        self.sign_up_text.value = _("auth.no_account")
        self.sign_up_button.content = _("auth.sign_up")
                
        self.log.debug("LoginCard updated.")
    
    def is_valid(self):
        """Check that both username and password are filled in."""
        valid = bool(self.username.value) and bool(self.password.value)
        self.log.debug(f"Login form validation result: {valid}")
        return valid
    
    def get_payload(self):
        """Return the current username and password as a dict."""
        return {
            "username": self.username.value,
            "password": self.password.value
        }
