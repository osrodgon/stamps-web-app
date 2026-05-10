import flet as ft
import requests

from components.auth.login_card import LoginCard
from core.urls import URLs
from core.translations import _, set_language, get_language
from core.severity import Severity
from components.buttons.text_button import TextButton
from components.layout.brand import Brand
from services.auth_service import AuthService
from core.base_ui import BaseUI
from settings import BACKGROUND_IMG, USER_LANGUAGE

class LoginPage(ft.View, BaseUI):
    """
    The login page view for the Stamps web application.

    This page provides the user interface for authentication, featuring:
    -   A background image (if available)
    -   A centered login card with username/password fields
    -   A language selector button (top-right) for switching between
        English and Spanish

    The page extends both ft.View (for routing) and BaseUI (for logging
    and common utilities). Language changes are persisted to SharedPreferences
    and synchronized with the translation module.

    Attributes:
        background (ft.Container): The background image container.
        lang_button (ft.Container): The language selector button container.
        login_container (ft.Container): The container holding the LoginCard.
        prefs (ft.SharedPreferences): SharedPreferences instance for
            persisting language preferences.
    """

    main_page: ft.Page
    background: ft.Container
    lang_button: ft.Container
    login_container: ft.Container
    prefs: ft.SharedPreferences
    auth_service: AuthService
    login_card: LoginCard
    
    def __init__(self, page: ft.Page):
        """
        Initializes the LoginPage with UI components and layout.

        Sets up the background, language selector, and login card.
        The language button text is determined by the current language
        (shows 'EN' if Spanish is active, 'ES' if English is active).

        Args:
            page (ft.Page): The root Flet page instance, used for
                navigation and page-level operations.
        """
        self.log.debug("Initializing LoginPage...")
        self.main_page = page
        self.prefs = ft.SharedPreferences()
        self.auth_service = AuthService()
        
        # Background Image (only if file exists)
        self.background = self._set_background(BACKGROUND_IMG)

        # Language Selector (Top Right)
        self.log.debug("Loading language selector control...")
        if get_language() == "es":
            lang_text = _("branding.language_en").upper()
        else:
            lang_text = _("branding.language_es").upper()
        self.lang_button = ft.Container(
            content = TextButton(
                text=lang_text,
                size=14,
                font_family="Roboto-Bold",
                on_click=self._handle_language_change
            ),
            padding=10,
            top=0,
            right=0
        )

        # Login Card - Centered
        self.log.debug("Loading Login Card...")
        self.login_card = LoginCard(on_login_click=self.on_login, on_sign_up_click=self._handle_sign_up)
        self.login_container = ft.Container(
            content=self.login_card,
            alignment=ft.Alignment.CENTER,
            expand=True
        )
        
        # Branding - Always bottom center
        self.log.debug("Loading Collectibles branding...")
        self.collectibles = Brand()
        
        # Stack with all controls
        self.stack = ft.Stack(
            controls=[
                self.background,
                self.login_container,
                self.lang_button,
                self.collectibles
            ],
            expand=True
        )

        super().__init__(
            route=URLs.Frontend.login,
            padding=0,
            controls=[self.stack]
        )
        
    async def on_login(self, e):
        """
        Handles the login button click event.

        Extracts the username and password from the login card's data,
        validates that neither field is empty, and logs the attempt.

        Args:
            e (ft.ControlEvent): The click event from the login button.
                e.control.data is expected to be a dict containing
                'username' and 'password' TextField references.

        Note:
            This is a placeholder implementation. Actual authentication
            logic (e.g., API call, session creation) should be added.
        """
        if not self.login_card.is_valid():
            message = _('auth.username_password_required')
            self.log.debug(message)
            await self.show_notification(message, severity=Severity.WARNING, duration=1500)
            return message
        
        self.log.debug("Login data valid. Attempting login...")
        payload = self.login_card.get_payload()
        response = await self.auth_service.login(payload)
        
        # No response from backend
        if response is None:
            error_msg = _('messages.no_response')
            self.log.error(error_msg)
            await self.show_notification(error_msg, severity=Severity.ERROR, duration=1500)
            return error_msg
        
        data = response.json()
        # Login failed
        if response.status_code != requests.codes.ok:
            error_msg = data['errors'][0]['message']
            self.log.error(f'Login failed: {error_msg}')
            await self.show_notification(f'Error: {error_msg}', severity=Severity.ERROR, duration=1500)
            return response
        
        # Login Success. Store auth token and user data in SharedPreferences
        self.log.debug("Login successful")
        token = data["data"].get("token", None)
        user_data = data["data"].get("payload", None)
        if token and user_data:
            self.log.debug("Auth token and user data stored in SharedPreferences")
            await self._save_user(token, user_data)
            

        # Redirect based on user type
        if user_data.get("is_admin"):
            await self.main_page.push_route(URLs.Frontend.stamps_manager)
        else:
            await self.main_page.push_route(URLs.Frontend.collections)


    async def _handle_sign_up(self, e):
        """Navigate to the sign-up page."""
        self.log.debug("Navigating to Sign Up page")
        await self.main_page.push_route(URLs.Frontend.signup)
        
    async def _handle_language_change(self, e):
        """
        Handles the language selector button click event.

        Toggles the application language between English ('en') and
        Spanish ('es'). The button text updates to show the language
        that will be switched to when clicked (e.g., shows 'EN' when
        Spanish is active).

        Persists the language choice to SharedPreferences and updates
        the translation module. Also refreshes the LoginCard to display
        translated text.

        Args:
            e (ft.ControlEvent): The click event from the language button.
                e.control.content.value contains the current button text.

        Note:
            After this method, call page.update() to reflect UI changes
            if not already triggered.
        """
        current_text = e.control.content.value
        
        if current_text == _("branding.language_es").upper():
            await self.prefs.set(USER_LANGUAGE, "es")
            set_language("es")  # Update the language in the translations module
            e.control.content.value = _("branding.language_en").upper()
            
            self.log.debug("Language changed to Spanish.")
        else:
            await self.prefs.set(USER_LANGUAGE, "en")
            set_language("en")  # Update the language in the translations module
            e.control.content.value = _("branding.language_es").upper()
            
            self.log.debug("Language changed to English.")
        
        # Update branding
        self.collectibles.update()
        
        # Update login card
        self.login_container.content.update() 
        