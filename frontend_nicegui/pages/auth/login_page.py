import requests
from base.base_page import BasePage
from components.auth.login_card import LoginCard
from components.branding.footer_branding import FooterBranding
from core.translations import _
from core.urls import URLs
from nicegui import app, ui
from settings import (
    BACKGROUND_IMG, MOCK_PASSWORD, MOCK_USER, 
    USER_NAME, USER_IS_ADMIN, USER_FIRST_NAME, USER_LANGUAGE,
    USER_LAST_NAME, USER_EMAIL, USER_JWT_TOKEN, USER_ID, DEFAULT_LANGUAGE
)
from services.auth_service import AuthService
from services.config_service import ConfigService


class LoginPage(ui.column, BasePage):
    """
    Represents the user login page.

    This class builds a full-screen login page, including a background image,
    a central login card for user input, and footer branding. It handles user
    authentication by making API calls to the backend.
    """
    login_card: LoginCard = None
    footer_branding: FooterBranding = None
    auth_service: AuthService = None
    
    def __init__(self):
        """
        Initializes the LoginPage.

        This constructor sets up the visual components of the login page,
        including applying a background image, centering the `LoginCard`,
        and adding `FooterBranding`.
        """
        self.log.debug('Initializing LoginPage...')
        super().__init__()
        self.auth_service = AuthService()
        self.config = ConfigService()
            
        with self.classes('w-full h-screen p-4'):
            self.set_background(BACKGROUND_IMG)
            
            with ui.column().classes('w-full flex-grow justify-center items-center'):
                self.login_card = LoginCard(on_sign_in=self.call_rest_method)
            
            with ui.row().classes('absolute top-4 right-4 items-center gap-2 text-sm font-medium'):
                if app.storage.user.get(USER_LANGUAGE, DEFAULT_LANGUAGE) == 'en':
                    ui.link(_('branding.language_es', _language='es'), '#') \
                        .on('click', lambda: self._set_language('es')) \
                        .classes('text-gray-500 hover:text-primary no-underline transition-colors uppercase track-wide')
                else:
                    ui.link(_('branding.language_en', _language='en'), '#') \
                        .on('click', lambda: self._set_language('en')) \
                        .classes('text-gray-500 hover:text-primary no-underline transition-colors uppercase track-wide')
                        
            self.footer_branding = FooterBranding()
        
    async def _set_language(self, lang: str):
        """
        Sets the application language and persists this preference.
        
        Args:
            lang (str): The language code (en/es)
        """
        app.storage.user[USER_LANGUAGE] = lang
        ui.navigate.reload()

    async def call_rest_method(self):
        """
        Processes a login attempt by calling the backend API.

        This method first validates the user input from the `LoginCard`. If valid,
        it sends the credentials to the backend. It then handles the API response,
        triggering either the success flow or displaying an error notification.
        """
        self.log.debug('Handling login attempt...')
        if self.login_card.is_valid():
            self.log.debug("Login data valid. Attempting login...")
            payload = self.login_card.get_data()
            
            response = await self.auth_service.login(payload=payload)
            
            if response is None:
                error_msg = _('messages.no_response')
                self.log.error(error_msg)
                self.notify(error_msg, 'negative')
                return error_msg

            if response.status_code == requests.codes.ok:
                data = response.json()['data']
                self.log.debug(f"User Info: {data}")                
                
                if await self.login_success(data):
                    self.log.debug('Login successful')
                    return response
                else:
                    error_msg = _('messages.response_issue')
                    self.log.error(error_msg)
                    self.notify(error_msg, 'negative')
                    return error_msg

            else:
                data = response.json()
                error_msg = data['errors'][0]['message']
                self.log.error(f'Login failed: {error_msg}')
                self.login_card.notify(f'Error: {error_msg}', 'negative')
                return response
        else:
            error_msg = _('auth.username_password_required')
            self.log.debug("Login data invalid. Showing error message...")
            self.login_card.notify(error_msg, 'negative')
            return error_msg
        
    async def login_success(self, data: dict):
        """
        Handles a successful login response from the backend API.

        This method stores user and session information (like JWT token) in the
        application's user storage. It then removes the login page content and
        redirects the user to the appropriate page based on their role (admin or user).

        Args:
            data (dict):    A dictionary containing the successful login response data,
                            including 'token' and user details.

        Returns:
            bool: True if the login process completes successfully, False otherwise.
        """
        token = data.get('token', None)
        is_admin = data.get('payload', {}).get('is_admin', False)
        username = data.get('payload', {}).get('username', "Missing username")
        first_name = data.get('payload', {}).get('first_name', "No name")
        last_name = data.get('payload', {}).get('last_name', "No last name")
        email = data.get('payload', {}).get('email', "No email")
        user_id = data.get('payload', {}).get('user_id', None)
        
        if token is None:
            error_msg = _('messages.token_missing')
            self.log.error(error_msg)
            return False
        
        app.storage.user[USER_JWT_TOKEN] = token
        app.storage.user[USER_IS_ADMIN] = is_admin
        app.storage.user[USER_NAME] = username
        app.storage.user[USER_FIRST_NAME] = first_name
        app.storage.user[USER_LAST_NAME] = last_name
        app.storage.user[USER_EMAIL] = email
        app.storage.user[USER_ID] = user_id
        await self.config.load_user_config()
        
        self.log.debug(f"Token: {token[:10]}...")
        
        self.delete()
        
        if is_admin:
            ui.navigate.to(URLs.Frontend.stamps_manager)
        else:
            ui.navigate.to(URLs.Frontend.collections)
            
        return True
    
    async def mock_login(self):
        """
        Performs a mock login for development or testing purposes.

        This method uses credentials from environment variables (`MOCK_LOGIN_USER`
        and `MOCK_LOGIN_PASSWORD`) to log in. It is intended for automated
        testing or development scenarios where manual login is not desired.
        If the mock login fails, an error is displayed.
        """
        self.log.debug('Starting test mode...')
        
        if MOCK_USER and MOCK_PASSWORD:
            payload = {
                'username': MOCK_USER,
                'password': MOCK_PASSWORD,
            }
            
            response = await self.auth_service.login(payload=payload)
            
            if response and response.status_code == requests.codes.ok:
                data = response.json()['data']
                self.log.debug(f"User Info: {data}")
                await self.login_success(data)
            else:
                error_msg = _('messages.response_mock_login')
                self.log.error(error_msg)
                self.notify(error_msg, 'negative', timeout=0, close_button=_('ui.close'))
        else:
            self.log.debug("Test mode failed. Review environment variables.")