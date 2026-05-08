import requests
from base.base_ui import BaseUI
from nicegui import ui


class BasePage(BaseUI):
    """
    A base class for UI pages in the application.

    This class provides common functionalities that can be inherited by specific
    pages, such as setting the background and handling API responses. It extends
    BaseUI to include UI-related functionalities.
    """

    def __init__(self):
        """Initializes the BasePage, setting up the logger."""
        super().__init__()
        self.log.debug("BasePage initialized.")

    def set_background(self, image: str):
        """
        Sets the background image for the entire page.

        Args:
            image (str): The URL or path to the background image.
        """
        self.log.debug(f"Setting page background to: {image}")
        ui.query('body').style(
            f'background-image: url("{image}");'
            'background-size: cover;'
            'background-position: center;'
            'background-repeat: no-repeat;'
            'height: 100vh;'
            'overflow: hidden;'
        )

    def _is_valid_response(self, response) -> bool:
        """
        Validates the HTTP response from an API request.

        This method checks if the response is not None, has a successful
        status code (200 OK), and contains data.

        Args:
            response: The HTTP response object from the requests library.

        Returns:
            bool: True if the response is valid, False otherwise.
        """
        if response is None:
            self.log.error("API request failed, no response from server.")
            return False

        if response.status_code != requests.codes.ok:
            self.log.error(f'API request failed with error: {response.status_code}')
            return False

        if len(response.json()['data']) == 0:
            self.log.debug('API request failed, no data returned from server.')

        return True