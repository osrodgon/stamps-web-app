"""
Navigation drawer component for the application.

This module provides a side drawer (navigation menu) that slides in from
the left side of the screen. It displays user profile information,
navigation menu items, and the organization logo.
"""

import flet as ft

from settings import ORG_LOGO
from core.translations import _


class AppDrawer(ft.Container):
    """
    A sliding navigation drawer component.

    This component provides a side menu that slides in from the left edge
    of the screen. It includes:
    - User profile section with name and email
    - Menu items (Profile, Settings, Logout)
    - Organization logo at the bottom

    The drawer animates in/out with a smooth slide transition and can be
    triggered by a menu button in the header.

    Attributes:
        user_full_name (ft.Text): Display name of the logged-in user.
        user_email (ft.Text): Email address of the logged-in user.
    """

    user_full_name: ft.Text
    user_email: ft.Text

    def __init__(self, on_logout=None):
        """
        Initialize the AppDrawer component.

        Sets up the drawer layout with profile header, menu items, and logo.
        Configures animation properties for smooth slide transitions.
        """
        super().__init__()
        self.width = 300
        self.bgcolor = ft.Colors.GREY_50
        self.shadow = ft.BoxShadow(blur_radius=5, color=ft.Colors.BLACK_26)

        # Subtle right border to separate from main content
        self.border = ft.Border.only(right=ft.BorderSide(1, ft.Colors.BLACK_12))
        self.padding = ft.Border.only(top=0, left=0, right=0, bottom=0)

        self.offset = ft.Offset(-1, 0)
        self.animate_offset = ft.Animation(300, "decelerate")
        self.animate_size = ft.Animation(300, "decelerate")

        # 1. Profile Header Area
        self.user_full_name = ft.Text("Unknown", font_family="Roboto-Bold", size=18, color=ft.Colors.BLACK_87)
        self.user_email = ft.Text("Unknown", size=14, color=ft.Colors.BLUE_600)
        self.profile_header = ft.Container(
            content=ft.Row([
                ft.Icon(
                    ft.Icons.ACCOUNT_CIRCLE,
                    size=50,
                    color=ft.Colors.BLUE_400
                ),
                ft.Column([
                    self.user_full_name,
                    self.user_email,
                ], spacing=0)
            ]),
            bgcolor=ft.Colors.WHITE,
            padding=ft.Border.only(top=20, bottom=20, left=10, right=10),
            alignment=ft.Alignment.CENTER
        )

        # 2. Menu Items Area
        # Using a Column with expand=True so it pushes the logo to the bottom
        self.menu_items = ft.Column(
            controls=[
                ft.Divider(height=1, color=ft.Colors.BLACK),
                ft.ListTile(
                    leading=ft.Icon(ft.Icons.PERSON, color=ft.Colors.BLACK_54),
                    title=ft.Text(_("profile.profile"), color=ft.Colors.BLACK_87),
                    on_click=lambda _: print("Profile clicked")
                ),
                ft.ListTile(
                    leading=ft.Icon(ft.Icons.SETTINGS, color=ft.Colors.BLACK_54),
                    title=ft.Text(_("profile.settings"), color=ft.Colors.BLACK_87),
                    on_click=lambda _: print("Settings clicked")
                ),
                ft.Divider(height=1, color=ft.Colors.BLACK_12),
                ft.ListTile(
                    leading=ft.Icon(ft.Icons.LOGOUT, color=ft.Colors.RED_400),
                    title=ft.Text(_("auth.logout"), color=ft.Colors.RED_400),
                    on_click=on_logout
                ),
            ],
            expand=True,  # This takes up all available middle space
            scroll=ft.ScrollMode.ADAPTIVE,
            spacing=0
        )

        # 3. Logo Area (Bottom)
        self.logo_footer = ft.Container(
            content=ft.Column([
                ft.Image(
                    src=ORG_LOGO,  # Replace with your local assets path
                    width=None,
                    height=None
                ),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            alignment=ft.Alignment.BOTTOM_RIGHT,
            padding=ft.Border.only(right=20, bottom=20)
        )

        # Main Layout of the Drawer
        self.content = ft.Container(
            content=ft.Column(
                controls=[
                    self.profile_header,
                    self.menu_items,
                    self.logo_footer
                ],
                spacing=0,
                expand=True
            ),
            width=0,
            clip_behavior=ft.ClipBehavior.HARD_EDGE
        )

    def update_data(self, first_name: str, last_name: str, email: str) -> None:
        """
        Update the user profile information displayed in the drawer.

        Args:
            first_name (str): User's first name.
            last_name (str): User's last name.
            email (str): User's email address.
        """
        self.user_full_name.value = f"{first_name} {last_name}"
        self.user_email.value = email

        self.update()
        