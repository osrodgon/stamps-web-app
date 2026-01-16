import os

from core.log_setup import log_setup
from core.urls import URLs
from fastapi import Request, Response
from nicegui import app, ui
from nicegui.client import Client
from nicegui.page import page
from pages.admin.stamps_manager_page import StampsManagerPage
from pages.auth.login_page import LoginPage
from pages.auth.signup_page import SignUpPage
from pages.collection.collections_page import CollectionsPage
from pages.not_found_page import NotFoundPage
from settings import APP_NAME, ASSETS_DIR, ASSETS_FOLDER_NAME, MOCK_LOGIN


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
        @page(URLs.Frontend.collections)
        def collections_page():
            """
            Displays the collections page
            """
            CollectionsPage()
            
        @page(URLs.Frontend.login)
        def login_page(request: Request):
            """
            Displays the login page.

            Args:
                request (Request): The FastAPI request object.
            """
            app.storage.user['language'] = 'es'
            LoginPage()
        
        @page(URLs.Frontend.signup)
        def signup_page(request: Request):
            """
            Displays the signup page.

            Args:
                request (Request): _description_
            """
            SignUpPage()
        
        @page(URLs.Frontend.logout)    
        def logout(request: Request):
            """
            Logs out the user and redirects to the login page.

            Args:
                request (Request): The FastAPI request object.
            """
            app.storage.user.clear()
            ui.navigate.to(URLs.Frontend.login)
            
        @page(URLs.Frontend.stamps_manager)
        async def stamps_manager(request: Request):
            """
            Displays the stamp manager page

            Args:
                request (Request): _description_
            """
            StampsManagerPage()
            
        @page(URLs.Frontend.root)
        async def main_page(request: Request):
            """
            The main entry point of the application.
            Redirects to dashboard if authenticated, otherwise to login.

            Args:
                request (Request): The FastAPI request object.
            """
            app.storage.user['language'] = 'es'
                
            if MOCK_LOGIN:
                """
                This is just for testing and developing purposes.
                
                To avoid manual login, if test mode is enabled, it will autologin
                using the test user name and password defined in the environment variables.
                
                THIS MUST BE ALWAYS DISABLED IN PRODUCTION.
                """
                test = LoginPage()
                await test.mock_login()
            else :
                if StampsApp.check_authentication(request): 
                    if app.storage.user.get('is_admin', False):
                        ui.navigate.to(URLs.Frontend.stamps_manager)
                    else:
                        ui.navigate.to(URLs.Frontend.collections)
                else:
                    ui.navigate.to(URLs.Frontend.login)
                
        @app.exception_handler(404)
        async def exception_handler_404(request: Request, exception: Exception) -> Response:
            with Client(page(URLs.Frontend.root), request=request) as client:
                NotFoundPage()

            return client.build_response(request, 404)
    
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
    APP_DIR = os.path.dirname(os.path.abspath(__file__))
    StampsApp.setup_static_logging_and_routes(APP_DIR)
    StampsApp.run(os.getenv("APP_STORAGE_SECRET"))
    