from nicegui import ui

from base.base_ui import BaseUI
from utils.translations import Translations


class FooterBranding(ui.column, BaseUI):
    """A UI component for the application's footer branding."""
    def __init__(self):
        """Initializes the FooterBranding component."""
        super().__init__()
        self.log.debug("Initializing FooterBranding...")

        with self.classes('w-full items-center flex-shrink-0 mt-auto mb-8'):
            ui.label(Translations.translate('L007')).classes('text-5xl font-extrabold text-[#2C4869] tracking-widest uppercase')
            with ui.row().classes('items-center justify-end'):
                ui.separator().classes('w-12 bg-gray-400 h-[2px]')
                ui.label(Translations.translate('L008')).classes('text-xl text-gray-700 font-normal mx-4')
                ui.separator().classes('w-12 bg-gray-400 h-[2px]')