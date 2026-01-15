from nicegui import ui, app
import requests

from components.auth.login_card import LoginCard
from components.branding.footer_branding import FooterBranding
from base.base_page import BasePage
from base.base_rest import BaseRest
from core.urls import URLs
from settings import BACKGROUND_IMG
from core.translations import _

class LoginPage(ui.column, BasePage, BaseRest):
    """A page component for the user login screen."""
    login_card: LoginCard = None
    footer_branding: FooterBranding = None
    
    def __init__(self):
        """Initializes the LoginPage, setting up the background, login card, and footer."""
        self.log.debug('Initializing LoginPage...')
        super().__init__()
        
        with ui.column().classes('w-full h-screen p-4'):
            self.set_background(BACKGROUND_IMG)
            
            with ui.column().classes('w-full flex-grow justify-center items-center'):
                self.login_card = LoginCard(on_sign_in=self.call_rest_method)
            
            self.footer_branding = FooterBranding()
        
    async def call_rest_method(self):
        """
        Handles the login attempt by calling the backend REST API.

        Validates the form, sends the credentials to the backend,
        and handles both successful and failed login responses.
        """
        self.log.debug('Handling login attempt...')
        if self.login_card.is_valid():
            self.log.debug("Login data valid. Attempting login...")
            payload = self.login_card.get_data()
            
            response = await self._make_request(
                request_type=BaseRest.POST, 
                url=URLs.Backend.login, 
                payload=payload, 
                headers=None
            )
            
            if response is None:
                error_msg = _('no_response')
                self.log.error(error_msg)
                self.notify(error_msg, 'negative')
                return error_msg

            if response.status_code == requests.codes.ok:
                data = response.json()['data']
                self.log.debug(f"User Info: {data}")                
                
                if self.login_success(data):
                    self.log.debug('Login successful')
                    return response
                else:
                    error_msg = _('response_issue')
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
            error_msg = _('username_password_required')
            self.log.debug("Login data invalid. Showing error message...")
            self.login_card.notify(error_msg, 'negative')
            return error_msg
        
    def login_success(self, data: dict):
        """
        Handles the successful login response from the API.

        Stores the JWT token in the user's session storage, clears the
        login page content, and navigates to the dashboard.

        Args:
            data (dict): The data dictionary from the API response, expected to contain a 'token'.
        """
        token = data.get('token', None)
        is_admin = data.get('payload', False).get('is_admin', False)
        username = data.get('payload', False).get('username', "Missig username")
        first_name = data.get('payload', False).get('first_name', "No name")
        last_name = data.get('payload', False).get('last_name', "No last name")
        email = data.get('payload', False).get('email', "No email")
        
        if token is None:
            error_msg = _('token_missing')
            self.log.error(error_msg)
            return False
        
        app.storage.user['jwt_token'] = token
        app.storage.user['is_admin'] = is_admin
        app.storage.user['username'] = username
        app.storage.user['first_name'] = first_name
        app.storage.user['last_name'] = last_name
        app.storage.user['email'] = email
        
        self.log.debug(f"Token: {token[:10]}...")
        
        self.delete()
        
        if is_admin:
            ui.navigate.to(URLs.Frontend.stamps_manager)
        else:
            ui.navigate.to(URLs.Frontend.collections)
            
        return True