from nicegui import ui
from nicegui.page import page
from pages.login_page import LoginPage

class App:
    """
    The main NiceGUI application configuration.
    """
    def __init__(self):
        # Initialize other pages (e.g., a simple dashboard for redirection)
        @page('/dashboard')
        def dashboard_page():
            ui.label('Welcome to the Dashboard!').classes('text-3xl font-bold p-10')
            ui.button('Go back to Login', on_click=lambda: ui.navigate.to('/login'))
            
        @page('/login')
        def login_page():
            LoginPage()

        # Start the UI
        ui.run()

# Run the application
# if __name__ == '__main__':
App()