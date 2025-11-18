import os
from nicegui import ui, app
from nicegui.page import page
from pages.auth.login_page import LoginPage

from settings import ASSETS_DIR, BACKGROUND_IMG

class App:
    """
    The main NiceGUI application configuration.
    """
    def __init__(self):
        self.__set_assets_folder()
        
        @page('/dashboard')
        def dashboard_page():
            ui.label('Welcome to the Dashboard!').classes('text-3xl font-bold p-10')
            ui.button('Go back to Login', on_click=lambda: ui.navigate.to('/login'))
            
        @page('/login')
        def login_page():
            self.__set_background_image(BACKGROUND_IMG)
            LoginPage()
            
        @page('/')
        def main_page():
            ui.navigate.to('/login')
            

        # Start the UI
        ui.run()
        
    def __set_assets_folder(self):
        SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

        # Define the local folder containing your images
        ASSETS_FOLDER_NAME = 'assets'
        ASSETS = os.path.join(SCRIPT_DIR, ASSETS_FOLDER_NAME)
        
        app.add_static_files(ASSETS_DIR, ASSETS)
        
    def __set_background_image(self, image: str):
        ui.query('body').style(
                f'background-image: url("{image}");'
                'background-size: cover;' # Makes the image cover the entire background
                'background-position: center;' # Centers the image
                'background-repeat: no-repeat;' # Prevents image tiling
                'height: 100vh;'            # Ensures the body is exactly the height of the viewport
                'overflow: hidden;'
            )
        

# Run the application
# if __name__ == '__main__':
app = App()