from base.base_page import BasePage
from components.common.top_bar import TopBar
from components.stamps.issues_table import IssuesTable
from core.translations import _
from nicegui import ui, app
from services.stamps_service import StampsService
from settings import API_MASTER_KEY


class StampsManagerPage(ui.column, BasePage):
    """
    A page for managing stamps, displaying a year-based filter.

    This class sets up the user interface for the stamps management page,
    including a top navigation bar and a dropdown menu to filter stamps by year.
    It fetches the available years from a backend API to populate this dropdown.
    """
    top_bar: TopBar = None
    years_select = None
    table: IssuesTable = None
    stamps_service: StampsService = None
    print_types = []
    stamp_types = []
    
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
        
        self.configure_styles()
        
        self.top_bar = TopBar(_('stamps_manager_title'))
        self.classes('w-full h-screen no-wrap p-0 m-0 overflow-hidden')
        
        with self.classes('fixed inset-0 flex flex-col no-wrap overflow-hidden bg-white'):
            with ui.column().classes('w-full flex-grow p-4 mt-[80px] overflow-hidden flex flex-col no-wrap'):
                with self.top_bar.extra_controls:
                    self.years_select = ui.select([], label=_("select_year"), on_change=lambda e: self.get_issues(e.value))
                    self.years_select.classes('w-48')
                    self.years_select.props('dark popup-content-class="bg-white year-select-popup"')

                self.table = IssuesTable(
                    on_save=lambda e: self.notify(e.args, timeout=0, close_button=_('close')),
                    on_delete=lambda e: self.notify(e.args)
                )
            
        ui.timer(0, self.get_years, once=True)
        ui.timer(0, self.get_print_types, once=True)
        ui.timer(0, self.get_stamp_types, once=True)
        ui.timer(0, self.load_issues_once, once=True)
    
    def configure_styles(self):
        """Configures the page-specific styles."""
        ui.query('body').style('overflow: hidden; margin: 0; padding: 0;')
        # Force dropdown items to be black when using dark mode input but light menu
        ui.add_head_html('''
            <style>
                .year-select-popup .q-item, 
                .year-select-popup .q-item__label {
                    color: black !important;
                }
            </style>
        ''')

    async def get_years(self):
        """
        Asynchronously fetches years from the backend and updates the UI.

        This method makes an API call to the backend to retrieve a list of years.
        On success, it populates the 'years_select' dropdown with the fetched years.
        On failure, it logs the error and displays a notification to the user.
        """
        self.log.debug('Getting years...')
        
        response = await self.stamps_service.get_years(api_key=API_MASTER_KEY)
        
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
        
        response = await self.stamps_service.get_issues(year, api_key=API_MASTER_KEY)
        
        if self._is_valid_response(response):
            data = response.json()['data']
            
            for row in data:
                row['opts_print_types'] = self.print_types
                row['opts_stamp_types'] = self.stamp_types
            
            self.table.rows[:] = data
            self.table.update()
        else:
            self.log.error(_('api_error', _language='en'))
            self.notify(_('api_error'), 'warning', timeout=0, close_button=_('close'))

    async def load_issues_once(self):
        """
        Loads the initial set of issues when the page starts.

        This method attempts to retrieve the user's last viewed year from storage
        and fetches issues for that year. If no year is stored, it defaults to 1850.
        It is scheduled to run once immediately after page initialization.
        """
        if app.storage.user.get('current_year'):
            await self.get_issues(app.storage.user.get('current_year'))
        else:
            await self.get_issues(1850)
   
    async def get_print_types(self):
        """
        Asynchronously fetches the available print types from the backend.

        This method retrieves the list of print types from the API and populates
        the `print_types` list, which is used for the dropdown options in the
        stamps table editing interface.
        """
        self.log.debug('Getting print types...')
        
        response = await self.stamps_service.get_print_types(api_key=API_MASTER_KEY)
        
        if self._is_valid_response(response):
            data = response.json()['data']
            types_list = []
            
            for print_type in data:
                types_list.append(print_type['name'])
                
            self.print_types = types_list
        else:
            self.log.error(_('api_error', _language='en'))
            self.notify(_('api_error'), 'warning', timeout=0, close_button=_('close'))

    async def get_stamp_types(self):
        """
        Asynchronously fetches the available stamp types from the backend.

        This method retrieves the list of stamp types from the API and populates
        the `stamp_types` list, which is used for the dropdown options in the
        stamps table editing interface.
        """
        self.log.debug('Getting stamp types...')
        
        response = await self.stamps_service.get_stamp_types(api_key=API_MASTER_KEY)
        
        if self._is_valid_response(response):
            data = response.json()['data']
            types_list = []
            
            for stamp_type in data:
                types_list.append(stamp_type['name'])
                
            self.stamp_types = types_list
        else:
            self.log.error(_('api_error', _language='en'))
            self.notify(_('api_error'), 'warning', timeout=0, close_button=_('close'))  
