from nicegui import ui

from base.base_page import BasePage
from base.base_rest import BaseRest
from components.common.top_bar import TopBar
from settings import API_MASTER_KEY
from core.urls import URLs
from core.translations import _



class StampsManagerPage(ui.column, BasePage, BaseRest):
    """
    A page for managing stamps, displaying a year-based filter.

    This class sets up the user interface for the stamps management page,
    including a top navigation bar and a dropdown menu to filter stamps by year.
    It fetches the available years from a backend API to populate this dropdown.
    """
    top_bar: TopBar = None
    years_select = None
    
    def __init__(self):
        """
        Initializes the StampsManagerPage.

        This constructor sets up the page layout, including the top bar with
        extra controls for year selection. It also schedules an asynchronous
        task to fetch the years from the backend.
        """
        super().__init__()
        self.log.debug('Initializing StampsManagerPage...')
        
        self.top_bar = TopBar(_('stamps_manager_title'))
        
        with self:
            with self.top_bar.extra_controls:
                self.years_select = ui.select([], label='Select Year', on_change=lambda e: ui.notify(e.value)).classes('w-48')
            
        ui.timer(0, self.get_years, once=True)
    
    async def get_years(self):
        """
        Asynchronously fetches years from the backend and updates the UI.

        This method makes an API call to the backend to retrieve a list of years.
        On success, it populates the 'years_select' dropdown with the fetched years.
        On failure, it logs the error and displays a notification to the user.
        """
        self.log.debug('Getting years...')
        
        headers = {'Authorization': f'Api-Key {API_MASTER_KEY}'}
        
        response = await self._make_request(
            request_type=BaseRest.GET, 
            url=URLs.Backend.years, 
            payload=None, 
            headers=headers
        )
        
        if response is None:
            error_msg = _('no_response')
            self.log.error(error_msg)
            self.notify(error_msg, 'negative')
            return None

        if response.status_code == 200:
            data = response.json()['data']
            years = [item['year'] for item in data]
            
            self.years_select.options = years
            self.years_select.update()
        else:
            error_msg = _('response_issue')
            self.log.error(error_msg)
            self.notify(error_msg, 'negative')
            return None