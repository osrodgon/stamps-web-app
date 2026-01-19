from base.base_page import BasePage
from components.common.top_bar import TopBar
from components.stamps.issues_table import IssuesTable
from core.translations import _
from nicegui import ui, app
from services.stamps_service import StampsService
from settings import API_MASTER_KEY
import unicodedata


class StampsManagerPage(ui.column, BasePage):
    """
    The main administrative page for managing stamp issues.

    This page provides a robust interface for browsing and filtering stamp issues.
    Key features include:
    - **Year-based Filtering**: A dropdown to view issues from a specific year.
    - **Series Search**: A text input for filtering by series name (case/accent insensitive).
    - **Hybrid Filtering**: Local filtering when a year is selected, server-side search when not.
    - **Persistence**: Remembers the last viewed year across sessions.
    - **Inline Management**: Integrates with IssuesTable for direct CRUD operations.
    - **Stamp Gallery**: Automatically fetches and displays individual stamps when an issue is expanded.
    """
    top_bar: TopBar = None
    years_select = None
    series_filter = None
    table: IssuesTable = None
    stamps_service: StampsService = None
    print_types = []
    stamp_types = []
    all_issues = []
    
    def __init__(self):
        """
        Initializes the StampsManagerPage component.

        Sets up the full page layout including the TopBar with filtering controls
        (year selection and series search) and the main IssuesTable.
        It triggers the initial data load sequence.
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
                    self.years_select.props('dark clearable popup-content-class="bg-white year-select-popup drop-shadow-md"')

                    self.series_filter = ui.input(label=_("filter_series"))
                    self.series_filter.on('keydown.enter', self.filter_issues)
                    self.series_filter.on_value_change(lambda e: self.filter_issues() if not e.value else None)
                    self.series_filter.classes('w-64')
                    self.series_filter.props('dark clearable')

                self.table = IssuesTable(
                    on_save=lambda e: self.notify(e.args, timeout=0, close_button=_('close')),
                    on_delete=lambda e: self.notify(e.args)
                )
                self.table.on('expand', lambda e: self.handle_expand(e.args))
            
        ui.timer(0, self.load_issues_once, once=True)

    async def handle_expand(self, row_data):
        """
        Handles the expansion event triggered by the IssuesTable.

        This method implements lazy loading for stamp data. When a row is expanded:
        1. It checks if the stamps for that issue have already been loaded.
        2. If not, it fetches them from the backend using `StampsService.get_stamps`.
        3. Updates the specific row object in the table's state to ensure reactivity.
        4. Triggers a UI update to replace the loading spinner with the stamp gallery.

        Args:
            row_data (dict): The data of the row being expanded, including its ID.
        """
        issue_id = row_data.get('id')
        if not issue_id:
            return
            
        # Find the actual row object in our local data to ensure reactivity
        row = next((r for r in self.table.rows if r.get('id') == issue_id), None)
        if not row:
            return
            
        # If stamps are already loading or loaded, don't fetch again
        if row.get('stamps') is not None:
            return
            
        self.log.debug(f'Fetching stamps for issue {issue_id}...')
        response = await self.stamps_service.get_stamps(issue_id, api_key=API_MASTER_KEY)
        
        if self._is_valid_response(response):
            stamps_data = response.json().get('data', [])
            # Update the row in the table's state
            row['stamps'] = stamps_data
            
            # Also update in all_issues if we are in year view
            all_issue_row = next((r for r in self.all_issues if r.get('id') == issue_id), None)
            if all_issue_row:
                all_issue_row['stamps'] = stamps_data
                
            self.table.update()
        else:
            self.log.error(f"Failed to fetch stamps for issue {issue_id}")
            row['stamps'] = [] # Set to empty list to stop loading state
            self.table.update()

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
        Fetches stamp issues from the backend or applies local filtering.

        Depending on whether a 'year' is provided or a 'series_name' filter is active,
        this method either calls the backend API or triggers local filtering.
        It also handles data enrichment (injecting print/stamp type options)
        and persists the selected year to user storage.

        Args:
            year (int|str, optional): The year to fetch issues for. Can be None if
                                     searching globally by series name.
        """
        series = self.series_filter.value
        if series:
            series = self._normalize_string(series)

        if year:
            self.log.debug(f'Getting issues for year {year}...')
            response = await self.stamps_service.get_issues(year=year, api_key=API_MASTER_KEY)
        else:
            if series:
                self.log.debug(f'Getting issues for series {series}...')
                response = await self.stamps_service.get_issues(series_name=series, api_key=API_MASTER_KEY)
            else:
                self.log.debug('No year or series provided')
                self.table.rows = []
                self.table.update()
                return
        
        if self._is_valid_response(response):
            data = response.json()['data']
            
            for row in data:
                row['opts_print_types'] = self.print_types
                row['opts_stamp_types'] = self.stamp_types
            
            self.all_issues = data
            self.table.rows[:] = data
            self.table.update()
            
            if year:
                app.storage.user['current_year'] = year
            
            # Re-apply filter only if we fetched by year (not by series) implies data might need filtering
            if year and self.series_filter.value:
                await self.filter_issues()
        else:
            self.log.error(_('api_error', _language='en'))
            self.notify(_('api_error'), 'warning', timeout=0, close_button=_('close'))

    async def filter_issues(self, e=None):
        """
        Handles the logic for filtering issues based on the series filter input.

        - If a **year is selected**: Performs a local (client-side), case-insensitive,
          and accent-insensitive search within the already loaded issues.
        - If **no year is selected**: Triggers a backend search across the entire
          database using the normalized series name.

        Args:
            e (ojbect, optional): The event object from UI triggers (keyup/enter).
        """
        if self.years_select.value:
            # Client side filtering
            self.log.debug('Filtering issues locally...')
            filter_text = self._normalize_string(self.series_filter.value)
            
            if filter_text:
                filtered_issues = [
                    issue for issue in self.all_issues 
                    if issue.get('name') and filter_text in self._normalize_string(issue.get('name'))
                ]
                self.table.rows[:] = filtered_issues
            else:
                self.table.rows[:] = self.all_issues
            
            self.table.update()
        else:
            # Server side filtering
            self.log.debug('Filtering issues via backend...')
            # We pass None as year to trigger series search in get_issues
            # But we must ensure we don't cause infinite loop. 
            # get_issues will call filter_issues ONLY if year is passed.
            await self.get_issues(year=None)

    async def load_issues_once(self):
        """
        Loads the initial set of issues when the page starts.

        This method attempts to retrieve the user's last viewed year from storage
        and fetches issues for that year. If no year is stored, it defaults to 1850.
        It is scheduled to run once immediately after page initialization.
        """
        await self.get_years()
        await self.get_print_types()
        await self.get_stamp_types()

        if app.storage.user.get('current_year'):
            year = int(app.storage.user.get('current_year'))
            self.years_select.value = year
            await self.get_issues(year)
        else:
            self.years_select.value = 1850
            await self.get_issues(1850)
        self.series_filter.update()
            
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
    
    def _normalize_string(self, text: str) -> str:
        """
        Normalizes a string by converting it to lowercase and removing accents.
        
        Args:
            text (str): The string to normalize.
            
        Returns:
            str: The normalized string.
        """
        if not text:
            return ""
        
        # Normalize to NFD (Normalization Form Decomposition)
        # This separates characters from their accents
        nfd_form = unicodedata.normalize('NFD', text)
        
        # Filter out non-spacing marks (accents)
        return "".join(c for c in nfd_form if unicodedata.category(c) != 'Mn').lower()
