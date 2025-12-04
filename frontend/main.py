import os
from fastapi import Request
from nicegui import ui, app
from nicegui.page import page
from dotenv import load_dotenv

from pages.auth.login_page import LoginPage
from utils.log_setup import log_setup

from settings import (
    APP_NAME, ASSETS_DIR, ASSETS_FOLDER_NAME
)

class StampsApp():
    """
    Main application class for the Stamps web application.
    Handles static file setup, logging, route registration, and authentication.
    """

    @staticmethod
    def set_background_image(image_url: str):
        """
        Applies a background image to the NiceGUI page body.

        Args:
            image_url (str): The URL of the image to be used as the background.
        """
        ui.query('body').style(
                f'background-image: url("{image_url}");'
                'background-size: cover;'
                'background-position: center;'
                'background-repeat: no-repeat;'
                'height: 100vh;'
                'overflow: hidden;'
            )
        
    @staticmethod
    def setup_static_logging_and_routes(root_dir: str):
        """
        Sets up logging, static files, and routes for the NiceGUI application.

        Args:
            root_dir (str): The root directory of the application, used to locate assets.
        """
        assets_path = os.path.join(root_dir, ASSETS_FOLDER_NAME)
        
        app.add_static_files(ASSETS_DIR, assets_path)
        log_setup()
        StampsApp.register_routes()
        
    @staticmethod
    def check_authentication(request: Request) -> bool:
        """
        Checks if the current request is authenticated.

        Args:
            request (Request): The FastAPI request object containing session information.

        Returns:
            bool: True if authenticated, False otherwise.
        """
        return app.storage.user.get('jwt_token') is not None
    
    @staticmethod
    def register_routes():
        """
        Registers all application routes using NiceGUI's `@page` decorator.
        """
        @page('/collections')
        def collections_page():
            """
            Displays the collections page.
            """
            ui.label('Welcome to the Collections!').classes('text-3xl font-bold p-10')
            ui.button('Go back to Login', on_click=lambda: ui.navigate.to('/login'))
            ui.button('Logout', on_click=lambda: ui.navigate.to('/logout'))
            
        @page('/login')
        def login_page(request: Request):
            """
            Displays the login page.

            Args:
                request (Request): The FastAPI request object.
            """
            LoginPage()
        
        @page('/logout')    
        def logout(request: Request):
            """
            Logs out the user and redirects to the login page.

            Args:
                request (Request): The FastAPI request object.
            """
            app.storage.user.clear()
            ui.navigate.to('/login')
            
        @page('/')
        async def main_page(request: Request):
            """
            The main entry point of the application.
            Redirects to dashboard if authenticated, otherwise to login.

            Args:
                request (Request): The FastAPI request object.
            """
            if StampsApp.check_authentication(request): 
                ui.navigate.to('/collections')
            else:
                ui.navigate.to('/login')
    
    @staticmethod            
    def run(storage_secret: str):
        """
        Runs the NiceGUI application with a specified title.
        """
        ui.run(title=APP_NAME, storage_secret=storage_secret)
                
if __name__ in {"__main__", "__mp_main__"}:
    """
    Entry point for the Stamps frontend application.
    Initializes the application, sets up static files, logging, and routes,
    then creates an instance of the App and runs it.
    """
    try:
        from dotenv import load_dotenv
        
        # Load variables from environment
        load_dotenv()
    except ImportError:
        pass
    APP_DIR = os.path.dirname(os.path.abspath(__file__))
    StampsApp.setup_static_logging_and_routes(APP_DIR)
    StampsApp.run(os.getenv("APP_STORAGE_SECRET"))