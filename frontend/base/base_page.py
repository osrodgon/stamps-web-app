import requests
from base.base_ui import BaseUI
from nicegui import ui


class BasePage(BaseUI):
    """A base class for UI pages, providing common functionalities like logging."""
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
        if response is None:
            self.log.error("API request failed, no response from server.")
            return False
        
        if response.status_code != requests.codes.ok:
            self.log.error(f'API request failed with error: {response.status_code}')
            return False
        
        if len(response.json()['data']) == 0:
            self.log.debug('API request failed, no data returned from server.')
            return False
        
        return True
    