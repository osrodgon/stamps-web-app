import flet as ft

from core.base_ui import BaseUI
from components.colors import GREY_700
from core.translations import _
from components.form.text_field import TextField
from components.buttons.primary_button import PrimaryButton
from core.utils import is_valid_email, is_strong_password
from components.constants import FONT_SIZE_DEFAULT, FONT_SIZE_HEADING, CARD_SPACING, CARD_PADDING, CARD_BORDER_RADIUS, CARD_SHADOW_BLUR, CARD_SHADOW_OPACITY

class SignupCard(ft.Container, BaseUI):
    """
    A signup card with first name, last name, username, email, password, 
    and confirm password fields.

    Provides a form for user registration with validation for all fields.
    The signup button is disabled until all required fields are filled.
    All translatable text is refreshed via update() when the locale changes.

    Attributes:
        sign_up_header: Header text displaying 'Sign Up'.
        sign_up_description: Description text prompting for account details.
        first_name: Input field for the user's first name.
        last_name: Input field for the user's last name.
        username: Input field for the username.
        email: Input field for the email address.
        password: Input field for the password (masked).
        confirm_password: Input field for password confirmation (masked).
        sign_up: Primary button to submit the signup form.
        cancel: Primary button to cancel and navigate back.
        size: Default font size for text elements.
    """

    sign_up_header: ft.Text
    sign_up_description: ft.Text
    first_name: TextField
    last_name: TextField
    username: TextField
    email: TextField
    password: TextField
    confirm_password: TextField
    sign_up : PrimaryButton
    cancel: PrimaryButton
    size = FONT_SIZE_DEFAULT
    
    def __init__(self, on_sign_up_click, on_sign_up_cancel):
        """
        Build the signup card with text fields, buttons, and layout.

        Creates all form fields and sets up validation handlers. The signup
        button is initially disabled until all fields have content.

        Args:
            on_sign_up_click: Called when the sign-up button is clicked.
            on_sign_up_cancel: Called when the cancel button is clicked.
        """
        self.log.debug("Initializing SignupCard...")
        
        super().__init__()
        
        self.on_sign_up_click = on_sign_up_click
        self.on_sign_up_cancel = on_sign_up_cancel
        
        # Create the UI elements
        self.sign_in_header = ft.Text(
            _("auth.sign_up"),
            size=FONT_SIZE_HEADING,
            font_family="Roboto-Bold",
            color=ft.Colors.BLACK,
        )
        self.sign_in_desc = ft.Text(
            _("auth.account_details"),
            size=self.size,
            font_family="Roboto",
            color=GREY_700,
            no_wrap=True
        )
        self.first_name = TextField(label=_("auth.first_name"))
        self.first_name.on_change = self._validate
        self.last_name = TextField(label=_("auth.last_name"))
        self.last_name.on_change=self._validate
        self.username = TextField(label=_("auth.username"))
        self.username.on_change=self._validate
        self.email = TextField(label=_("auth.email"))
        self.email.on_change=self._validate
        self.password = TextField(label=_('auth.password'), password=True, can_reveal_password=True)
        self.password.on_change=self._validate
        self.confirm_password = TextField(label=_('auth.confirm_password'), password=True, can_reveal_password=True)
        self.confirm_password.on_change=self._validate
        self.sign_up = PrimaryButton(
            text=_("auth.sign_up").upper(),
            on_click=self.on_sign_up_click,
        )
        self.sign_up.disabled = True
        self.sign_up.width = 200
        self.cancel = PrimaryButton(
            text=_("ui.cancel").upper(),
            on_click=self.on_sign_up_cancel,
        )
        
        
        # Layout the elements in a column
        self.content = ft.Column(
            controls=[
                ft.Row(controls=[self.sign_in_header], tight=True),
                ft.Row(controls=[self.sign_in_desc], tight=True),
                ft.Row(controls=[
                        self.first_name,
                        self.last_name
                    ], 
                    tight=True
                ),
                ft.Row(controls=[self.username], tight=True),
                ft.Row(controls=[self.email], tight=True),
                ft.Row(controls=[self.password], tight=True),
                ft.Row(controls=[self.confirm_password], tight=True),
                ft.Row(controls=[
                        self.sign_up, 
                        self.cancel
                    ], 
                    alignment=ft.MainAxisAlignment.CENTER
                )
            ],
            spacing=CARD_SPACING,
            tight=True,
            intrinsic_width=True,
        )
        
        # Style the container
        self.bgcolor = ft.Colors.WHITE
        self.padding = CARD_PADDING
        self.border_radius = CARD_BORDER_RADIUS
        self.shadow = ft.BoxShadow(blur_radius=CARD_SHADOW_BLUR, color=ft.Colors.with_opacity(CARD_SHADOW_OPACITY, ft.Colors.BLACK))
        
    def _validate(self):
        """
        Validate all form fields and enable/disable the submit button.

        Checks if all required fields have values and enables the signup
        button only when all fields are filled. Called on every field's
        on_change event to provide real-time feedback.
        """
        self.log.debug("Validating form fields...")
        
        is_valid_form = all([
            self.first_name.value,
            self.last_name.value,
            self.username.value,
            self.email.value,
            self.password.value,
            self.confirm_password.value
        ])
        
        
        self.sign_up.disabled = not is_valid_form
        self.page.update()
        
        self.log.debug(f"Signup form validation result: {is_valid_form}")
        return is_valid_form

    def is_valid(self):
        """
        Validate all form fields and set error messages for invalid fields.

        Performs comprehensive validation including:
        - Required field checks
        - Email format validation
        - Password strength validation
        - Password match verification

        Returns:
            bool: True if all fields are valid, False otherwise.
        """
        self.log.debug("Validating form fields...")
        
        self.first_name.error = _("ui.required") if not self.first_name.value else None
        self.last_name.error = _("ui.required") if not self.last_name.value else None
        self.username.error = _("ui.required") if not self.username.value else None
        
        if not self.email.value:
            self.email.error = _("ui.required")
        elif self.email.value and not is_valid_email(self.email.value):
            self.email.error = _("auth.invalid_email")
        else:
            self.email.error = None

        if not self.password.value:
            self.password.error = _("ui.required")
        elif self.password.value and not is_strong_password(self.password.value):
            self.password.error = _("auth.invalid_password")
        else:
            self.password.error = None

        if not self.confirm_password.value:
            self.confirm_password.error = _("ui.required")
        elif self.confirm_password.value != self.password.value:
            self.confirm_password.error = _("auth.password_not_match")
        else:
            self.confirm_password.error = None
        
        form_validated = all([
            self.first_name.value,
            self.last_name.value,
            self.username.value,
            is_valid_email(self.email.value),
            is_strong_password(self.password.value),
            self.confirm_password.value == self.password.value
        ])
        self.page.update()
        
        self.log.debug(f"Signup form validation result: {form_validated}")
        return form_validated
    
    def get_payload(self):
        """
        Return the current form data as a dictionary for API submission.

        Returns:
            dict: User registration data with keys: username, email, 
                  password, first_name, last_name.
        """
        self.log.debug("Getting signup form payload...")
        
        return {
            "username": self.username.value,
            "email": self.email.value,
            "password": self.password.value,
            "first_name": self.first_name.value,
            "last_name": self.last_name.value
        }