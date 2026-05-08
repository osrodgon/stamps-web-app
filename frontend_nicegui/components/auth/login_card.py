from base.base_ui import BaseUI
from core.translations import _
from core.urls import URLs
from nicegui import ui


class LoginCard(ui.card, BaseUI):
    """A login card with username/password inputs, sign-in button, and sign-up link."""
    username: ui.input = None
    password: ui.input = None
    
    def __init__(self, on_sign_in: callable = None):
        """Build the login card with input fields, button, and sign-up link.

        Args:
            on_sign_in: Optional callback triggered on sign-in button click
                or Enter key press in either input field.
        """
        super().__init__()
        self.log.debug('Initializing LoginCard...')
        with self.classes('w-auto p-6 shadow-xl rounded-lg'):
            ui.label(_('auth.sign_in')).classes('text-2xl font-semibold')
                
            ui.label(_('auth.username_and_password')).classes('text-gray-600')
            
            self.username = ui.input(
                label=_('auth.username'),
            ).classes('w-full').on('keydown.enter', on_sign_in)

            self.password = ui.input(
                label=_('auth.password'), 
                password=True, 
                password_toggle_button=True
            ).classes('w-full').on('keydown.enter', on_sign_in)
            
            ui.button(_('auth.sign_in'), on_click=on_sign_in).classes('w-full')

                
            with ui.row().classes('w-full justify-center'):
                ui.label(_('auth.no_account')).classes('text-sm text-gray-600')
                ui.link(_('auth.sign_up'), URLs.Frontend.signup).classes('text-blue-600 hover:text-blue-800 text-sm')
                
    def is_valid(self):
        """Check that both username and password are filled in."""
        valid = bool(self.username.value) and bool(self.password.value)
        self.log.debug(f"Login form validation result: {valid}")
        return valid
    
    def get_data(self):
        """Return the current username and password as a dict."""
        data = {
            'username': self.username.value,
            'password': self.password.value,
        }
        self.log.debug("Retrieving data from login form.")
        return data