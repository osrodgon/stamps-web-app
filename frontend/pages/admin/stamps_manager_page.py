import flet as ft

from components.templates.standard_page import StandardPage
from components.layout.app_header import AppHeader
from core.translations import _

class StampsManagerPage(StandardPage):
    def __init__(self, page: ft.Page):
        super().__init__(page=page)
        
        # Set the AppHeader (will be created later)
        self.set_app_header(AppHeader())
        
        # Customize main content
        self.main.content = ft.Column([
            ft.Text(_("stamps.stamps_manager_title"))
        ])