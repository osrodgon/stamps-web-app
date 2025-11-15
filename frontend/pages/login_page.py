from nicegui import ui
from nicegui.page import page
from forms.login_form import LoginForm


# @page('/login') # Define the route using the @page decorator
class LoginPage:
    """
    The main page class for the /login route. 
    It manages the overall layout and handles the result of the LoginForm.
    """
    def __init__(self):
        self.token = None # To store the auth token or session info

        with ui.row().classes('w-full h-screen justify-center items-center'):
            # The LoginForm is initialized here, passing a method to handle success
            self.form = LoginForm(login_success_handler=self.handle_login_success)

    def handle_login_success(self, data: dict):
        """
        Callback function executed on successful API login.
        """
        # Store the token (assuming Django returns one like 'token' or 'key')
        self.token = data.get('key', 'TOKEN_NOT_FOUND')
        
        # Clear the page content
        self.form.delete()
        
        # Show a success message and the retrieved token
        with ui.column().classes('p-6 bg-green-100 rounded-lg shadow-xl text-center'):
            ui.icon('check_circle', size='4rem').classes('text-green-600')
            ui.label('Login Successful!').classes('text-3xl font-semibold text-green-700')
            ui.label(f'Your Auth Token:').classes('mt-4 text-lg')
            ui.code(self.token).classes('font-mono bg-white p-2 rounded')

            # Optional: Redirect to another page after successful login
            ui.timer(3.0, lambda: ui.navigate.to('/dashboard'), once=True)