from nicegui import ui
from forms.login_form import LoginForm
from common.logger import Logger

class LoginPage(Logger):
    """
    The main page class for the /login route. 
    It manages the overall layout and handles the result of the LoginForm.
    """
    def __init__(self):
        super().__init__()
        self.token = None # To store the auth token or session info

        with ui.row().classes('w-full h-screen justify-center items-center'):
            # The LoginForm is initialized here, passing a method to handle success
            self.form = LoginForm(login_success_handler=self.handle_login_success)

    def handle_login_success(self, data: dict):
        """
        Callback function executed on successful API login.
        """
        # Store the token (assuming Django returns one like 'token' or 'key')
        self.token = data.get('token', 'TOKEN_NOT_FOUND')
        self.debug(f"Token: {self.token}")
        
        # Clear the page content
        self.form.delete()
        
        # Optional: Redirect to another page after successful login
        ui.navigate.to('/dashboard')