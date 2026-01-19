import asyncio

import requests
from base.base_page import BasePage
from components.auth.signup_card import SignUpCard
from components.branding.footer_branding import FooterBranding
from core.translations import _
from core.urls import URLs
from nicegui import ui
from settings import BACKGROUND_IMG
from services.auth_service import AuthService


class SignUpPage(ui.column, BasePage):
    """
    Represents the user sign-up page.

    This class constructs the user registration page, featuring a background
    image, a central `SignUpCard` for user data entry, and footer branding.
    It manages the sign-up process by communicating with the backend API.
    """
    signup_card: SignUpCard = None
    footer_branding: FooterBranding = None
    auth_service: AuthService = None
    
    def __init__(self):
        """
        Initializes the SignUpPage.

        This constructor sets up the visual elements of the page, including
        the background image, the centered `SignUpCard` component, and the
        `FooterBranding`.
        """
        self.log.debug('Initializing SignUpPage...')
        super().__init__()
        self.auth_service = AuthService()
        
        with self.classes('w-full h-screen p-4'):
            self.set_background(BACKGROUND_IMG)
            
            with ui.column().classes('w-full flex-grow justify-center items-center'):
                self.signup_card = SignUpCard(on_sign_up=self.call_rest_method, on_back=self.back_to_login)
            
            self.footer_branding = FooterBranding()
            
    async def call_rest_method(self):
        """
        Handles the user sign-up attempt by calling the backend API.

        This method validates the data from the `SignUpCard`. If the data is
        valid, it sends a request to the backend to create a new user. On a
        successful registration, it displays a success message and redirects
        to the login page. If registration fails, it shows an error message.
        """
        self.log.debug('Handling signup attempt...')
        if self.signup_card.is_valid():
            self.log.debug("Signup data valid. Attempting to signup...")
            payload = self.signup_card.get_data()
            response = await self.auth_service.signup(payload=payload)
            
            if response is None:
                error_msg = _('no_response')
                self.log.error(error_msg)
                self.notify(error_msg, 'negative')
                return error_msg

            if response.status_code == requests.codes.created:
                self.log.debug('Signup successful')
                self.notify(_('sign_up_sucess'), 'positive')
                await asyncio.sleep(3)
                ui.navigate.to(URLs.Frontend.login)
                
                return response
            else:
                data = response.json()
                error_msg = data['errors'][0]['message']
                self.log.error(f'Signup failed: {error_msg}')
                self.signup_card.notify(f'Error: {error_msg}', 'negative')
                
                return response
        else:
            error_msg = _('review_form_data')
            self.log.debug("Signup data not valid. Please review the form.")
            self.signup_card.notify(error_msg, 'negative')
            
            return error_msg
    
    def back_to_login(self):
        ui.navigate.to(URLs.Frontend.login)
        