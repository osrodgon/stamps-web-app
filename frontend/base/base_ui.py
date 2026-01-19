from core.logger import Logger
from nicegui import ui


class BaseUI(Logger):
    """
    A base class for creating UI components in the application.

    This class provides common functionalities that UI components can inherit,
    such as logging and displaying notifications. It is designed to reduce
    code duplication and promote a consistent user experience across the app.
    """

    def __init__(self):
        """Initializes the BaseUI component and sets up the logger."""
        super().__init__()
        self.log.debug("BaseUI initialized.")

    def notify(
        self,
        message: str,
        type: str = "warning",
        timeout: float = 1.5,
        close_button: bool = False,
    ):
        """
        Displays a notification message to the user.

        Args:
            message (str): The message to be displayed in the notification.
            type (str, optional): The type of the notification, which affects
                its appearance. Common types include 'positive', 'negative',
                'warning', 'info', and 'ongoing'. Defaults to 'warning'.
            timeout (float, optional): The duration in seconds for which the
                notification is visible. A value of 0 makes it permanent until
                closed. Defaults to 1.5.
            close_button (bool, optional): If True, a close button is displayed
                on the notification, allowing the user to dismiss it manually.
                Defaults to False.
        """
        self.log.debug(f"Displaying notification: '{message}' with type: {type}")
        ui.notification(
            message, type=type, progress=True, timeout=timeout, close_button=close_button
        )