import os
import flet as ft

from core.logger import Logger
from core.translations import _
from core.severity import Severity
from settings import    ASSETS_DIR, USER_JWT_TOKEN, USER_IS_ADMIN, USER_ID, USER_NAME, \
                        USER_FIRST_NAME, USER_LAST_NAME, USER_EMAIL


class BaseUI(Logger):
    """Base class for UI components with logging and notification support."""

    def __init__(self):
        """Initialize BaseUI and set up the logger."""
        super().__init__()
        self.log.debug("BaseUI initialized.")

    def _set_background(self, image):
        """Create a background container with image or fallback color.

        Args:
            image: Filename of the background image in ASSETS_DIR.

        Returns:
            ft.Container: Expanded container with image or solid color.
        """
        image_path = os.path.join(ASSETS_DIR, image)

        background = ft.Container(
            expand=True,
            bgcolor=ft.Colors.BLUE_GREY_50
        )
        if os.path.exists(image_path):
            background = ft.Container(
                expand=True,
                image=ft.DecorationImage(
                        src=image,
                        fit=ft.BoxFit.COVER
                    )
            )
            self.log.debug(f"Loading background from {image_path}")
        else:
            self.log.warning(f"Background image not found. Using solid color instead.")
        return background

    async def _save_user(self, token, user_data):
        """Store user data in SharedPreferences.

        Args:
            token: JWT authentication token.
            user_data: Dict with user fields (user_id, username, is_admin, etc.).
        """
        prefs = ft.SharedPreferences()

        await prefs.set(USER_JWT_TOKEN, token)
        await prefs.set(USER_ID, user_data.get("user_id"))
        await prefs.set(USER_NAME, user_data.get("username"))
        await prefs.set(USER_IS_ADMIN, user_data.get("is_admin"))
        await prefs.set(USER_FIRST_NAME, user_data.get("first_name"))
        await prefs.set(USER_LAST_NAME, user_data.get("last_name"))
        await prefs.set(USER_EMAIL, user_data.get("email"))
        self.log.debug("User preferences saved.")

    async def _delete_user(self):
        """Remove all user data from SharedPreferences."""
        prefs = ft.SharedPreferences()

        await prefs.remove(USER_JWT_TOKEN)
        await prefs.remove(USER_ID)
        await prefs.remove(USER_NAME)
        await prefs.remove(USER_IS_ADMIN)
        await prefs.remove(USER_FIRST_NAME)
        await prefs.remove(USER_LAST_NAME)
        await prefs.remove(USER_EMAIL)
        self.log.debug("User preferences removed")
    
    def show_notification(self, message: str, severity: Severity = Severity.INFO, duration=2000):
        """Show a SnackBar notification with color based on severity.

        Args:
            message: The notification text.
            severity: Severity level determining the background color.
            duration: Milliseconds to show the notification.

        Note:
            Requires `self.main_page` to be set (the root ft.Page instance).
        """
        severity_colors = {
            Severity.INFO: ft.Colors.BLUE_300,
            Severity.SUCCESS: ft.Colors.GREEN_300,
            Severity.WARNING: ft.Colors.ORANGE_300,
            Severity.ERROR: ft.Colors.RED_300
        }
        bgcolor = severity_colors.get(severity, ft.Colors.BLUE_300)
        
        self.main_page.show_dialog(
            ft.SnackBar(
                content=ft.Text(
                    message, 
                    color=ft.Colors.BLACK, 
                    align=ft.Alignment.CENTER
                ),
                bgcolor=bgcolor,
                behavior=ft.SnackBarBehavior.FLOATING,
                duration=duration
            )
        )
        