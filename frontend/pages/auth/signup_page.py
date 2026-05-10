import flet as ft
import requests

from core.base_ui import BaseUI
from core.urls import URLs
from components.layout.brand import Brand
from core.translations import _
from components.auth.signup_card import SignupCard
from core.severity import Severity
from services.auth_service import AuthService
from settings import BACKGROUND_IMG

class SignupPage(ft.View, BaseUI):
    main_page: ft.Page
    background: ft.Container
    signup_card: SignupCard
    collectibles: Brand
    auth_service: AuthService
    sign_up_card: SignupCard
    
    def __init__(self, page: ft.Page):
        self.log.debug("Initializating SignupPage...")
        self.main_page = page
        self.auth_service = AuthService()
        
        # Background Image (only if file exists)
        self.background = self._set_background(BACKGROUND_IMG)
        
        # Signup card. Centered
        self.log.debug("Loading Signup Card...")
        self.sign_up_card = SignupCard(on_sign_up_click=self.on_sign_up, on_sign_up_cancel=self._handle_sign_up_cancel)
        self.sign_up_container = ft.Container(
            content=self.sign_up_card,
            alignment=ft.Alignment.CENTER,
            expand=True
        )
        
        # Branding - Always bottom center
        self.log.debug("Loading Collectibles branding...")
        self.collectibles = Brand()
        
        # Stack with all controls
        self.stack = ft.Stack(
            controls=[
                self.background,
                self.sign_up_container,
                self.collectibles
            ],
            expand=True
        )
        
        super().__init__(
            route=URLs.Frontend.signup,
            padding=0,
            controls=[
                self.stack
            ]
        )
        
    async def on_sign_up(self):
        self.log.debug("Sign up button clicked")
        if self.sign_up_card.is_valid():
            self.log.debug("Sign up data valid. Attempting to create a user...")
            payload = self.sign_up_card.get_payload()
            response = await self.auth_service.signup(payload)
            
            # No response from backend
            if response is None:
                error_msg = _('messages.no_response')
                self.log.error(error_msg)
                await self.show_notification(error_msg, severity=Severity.ERROR, duration=1500)
                return error_msg
            
            data = response.json()
            # Login failed
            if response.status_code != requests.codes.created:
                error_msg = data['errors'][0]['message']
                self.log.error(f'Sing up failed: {error_msg}')
                await self.show_notification(f'Error: {error_msg}', severity=Severity.ERROR, duration=1500)
                return response
            
            # Sign up successfull
            await self.show_notification(_("auth.sign_up_success"), wait=True)
            await self.main_page.push_route(URLs.Frontend.login)
        self.main_page.update()
    
    async def _handle_sign_up_cancel(self):
        self.log.debug("Sign up cancelled.")
        await self.main_page.push_route(URLs.Frontend.login)