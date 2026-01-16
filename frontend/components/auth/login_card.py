from base.base_ui import BaseUI
from core.translations import _
from core.urls import URLs
from nicegui import ui


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
            ui.label(_('sign_in')).classes('text-2xl font-semibold')
                
            ui.label(_('username_and_password')).classes('text-gray-600')
            
            self.username = ui.input(
                label=_('username'),
            ).classes('w-full')
            self.password = ui.input(
                label=_('password'), 
                password=True, 
                password_toggle_button=True
            ).classes('w-full')
            
            ui.button(_('sign_in'), on_click=on_sign_in).classes('w-full')

                
            with ui.row().classes('w-full justify-center'):
                ui.label(_('no_account')).classes('text-sm text-gray-600')
                ui.link(_('sign_up'), URLs.Frontend.signup).classes('text-blue-600 hover:text-blue-800 text-sm')
                
    def is_valid(self):
        """
        Validates that both username and password fields are filled.

        Returns:
            bool: True if both fields have values, False otherwise.
        """
        valid = bool(self.username.value) and bool(self.password.value)
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