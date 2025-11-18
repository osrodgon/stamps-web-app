from nicegui import ui

from base.base_ui import BaseUI

class LoginCard(ui.card, BaseUI):
    """A UI component representing a login card with username and password fields."""
    username: ui.input = None
    password: ui.input = None
    
    def __init__(self, on_sign_in: callable = None):
        """
        Initializes the LoginCard component.

        Args:
            on_sign_in (callable, optional):    A callback function to be executed 
                                                when the 'Sign In' button is clicked. Defaults to None.
        """
        super().__init__()
        self.log.debug('Initializing LoginCard...')
        with self.classes('w-auto p-6 shadow-xl rounded-lg'):
            ui.label('Sign In').classes('text-2xl font-semibold')
                
            ui.label('Enter your username and password to access your account').classes('text-gray-600')
            
            self.username = ui.input(label='Username').classes('w-full')
            self.password = ui.input(label='Password', password=True, password_toggle_button=True).classes('w-full')
            
            ui.button('Sign In', on_click=on_sign_in).classes('w-full')

                
            with ui.row().classes('w-full justify-center'):
                ui.label("Don't have an account?").classes('text-sm text-gray-600')
                ui.link('Sign up', '/signup').classes('text-blue-600 hover:text-blue-800 text-sm')
                
    def is_valid(self):
        """
        Validates that both username and password fields are filled.

        Returns:
            bool: True if both fields have values, False otherwise.
        """
        valid = bool(self.username.value and self.password.value)
        self.log.debug(f"Login form validation result: {valid}")
        return valid
    
    def get_data(self):
        """
        Retrieves the current data from the login form fields.

        Returns:
            dict: A dictionary containing the username and password.
        """
        data = {
            'username': self.username.value,
            'password': self.password.value,
        }
        self.log.debug("Retrieving data from login form.")
        return data