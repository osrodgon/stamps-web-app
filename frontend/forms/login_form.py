from nicegui import ui
import requests
import asyncio

from common.logger import Logger
from settings import BACKEND_URL


class LoginForm(ui.card, Logger):
    """
    A reusable class component for the login form structure and logic.
    Inherits from ui.card to provide a clean, contained look.
    """
    def __init__(self, login_success_handler):
        super().__init__()
        self.username = ''
        self.password = ''
        self.error_message = ui.label('').classes('text-red-600')
        self.login_success_handler = login_success_handler

        with self.classes('w-full max-w-sm p-6'):
            ui.label('Login').classes('text-2xl font-bold mb-4')

            # --- Form Inputs ---
            # Input fields are bound to the component's properties
            ui.input('Username', on_change=lambda e: self._set_username(e.value)).bind_value(self, 'username').props('autofocus')
            
            # Use type='password' to mask the input
            ui.input('Password', on_change=lambda e: self._set_password(e.value)).bind_value(self, 'password').props('type=password')
            
            self.error_message # Display the error message label

            # --- Action Button ---
            ui.button('Sign In', on_click=self.login).classes('mt-4 w-full')

    def _set_username(self, value):
        self.username = value.strip()
        self.error_message.set_text('')

    def _set_password(self, value):
        self.password = value.strip()
        self.error_message.set_text('')

    async def login(self):
        """
        Handles the login process by sending data to the Django REST API.
        """
        self.debug('Login button clicked. Trying to login')
        if not self.username or not self.password:
            self.error_message.set_text('Username and password are required.')
            return

        try:
            # Prepare the JSON payload for the Django API
            payload = {'username': self.username, 'password': self.password}
            
            # Run the network request in the background to keep the UI responsive
            response = await asyncio.to_thread(
                requests.post, 
                f"{BACKEND_URL}/login/", 
                json=payload, 
                timeout=5
            )

            if response.status_code == 200:
                # Successfully logged in (Django usually returns a token/user data)
                data = response.json()
                # Pass the successful result to the page handler
                self.login_success_handler(data)
                self.debug('Login successful')
                self.error_message.set_text('')
            else:
                # Handle API errors (e.g., 400 Bad Request for invalid credentials)
                error_data = response.json()
                error_msg = error_data.get('detail', error_data.get('non_field_errors', ['Login failed.'])[0])
                self.error(f'Login failed: {error_msg}')
                self.error_message.set_text(f'Error: {error_msg}')

        except requests.exceptions.RequestException as e:
            self.error(f'Network error: {e}')
            self.error_message.set_text(f'Network Error: Could not connect to API.')