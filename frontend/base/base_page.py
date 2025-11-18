from nicegui import ui

from utils.logger import Logger


class BasePage(Logger):
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
