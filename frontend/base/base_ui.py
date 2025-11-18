from nicegui import ui

from utils.logger import Logger

class BaseUI(Logger):
    """A base class for UI components, providing common functionalities like notifications."""
    def __init__(self):
        """Initializes the BaseUI, setting up the logger."""
        super().__init__()
        self.log.debug("BaseUI initialized.")
        
    def notify(self, message: str, type: str='warning'):
        """
        Displays a notification message to the user.

        Args:
            message (str): The message to display in the notification.
            type (str, optional):   The type of notification (e.g., 'warning', 'positive', 'negative'). 
                                    Defaults to 'warning'.
        """
        self.log.debug(f"Displaying notification: '{message}' with type: {type}")
        ui.notification(message, type=type, progress=True, timeout=1.5)
        
        