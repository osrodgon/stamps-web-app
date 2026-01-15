from nicegui import ui

from base.base_page import BasePage
from base.base_rest import BaseRest
from components.common.top_bar import TopBar
from settings import API_MASTER_KEY
from core.urls import URLs
from core.translations import _



class StampsManagerPage(ui.column, BasePage, BaseRest):
    top_bar: TopBar = None
    
    def __init__(self):
        self.log.debug('Initializing StampsManagerPage...')
        super().__init__()
        
        self.top_bar = TopBar(_('stamps_manager_title'))
        