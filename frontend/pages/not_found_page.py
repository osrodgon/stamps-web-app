import asyncio

import flet as ft
from base.base_ui import BaseUI
from core.translations import _
from core.urls import URLs
from core.components.primary_button import PrimaryButton


class NotFoundPage(ft.View, BaseUI):
    """A 404 Not Found page displayed for unknown routes.

    Shows a centered layout with a 404 message, descriptive text,
    and a button to navigate back to the home page.
    """

    def __init__(self, main_page: ft.Page):
        """Initialize the 404 page with centered message and home button."""
        super().__init__()
        self.main_page = main_page
        self.route = URLs.Frontend.not_found
        self.padding = 20
        self.alignment = ft.Alignment.CENTER

        self.controls = [
            ft.Column(
                alignment=ft.CrossAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Text(
                        "404",
                        size=150,
                        font_family="Roboto-Black",
                        color=ft.Colors.BLUE_700,
                    ),
                    ft.Text(
                        _('errors.you_are_lost'),
                        size=24,
                        font_family="Roboto-Bold",
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Container(
                        ft.Markdown(_('errors.page_not_found')),
                        alignment=ft.Alignment.CENTER,
                        margin=30
                    ),
                    PrimaryButton(
                        _('errors.take_me_home'),
                        icon=ft.Icons.HOME,
                        on_click=self._go_home,
                        expand=False
                    ),
                    ft.Text(
                        "Stamps App",
                        size=14,
                        color=ft.Colors.GREY_400,
                    ),
                ],
                spacing=10,
                tight=True,
                expand=True
            ),
        ]

    def _go_home(self, e):
        """Navigate to root page."""
        asyncio.create_task(self.main_page.push_route(URLs.Frontend.root))