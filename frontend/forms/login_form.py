from nicegui import ui
import requests

from common.abstract_form import AbstractForm
from settings import BACKEND_URL


class LoginForm(AbstractForm):
    """
    A form for user authentication.

    This class creates the UI for a login form and handles the logic for
    authenticating a user against a backend API. It includes fields for
    username and password, and a button to submit the credentials.
    """
    def __init__(self, login_success_handler):
        """
        Initializes the login form.

        Args:
            login_success_handler: A callable to be executed upon successful login.
        """
        super().__init__()
        self.username = ''
        self.password = ''
        self.login_success_handler = login_success_handler
        
        with self.classes('w-full max-w-sm p-6'):
            ui.input(
                'Username', 
                on_change=lambda e: self._set_username(e.value)
            ).bind_value(self, 'username').props('autofocus').classes('mt-4 w-full')
            
            ui.input(
                'Password', 
                password_toggle_button=True,
                on_change=lambda e: self._set_password(e.value)
            ).bind_value(self, 'password').props('type=password').classes('mt-4 w-full')

            with ui.row().classes('mt-4 w-full justify-between'):
                # Sign In button
                ui.button(
                    'Sign In', 
                    on_click=self.login
                ).classes('w-2/5')
                
                # Sign Up button (Calls the new handler)
                ui.button(
                    'Sign Up', 
                    # on_click=self.navigate_to_signup_handler, # <-- CHANGED THIS LINE
                    color='secondary'
                ).classes('w-2/5')
        

    def _set_username(self, value):
        """
        Sets the username and clears any existing error messages.

        Args:
            value: The username string from the input field.
        """
        self.username = value.strip()
        self._set_error_message('')

    def _set_password(self, value):
        """
        Sets the password and clears any existing error messages.

        Args:
            value: The password string from the input field.
        """
        self.password = value.strip()
        self._set_error_message('')
    
    async def login(self):
        """
        Handles the login attempt by sending credentials to the backend API.
        """
        self.debug('Login button clicked. Trying to login')
        if not self.username or not self.password:
            self._set_error_message ('Username and password are required.')
            return

        try:
            payload = {'username': self.username, 'password': self.password}
            
            response = await self._post(f"{BACKEND_URL}/login/", payload)

            if response.status_code == 200:
                data = response.json()['data']
                
                self.login_success_handler(data)
                self.debug('Login successful')
                self._set_error_message('')
            else:
                error_data = response.json()
                error_msg = error_data['errors'][0]['message']
                self.error(f'Login failed: {error_msg}')
                self._set_error_message(f'Error: {error_msg}', 'negative')
        except requests.exceptions.RequestException as e:
            self.error(f'Network error: {e}')
            self._set_error_message(f'Network Error: Could not connect to API.', 'negative')