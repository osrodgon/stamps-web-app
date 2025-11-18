from nicegui import ui, app

from components.auth.login_card import LoginCard
from components.branding.footer_branding import FooterBranding
from base.base_page import BasePage
from base.base_rest import BaseRest
from settings import BACKGROUND_IMG, BACKEND_URL

class LoginPage(ui.column, BasePage, BaseRest):
    """A page component for the user login screen."""
    login_card: LoginCard = None
    footer: FooterBranding = None
    
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
            
            response = await self._make_request(BaseRest.POST, f"{BACKEND_URL}/login/", payload)
            
            if response is None:
                self.log.error("Login request failed, no response from server.")
                self.notify("Login request failed, no response from server.", 'negative')
                return

            if response.status_code == 200:
                data = response.json()['data']
                
                self.login_success(data)
                self.log.debug('Login successful')
            else:
                data = response.json()
                error_msg = data['errors'][0]['message']
                self.log.error(f'Login failed: {error_msg}')
                self.login_card.notify(f'Error: {error_msg}', 'negative')
        else:
            self.log.debug("Login data invalid. Showing error message...")
            self.login_card.notify('Username and password are required.')
        
    def login_success(self, data: dict):
        """
        Handles the successful login response from the API.

        Stores the JWT token in the user's session storage, clears the
        login page content, and navigates to the dashboard.

        Args:
            data (dict): The data dictionary from the API response, expected to contain a 'token'.
        """
        token = data.get('token', None)
        if token is None:
            self.log.error("Could not obtain token from login response.")
            return
        
        app.storage.user['jwt_token'] = token
        self.log.debug(f"Token: {token[:10]}...")
        
        self.delete()
        
        ui.navigate.to('/collections')