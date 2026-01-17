from base.base_page import BasePage
from components.common.top_bar import TopBar
from core.translations import _
from nicegui import ui
from services.stamps_service import StampsService


class StampsManagerPage(ui.column, BasePage):
    """
    A page for managing stamps, displaying a year-based filter.

    This class sets up the user interface for the stamps management page,
    including a top navigation bar and a dropdown menu to filter stamps by year.
    It fetches the available years from a backend API to populate this dropdown.
    """
    top_bar: TopBar = None
    years_select = None
    grid = None
    stamps_service: StampsService = None
    
    def __init__(self):
        """
        Initializes the StampsManagerPage.

        This constructor sets up the page layout, including the top bar with
        extra controls for year selection. It also schedules an asynchronous
        task to fetch the years from the backend.
        """
        super().__init__()
        self.log.debug('Initializing StampsManagerPage...')
        self.stamps_service = StampsService()
        
        ui.query('body').style('overflow: hidden')
        
        self.top_bar = TopBar(_('stamps_manager_title'))
        self.classes('w-full h-screen no-wrap p-0 m-0 overflow-hidden')
        
        with self.classes('w-full h-full p-4 gap-4 overflow-hidden'):
            with self.top_bar.extra_controls:
                self.years_select = ui.select([], label=_("select_year"), on_change=lambda e: self.get_issues(e.value)).classes('w-48')
                
            self.grid = ui.aggrid({
                'columnDefs': [
                    {'headerName': 'Id', 'field': 'id', 'editable': False, 'hide': True},
                    {'headerName': 'Year', 'field': 'year', 'editable': False, 'hide': True},
                    {'headerName': 'Date', 'field': 'date', 'editable': True},
                    {'headerName': 'Name', 'field': 'name', 'editable': True},
                    {'headerName': 'Type', 'field': 'stamp_type', 'editable': True},
                    {'headerName': 'Print', 'field': 'print_type', 'editable': True},
                    {'headerName': 'Printed', 'field': 'total_printed', 'editable': True},
                    {'headerName': 'Perf', 'field': 'perforation', 'editable': True},
                    {'headerName': 'Value', 'field': 'market_value', 'editable': True},
                ],
                'rowData': [],
                'stopEditingWhenCellsLoseFocus': True,
            }).classes('w-full h-[calc(100vh-130px)]')
            
        ui.timer(0, self.get_years, once=True)
    
    async def get_years(self):
        """
        Asynchronously fetches years from the backend and updates the UI.

        This method makes an API call to the backend to retrieve a list of years.
        On success, it populates the 'years_select' dropdown with the fetched years.
        On failure, it logs the error and displays a notification to the user.
        """
        self.log.debug('Getting years...')
        
        response = await self.stamps_service.get_years()
        
        if self._is_valid_response(response):
            data = response.json()['data']
            years = [item['year'] for item in data]
            
            self.years_select.options = years
            self.years_select.update()
        else:
            self.log.error(_('api_error', _language='en'))
            self.notify(_('api_error'), 'warning', timeout=0, close_button=_('close'))
            
    async def get_issues(self, year):
        """
        Asynchronously fetches and displays issues for a selected year.
    
        This method is triggered when a year is selected from the dropdown. It calls
        the backend to get all stamp issues for that year. On success, it formats
        and displays the issue names and dates. If no issues are found, it
        displays a corresponding message. In case of an error or no response,
        it logs the problem and notifies the user.

        Args:
            year (str): The year for which to fetch the issues.
        """
        self.log.debug(f'Getting issues for year {year}...')
        
        response = await self.stamps_service.get_issues(year)
        
        if self._is_valid_response(response):
            data = response.json()['data']
            
            self.grid.options['rowData'] = data
            await ui.run_javascript('true')
            self.grid.run_grid_method('autoSizeColumns', ['date'])
        else:
            self.log.error(_('api_error', _language='en'))
            self.notify(_('api_error'), 'warning', timeout=0, close_button=_('close'))
        