from base.base_page import BasePage

from components.common.top_bar import TopBar
from core.translations import _
from nicegui import ui


class CollectionsPage(ui.column, BasePage):
    top_bar: TopBar = None
    
    def __init__(self):
        super().__init__()
        self.log.debug('Initializing CollectionsPage...')
        
        self.top_bar = TopBar(_('collections_tile'))