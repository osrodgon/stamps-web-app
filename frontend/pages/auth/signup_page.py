import asyncio
from nicegui import ui
import requests

from base.base_page import BasePage
from base.base_rest import BaseRest
from components.auth.signup_card import SignUpCard
from components.branding.footer_branding import FooterBranding
from core.translations import _
from core.urls import URLs
from settings import BACKGROUND_IMG, API_MASTER_KEY


class SignUpPage(ui.column, BasePage, BaseRest):
    signup_card: SignUpCard = None
    footer_branding: FooterBranding = None
    
    def __init__(self):
        self.log.debug('Initializing SignUpPage...')
        super().__init__()
        
        with ui.column().classes('w-full h-screen p-4'):
            self.set_background(BACKGROUND_IMG)
            
            with ui.column().classes('w-full flex-grow justify-center items-center'):
                self.signup_card = SignUpCard(on_sign_up=self.call_rest_method)
            
            self.footer_branding = FooterBranding()
            
    async def call_rest_method(self):
        self.log.debug('Handling signup attempt...')
        if self.signup_card.is_valid():
            self.log.debug("Signup data valid. Attempting to signup...")
            payload = self.signup_card.get_data()
            headers = {'Authorization': f'Api-Key {API_MASTER_KEY}'}
            
            response = await self._make_request(
                request_type=BaseRest.POST, 
                url=URLs.Backend.signup, 
                payload=payload, 
                headers=headers
            )
            
            if response is None:
                error_msg = _('no_response')
                self.log.error(error_msg)
                self.notify(error_msg, 'negative')
                return error_msg

            if response.status_code == requests.codes.created:
                data = response.json()['data']
                
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