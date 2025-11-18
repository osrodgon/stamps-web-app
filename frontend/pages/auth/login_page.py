from nicegui import ui, app
from components.auth.login_form import LoginForm
from utils.logger import Logger

class LoginPage(Logger):
    """
    The main page class for the /login route. 
    It manages the overall layout and handles the result of the LoginForm.
    """
    def __init__(self):
        super().__init__()
        
        with ui.column().classes('w-full h-screen p-4'):
            with ui.column().classes('w-full flex-grow justify-center items-center'):
                # The LoginForm is initialized here, passing a method to handle success
                self.form = LoginForm(login_success_handler=self.handle_login_success)
                
            with ui.column().classes('w-full items-center flex-shrink-0 mt-auto mb-8'):
                ui.label('COLLECTIBLES').classes('text-5xl font-extrabold text-[#2C4869] tracking-widest uppercase')
                with ui.row().classes('items-center justify-end'):
                    ui.separator().classes('w-12 bg-gray-400 h-[2px]')
                    ui.label('Your World of Stamps').classes('text-xl text-gray-700 font-normal mx-4')
                    ui.separator().classes('w-12 bg-gray-400 h-[2px]')        

    def handle_login_success(self, data: dict):
        """
        Callback function executed on successful API login.
        """
        # Store the token (assuming Django returns one like 'token' or 'key')
        token = data.get('token', None)
        if token is None:
            self.log.error("Could not obtain token from login response.")
            return
        
        app.storage.user['jwt_token'] = token
        self.log.debug(f"Token: {token[:10]}...")
        
        # Clear the page content
        self.form.delete()
        
        # Optional: Redirect to another page after successful login
        ui.navigate.to('/dashboard')