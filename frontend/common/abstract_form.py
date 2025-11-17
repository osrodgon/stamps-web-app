from nicegui import ui
import asyncio
import requests


from common.logger import Logger

class AbstractForm(ui.card, Logger):
    """
    An abstract base class for creating form components with a consistent look and feel.

    This class provides a basic structure for forms, including error handling and
    notifications. It inherits from `nicegui.ui.card` for styling and `common.logger.Logger`
    for logging capabilities.

    Subclasses are expected to implement the `_build_form_content` method to define
    the specific fields and actions of the form.
    """
    def __init__(self):
        """Initializes the abstract form, setting up the card and logger."""
        super().__init__()
        self.error_message = ''
        with self.classes('w-full max-w-lg p-6'):
            self._build_form_content()

    def _build_form_content(self):
        """
        Builds the content of the form.

        This method must be implemented by subclasses to define the UI elements
        (inputs, buttons, etc.) that make up the form.
        """
        pass
        
    def notify(self, message: str, type: str='warning'):
        """
        Displays a notification message to the user.

        Args:
            message: The message to display in the notification.
            type: The type of notification (e.g., 'warning', 'positive', 'negative'). Defaults to 'warning'.
        """
        ui.notification(message, type=type, progress=True, timeout=1.5)

    def _set_error_message(self, message: str, type: str='warning'):
        """
        Sets an error message and displays it as a notification.

        Args:
            message: The error message to set. If empty, no notification is shown.
        """
        self.error_message = message
        if self.error_message != '':
            self.notify(message, type)
            
    async def _post(self, url: str, payload: dict) -> requests.Response:
        """
        Sends an asynchronous POST request to the specified URL.

        This method wraps a synchronous `requests.post` call in an `asyncio.to_thread`
        to avoid blocking the event loop.

        Args:
            url: The URL to send the POST request to.
            payload: The dictionary to send as the JSON body of the request.

        Returns:
            The `requests.Response` object from the POST request.
        """
        response = await asyncio.to_thread(
                requests.post, 
                url, 
                json=payload, 
                timeout=5
            )
        
        return response