from pathlib import Path
from base.base_page import BasePage
from components.common.top_bar import TopBar
from components.stamps.issues_table import IssuesTable
from core.translations import _
from nicegui import app, ui
from services.stamps_service import StampsService
from settings import IMAGE_DIR, NO_STAMP, USER_LANGUAGE
from core.numbers import Numbers


class StampsManagerPage(ui.column, BasePage):
    """
    The main administrative page for managing stamp issues.
    """
    # UI Constants
    MIN_SEARCH_LENGTH = 2
    CONTROL_WIDTH = 'w-64'
    ACTIVE_COLOR = 'white'
    INACTIVE_COLOR = 'grey-7'
    TEXT_OPACITY = 'opacity-70'
    
    # Data Keys
    STAMPS_KEY = 'stamps'
    ID_KEY = 'id'
    
    # Localization Keys
    ERR_API = 'messages.api_error'
    ERR_UNEXPECTED = 'messages.unexpected_error'

    # UI Components
    top_bar: TopBar = None
    years_range = None
    series_filter = None
    table: IssuesTable = None
    
    # Services
    stamps_service: StampsService = None
    
    # Data Storage
    print_types = []
    stamp_types = []
    all_issues = []
    
    # AI Series Lookup
    ai_dialog = None
    ai_name_input = None
    ai_date_input = None
    ai_result_container = None
    
    def __init__(self) -> None:
        """
        Initializes the StampsManagerPage component.
        
        This method sets up the page by initializing the StampsService, configuring
        styles, setting up the UI components, and loading the initial data.
        """
        super().__init__()
        self.log.debug('Initializing StampsManagerPage...')
        self.stamps_service = StampsService()
        self.configure_styles()
        self._setup_ui()
        self._setup_ai_series_lookup() 
        ui.timer(0, self.load_initial_data, once=True)

    def _setup_ui(self) -> None:
        """
        Sets up the main UI components.
        
        This method creates the TopBar and IssuesTable components, configuring their
        layout and event handlers.
        """
        self.top_bar = TopBar(_('stamps.stamps_manager_title'))
        self.classes('w-full h-screen no-wrap p-0 m-0 overflow-hidden')

        with self.classes('fixed inset-0 flex flex-col no-wrap overflow-hidden bg-white'):
            with ui.column().classes('w-full flex-grow p-4 mt-[80px] overflow-hidden flex flex-col no-wrap'):
                self._setup_filters()
                self._setup_table()

    def _setup_filters(self) -> None:
        """
        Sets up the filtering controls in the top bar.
        
        This method creates the filter inputs for series/year and the years range slider,
        configuring their properties and event handlers.
        """
        with self.top_bar.filter_controls:
            with ui.row().classes('items-center gap-8'):
                self.series_filter = ui.input(label=_("filter.series_year"), on_change=self.filter_issues)
                self.series_filter.classes(self.CONTROL_WIDTH)
                self.series_filter.props('dark clearable debounce=600')
                with ui.tooltip().classes('bg-blue-grey-9 text-white px-4 py-2'):
                    # Using HTML or multiple labels to simulate the list
                    ui.label(_("filter.series_year_tooltip_header")).classes('font-bold mb-1')
                    ui.label(_("filter.series_year_tooltip_1"))
                    ui.label(_("filter.series_year_tooltip_2"))
                    ui.label(_("filter.series_year_tooltip_3"))
                    ui.label(_("filter.series_year_tooltip_4"))

                with ui.column().classes('items-center gap-2 self-end'):
                    self.slider_container = ui.row().classes(f'items-center {self.TEXT_OPACITY} pb-3')
                    with self.slider_container:
                        # This spinner will disappear once we load data
                        self.loading_spinner = ui.spinner(size='sm', color=self.ACTIVE_COLOR)

    def _setup_table(self) -> None:
        """
        Initializes and configures the issues table.
        
        This method creates the IssuesTable component and configures its event handlers
        for saving, deleting, expanding, and paginating issues.
        """
        self.table = IssuesTable(
            on_save=lambda e: self.notify(e.args, timeout=0, close_button=_('ui.close')),
            on_delete=lambda e: self.notify(e.args)
        )
        self.table.on('expand', lambda e: self.handle_expand(e.args))
        self.table.on('request', lambda e: self.handle_pagination_change(e.args))
        
    def _setup_ai_series_lookup(self) -> None:
        """
        Sets up the AI Series Lookup dialog.
        
        Creates a modal dialog with input fields for name and date,
        an extract button, and a results display area.
        """
        # Right drawer version - auto-expands with content
        with ui.right_drawer(value=False).props('bordered width=600') as drawer:
            self.ai_drawer = drawer
            with ui.column().classes('w-full gap-4 p-4'):
                ui.label(_('ai_series_lookup.title')).classes('text-h6 font-bold')
                
                # Input fields
                with ui.row().classes('w-full gap-4'):
                    self.ai_name_input = ui.input(
                        label=_('ai_series_lookup.name_label'),
                        placeholder=_('ai_series_lookup.name_placeholder')
                    ).classes('flex-grow')
                    
                    self.ai_date_input = ui.input(
                        label=_('ai_series_lookup.date_label'),
                        placeholder=_('ai_series_lookup.date_placeholder')
                    ).classes('flex-grow')
                
                # Extract button
                ui.button(
                    _('ai_series_lookup.extract_button'),
                    on_click=self._handle_ai_extraction
                ).props('color=primary')
                
                # Results container - let it grow naturally
                self.ai_result_container = ui.column().classes('w-auto gap-2')
        
        
        # with ui.dialog() as self.ai_dialog, ui.card().classes('w-[600px] max-h-[80vh]'):
        #     ui.label(_('ai_series_lookup.title')).classes('text-h6 font-bold mb-4')
            
        #     # Input fields
        #     with ui.row().classes('w-full gap-4 mb-4'):
        #         self.ai_name_input = ui.input(
        #             label=_('ai_series_lookup.name_label'),
        #             placeholder=_('ai_series_lookup.name_placeholder')
        #         ).classes('flex-1')
                
        #         self.ai_date_input = ui.input(
        #             label=_('ai_series_lookup.date_label'),
        #             placeholder=_('ai_series_lookup.date_placeholder')
        #         ).classes('flex-1')
            
        #     # Extract button
        #     with ui.row().classes('w-full justify-end gap-2 mb-4'):
        #         ui.button(
        #             _('ai_series_lookup.extract_button'),
        #             on_click=self._handle_ai_extraction
        #         ).props('color=primary')
            
        #     # Results container (scrollable)
        #     with ui.scroll_area().classes('w-full h-[400px]'):
        #         self.ai_result_container = ui.column().classes('w-full gap-2')
        
        # Add button to top bar in _setup_filters
        with self.top_bar.db_operations:
            ui.button(
                icon='psychology',
                on_click=self.ai_drawer.toggle
                # on_click=self.ai_dialog.open
            ).props('round color=teal').tooltip(_('ai_series_lookup.button_tooltip'))
        
    async def _handle_ai_extraction(self) -> None:
        """
        Handles the AI extraction process.
        
        Validates input, calls the AI service, and displays results
        or error messages.
        """
        name = (self.ai_name_input.value or "").strip()
        date = (self.ai_date_input.value or "").strip()
        
        if not name or not date:
            self.notify(_('ai_series_lookup.error_empty_fields'), 'warning')
            return
        
        # Show loading state
        self.ai_result_container.clear()
        with self.ai_result_container:
            ui.spinner(size='lg')
            ui.label(_('ai_series_lookup.loading'))
        
        try:
            response = await self.stamps_service.series_extraction(name, date)
            
            if response is None:
                self._display_ai_error(_('ai_series_lookup.error_network'))
                return
                
            status = response.status_code
            
            if status == 200:
                data = response.json().get('data', {})
                self._display_ai_results(data)
            elif status == 404:
                self._display_ai_error(_('ai_series_lookup.error_not_found'))
            elif status == 400:
                error_data = response.json().get('data', {})
                self._display_ai_error(error_data.get('message', _('ai_series_lookup.error_validation')))
            elif status == 500:
                self._display_ai_error(_('ai_series_lookup.error_service'))
            else:
                self._display_ai_error(_('ai_series_lookup.error_unknown'))
                
        except Exception as e:
            self.log.error(f'AI extraction error: {e}')
            self._display_ai_error(_('ai_series_lookup.error_unknown'))
    
    def _display_ai_results(self, data: dict) -> None:
        """
        Displays AI extraction results in the dialog.
        
        Shows all extracted fields and provides options to save
        or view individual stamps.
        
        Args:
            data: The AI response data dictionary
        """
        self.ai_result_container.clear()
        
        with self.ai_result_container:
            # Get user language
            lang = app.storage.user.get(USER_LANGUAGE, 'en')

            # Header
            ui.label(data.get('issue_name', 'N/A')).classes('text-h6 font-bold')
            
            # Details grid
            with ui.grid().classes('w-full grid-cols-2 gap-2 text-sm'):
                self._add_result_field(_('ai_series_lookup.field_issue_date'), data.get('issue_date'))
                self._add_result_field(_('ai_series_lookup.field_artist'), data.get('artist'))
                self._add_result_field(_('ai_series_lookup.field_printer'), data.get('printer'))
                self._add_result_field(_('ai_series_lookup.field_print_type'), data.get('print_type'))
                self._add_result_field(_('ai_series_lookup.field_perforation'), data.get('perforation'))
                self._add_result_field(_('ai_series_lookup.field_paper_type'), data.get('paper_type'))
                self._add_result_field(_('ai_series_lookup.field_stamp_type'), data.get('stamp_type'))
                self._add_result_field(
                    _('ai_series_lookup.field_total_printed'), 
                    Numbers.format_localized(data.get('total_printed'), lang, 0, 0)
                )
                self._add_result_field(
                    _('ai_series_lookup.field_market_value_mnh'), 
                    Numbers.format_localized(data.get('market_value_mnh'), lang, 2, 2, ' €')
                )
                self._add_result_field(
                    _('ai_series_lookup.field_market_value_used'), 
                    Numbers.format_localized(data.get('market_value_used'), lang, 2, 2, ' €')
                )
            
            # Description
            if data.get('description'):
                ui.label(_('ai_series_lookup.field_description')).classes('text-subtitle2 font-bold mt-2')
                ui.label(data.get('description')).classes('text-body2 text-justify')
                
            # Notes
            if data.get('notes'):
                ui.label(_('ai_series_lookup.field_notes')).classes('text-subtitle2 font-bold mt-2')
                ui.label(data.get('notes')).classes('text-body2 text-justify')
            
            # Stamps list
            stamps = data.get('stamps', [])
            if stamps:
                ui.label(_('ai_series_lookup.stamps_title')).classes('text-subtitle2 font-bold mt-4')
                for stamp in stamps:
                    with ui.card().classes('w-full pa-2 mb-2'):
                        ui.label(stamp.get('motive', 'N/A')).classes('font-bold')
                        
                        if stamp.get('description'):
                            ui.label(stamp.get('description')).classes('text-body2 text-justify')
                            
                        with ui.grid().classes('w-full grid-cols-2 gap-2 text-sm'):
                            self._add_result_field(_('ai_series_lookup.field_edifil_code'), stamp.get('edifil_code', 'N/A'))
                            self._add_result_field(_('ai_series_lookup.field_face_value'), stamp.get('face_value', 'N/A'))
                            amount_printed = stamp.get('amount_printed', 'N/A')
                            if amount_printed != data.get('total_printed'):
                                self._add_result_field(
                                    _('ai_series_lookup.field_total_printed'), 
                                    Numbers.format_localized(amount_printed, lang, 0, 0)
                                    )
                            self._add_result_field(_('ai_series_lookup.field_color'), stamp.get('color', 'N/A'))
                            self._add_result_field(
                                _('ai_series_lookup.field_market_value_mnh'), 
                                Numbers.format_localized(stamp.get('market_value_mnh', 'N/A'), lang, 2, 2, ' €')
                            )
                            self._add_result_field(
                                _('ai_series_lookup.field_market_value_used'), 
                                Numbers.format_localized(stamp.get('market_value_used', 'N/A'), lang, 2, 2, ' €')
                            )
                            
                            
                        
            
            # Action buttons
            with ui.row().classes('w-full justify-end gap-2 mt-4'):
                ui.button(
                    _('ai_series_lookup.save_button'),
                    on_click=lambda: self._handle_save_ai_issue(data)
                ).props('color=positive')
                # ui.button(
                #     _('ai_series_lookup.close_button'),
                #     on_click=self.ai_dialog.close
                # )
                
    def _display_ai_error(self, message: str) -> None:
        """
        Displays an error message in the AI results container.
        
        Args:
            message: The error message to display
        """
        self.ai_result_container.clear()
        
        with self.ai_result_container:
            with ui.row().classes('w-full items-center gap-2 text-negative'):
                ui.icon('error', size='lg')
                ui.label(message).classes('font-bold')
            
            ui.label(_('ai_series_lookup.error_help')).classes('text-caption text-grey-7 mt-2')
    
    async def _handle_save_ai_issue(self, data: dict) -> None:
        """
        Handles saving AI extracted data as a new issue.
        
        Converts AI response data to issue format and creates a new issue.
        
        Args:
            data: The AI response data dictionary
        """
        self.notify(_('ai_series_lookup.save_not_implemented'), 'info')
        # Convert AI data to issue format
        # issue_data = {
        #     'name': data.get('issue_name').split('\n')[0][:200],  # Use first line of description as name
        #     'date': data.get('issue_date'),
        #     'total_printed': data.get('total_printed'),
        #     'market_value': data.get('market_value_mnh'),
        #     'print_type': data.get('print_type'),
        #     'perforation': data.get('perforation'),
        #     'paper_type': data.get('paper_type'),
        #     'stamp_type': data.get('stamp_type'),
        #     'printer': data.get('printer'),
        #     'notes': data.get('notes'),
        # }
        
        # # Show loading
        # self.notify(_('ai_series_lookup.saving'), 'info', timeout=0)
        
        # try:
        #     response = await self.stamps_service.create_issue(issue_data)
            
        #     if response is None:
        #         self.notify(_('ai_series_lookup.error_network'), 'negative')
        #         return
                
        #     if response.status_code in [200, 201]:
        #         created_issue = response.json().get('data', {})
        #         issue_id = created_issue.get('id')
        #         self.notify(
        #             _('ai_series_lookup.save_success'), 
        #             'positive',
        #             close_button=_('ui.close')
        #         )
        #         # Optionally: refresh the issues table
        #         await self.get_issues()
        #         self.ai_dialog.close()
        #     else:
        #         error_msg = response.json().get('data', {}).get('message', _('ai_series_lookup.error_save_failed'))
        #         self.notify(error_msg, 'negative', timeout=0, close_button=_('ui.close'))
                
        # except Exception as e:
        #     self.log.error(f'Error saving AI issue: {e}')
        #     self.notify(_('ai_series_lookup.error_save_failed'), 'negative', timeout=0, close_button=_('ui.close'))

    def _add_result_field(self, label: str, value) -> None:
        """Helper to display a label-value pair in results."""
        ui.label(f"{label}:").classes('font-bold')
        ui.label(str(value) if value else 'N/A')
    
    async def handle_pagination_change(self, event_data: dict) -> None:
        """
        Handles pagination change events from the issues table.
        
        This method is triggered when the user navigates between pages, changes
        the number of rows per page, or sorts the table columns.
        
        Args:
            event_data (dict): The event data containing pagination information.
        """
        pagination = event_data.get('pagination', {})
        
        page = pagination.get('page', 1)
        rows_per_page = pagination.get('rowsPerPage', 15)
        sort_by = pagination.get('sortBy', 'date')
        descending = pagination.get('descending', False)
        
        self.log.debug(f'Pagination changed: page={page}, rows_per_page={rows_per_page} sort_by={sort_by} descending={descending}')
        await self.get_issues(page=page, page_size=rows_per_page, sort_by=sort_by, descending=descending)
        
    async def handle_expand(self, row_data: dict) -> None:
        """
        Handles the expansion event for a row in the IssuesTable.
        
        This method is triggered when the user expands a row to view the stamps
        associated with that issue.
        
        Args:
            row_data (dict): The data for the row that was expanded.
        """
        issue_id = row_data.get(self.ID_KEY)
        if not issue_id:
            return

        row = next((r for r in self.table.rows if r.get(self.ID_KEY) == issue_id), None)
        if not row or row.get(self.STAMPS_KEY) is not None:
            return

        self.log.debug(f'Fetching stamps for issue {issue_id}...')
        response = await self.stamps_service.get_stamps(issue_id)

        if self._is_valid_response(response):
            stamps_data = response.json().get('data', [])
            lang = app.storage.user.get(USER_LANGUAGE, 'en')
            for stamp in stamps_data:
                stamp['url'] = self._resolve_stamp_image_url(stamp.get('image'))
                # Format stamp numbers
                if stamp.get('market_value'):
                    stamp['market_value'] = Numbers.format_localized(stamp['market_value'], lang, 2, 2)
                if stamp.get('face_value'):
                    stamp['face_value'] = stamp['face_value']

            # Update the row in the table's state
            row[self.STAMPS_KEY] = stamps_data

            # Synchronize with all_issues if applicable
            all_issue_row = next((r for r in self.all_issues if r.get(self.ID_KEY) == issue_id), None)
            if all_issue_row:
                all_issue_row[self.STAMPS_KEY] = stamps_data

            self.table.update()
        else:
            self.log.error(f"Failed to fetch stamps for issue {issue_id}")
            row[self.STAMPS_KEY] = []
            self.table.update()

    async def get_years(self) -> None:
        """
        Asynchronously fetches the available years from the backend.

        On success, it calculates the range and initializes the range slider
        in the top bar for year-based filtering. On failure, it notifies the user.
        """
        self.log.debug('Getting years...')
        
        response = await self.stamps_service.get_years()
        
        if self._is_valid_response(response):
            data = response.json()['data']
        
            min_year = data[0]['year']
            max_year = data[-1]['year']
            
            self.slider_container.clear()
            self.slider_container.delete()
            
            with self.top_bar.filter_controls:
                with ui.column().classes('items-center gap-2 self-end'):
                    self.years_range = ui.range(
                        min=min_year,
                        max=max_year,
                        step=5,
                        value={'min': min_year, 'max': max_year},
                        on_change=self.filter_issues
                    ).classes(f'{self.CONTROL_WIDTH} compact-slider transition-opacity {self.TEXT_OPACITY}') \
                    .props(f'dark dense color="{self.ACTIVE_COLOR}" selection-color="{self.ACTIVE_COLOR}" track-color="grey-9"')

                    self.years_label = ui.label().bind_text_from(
                        self.years_range, 'value',
                        backward=lambda v: f"{_('filter.years_available')}: {v['min']} - {v['max']}"
                    ).classes(f'text-{self.ACTIVE_COLOR} mb-[-4px] {self.TEXT_OPACITY} order-first gap-10')

                    self.feedback_label = ui.label() \
                        .classes(f'text-{self.ACTIVE_COLOR} mb-[-4px] {self.TEXT_OPACITY} order-first gap-10 italic')

                    # Show total collection span as a hint
                    total_range = f"{min_year} - {max_year}"
                    self.feedback_label.set_text(f"{_('filter.use_filter_to_enable_slider')} ({total_range})")

                    self.enable_years_slider(False)
        else:
            self.log.error(_(self.ERR_API, _language='en'))
            self.notify(_(self.ERR_API), 'warning', timeout=0, close_button=_('ui.close'))

    async def get_issues(self, page: int=1, page_size: int=None, sort_by: str='date', descending: bool=False) -> None:
        """
        Fetches stamp issues based on the current filter criteria with optimized filtering.
        
        This method implements intelligent filtering logic that:
        - Validates and processes filter inputs safely
        - Determines the appropriate filtering strategy (year-only vs series-based)
        - Handles year pattern detection in series input (e.g., "202*" -> year range)
        - Manages loading states consistently across all code paths
        - Processes API responses with proper error handling and data formatting
        
        The method delegates specific tasks to specialized helper methods for better
        maintainability and testability.
        
        Args:
            page (int): The page number to fetch (default: 1).
            page_size (int): The number of items per page (default: None, uses table default).
            sort_by (str): The field to sort by (default: 'date').
            descending (bool): Whether to sort in descending order (default: False).
        
        Raises:
            Exception: If an unexpected error occurs during the filtering process.
        """
        # Get and validate inputs
        series_input = (self.series_filter.value or "").strip()
        year_range_str = self._get_year_range_string()
        
        if page_size is None:
            pagination = self.table.pagination
            page_size = pagination.get('rows_per_page', 15) if pagination else 15
            
        current_page = page
        
        # Set loading state early for consistent UX
        self.table.loading = True
        
        try:
            # Determine filtering strategy based on input validation
            if self._should_use_year_only_filter(series_input):
                self.log.debug(f"Getting issues for years: {year_range_str}")
                response = await self.stamps_service.get_issues(
                    year=year_range_str,
                    page=current_page,
                    page_size=page_size,
                    sort_by=sort_by,
                    descending=descending
                )
            else:
                if series_input[:-1].isdigit():
                    year_range_str=series_input
                    series_input=''
                    
                self.log.debug(f"Getting issues for years: {year_range_str} and issues name: {series_input}")
                    
                response = await self.stamps_service.get_issues(
                    year=year_range_str,
                    series_name=series_input,
                    page=current_page,
                    page_size=page_size,
                    sort_by=sort_by,
                    descending=descending
                )
                self.enable_years_slider(True)
            
            # Process response with centralized logic
            await self._process_paginated_response(response)
            
        except Exception as e:
            self.log.error(f'Error fetching issues: {e}')
            self.notify(_(self.ERR_UNEXPECTED), 'warning', timeout=0, close_button=_('ui.close'))
        finally:
            # Always ensure loading state is reset
            self.table.loading = False
    
    async def _process_paginated_response(self, response) -> None:
        """
        Processes a paginated API response for issues and updates the table state.

        This method handles:
        - Response validation and error checking
        - Data enrichment with metadata for editing
        - Number formatting for display based on user locale
        - Updating the table's pagination state based on response metadata

        Args:
            response (requests.Response | None): The API response to process.
        """
        if not self._is_valid_response(response):
            self.log.error(f'API error fetching paginated issues: {response.status_code if response else "No response"}')
            self.notify(_(self.ERR_API), 'warning', timeout=0, close_button=_('ui.close'))
            return
        
        data = response.json()
        
        # Extract data and pagination metadata
        issues  = data.get('data', {}).get('issues', [])
        pagination = data.get('data', {}).get('pagination', {})
        
        if not issues:
            self.table.rows = []
        else:
            total_count = pagination.get('total', len(issues))
            current_page = pagination.get('page', 1)
            current_page_size = pagination.get('page_size', 15)
            sort_by = pagination.get('sort_by', 'date')
            order = pagination.get('order', 'asc')
            descending = order == 'desc' 
            
            lang = app.storage.user.get(USER_LANGUAGE, 'en')
            
            for row in issues:
                row['opts_print_types'] = self.print_types
                row['opts_stamp_types'] = self.stamp_types
                
                # Format numbers for display
                row['total_printed'] = Numbers.format_localized(row.get('total_printed'), lang, 0, 0)
                row['market_value'] = Numbers.format_localized(row.get('market_value'), lang, 2, 2, ' €')
                row['perforation'] = Numbers.format_localized(row.get('perforation'), lang, 0, 2)
                
            self.all_issues = issues
            self.table.rows[:] = issues
            
            
            self.table.pagination = {
                'page': current_page,
                'rowsPerPage': current_page_size,
                'rowsNumber': total_count,
                'sortBy': sort_by,
                'descending': descending
            }

    def _get_year_range_string(self) -> str:
        """
        Safely extracts the year range string from the years_range slider.
        
        This method handles potential None values and missing keys gracefully
        to prevent runtime errors when the slider is not initialized.
        
        Returns:
            str: The year range string in format "min-max", or empty string if invalid.
        """
        if not self.years_range:
            return ""
        
        year_range_val = self.years_range.value
        if not year_range_val or 'min' not in year_range_val or 'max' not in year_range_val:
            return ""
        
        return f"{year_range_val['min']}-{year_range_val['max']}"

    def _should_use_year_only_filter(self, series_input: str) -> bool:
        """
        Determines if filtering should be year-only based on the series input.
        
        Year-only filtering is used when:
        - No series input is provided, OR
        - Series input is too short (less than MIN_SEARCH_LENGTH characters)
        
        Args:
            series_input (str): The series input string to evaluate.
            
        Returns:
            bool: True if year-only filtering should be used, False otherwise.
        """ 
        if not series_input:
            return True  # Enable year-only when no input
        
        return len(series_input.strip()) <= self.MIN_SEARCH_LENGTH

    def _resolve_stamp_image_url(self, image_name: str) -> str:
        """
        Resolves the full URL/path for a stamp image, falling back to NO_STAMP.
        
        This method checks if the image file exists at the expected path and returns
        the appropriate URL or the default NO_STAMP image path.
        
        Args:
            image_name (str): The name of the image file to resolve.
            
        Returns:
            str: The URL/path to the image, or NO_STAMP if not found.
        """
        if not image_name:
            return str(NO_STAMP)

        image_path = f"{IMAGE_DIR}{image_name}"
        root_path = Path(__file__).resolve().parent.parent.parent
        full_physical_path = root_path / image_path.lstrip('/')

        if Path(full_physical_path).exists():
            return image_path
        return str(NO_STAMP)

    async def _fetch_metadata_list(self, service_method, storage_attr: str, log_name: str) -> None:
        """
        Generic helper to fetch a list of items from the service and store them.

        Args:
            service_method (Callable): The service method to call.
            storage_attr (str): The attribute name on self to store the resulting list.
            log_name (str): A descriptive name for logging/errors.
        """
        self.log.debug(f'Fetching {log_name}...')
        response = await service_method()

        if self._is_valid_response(response):
            data = response.json().get('data', [])
            setattr(self, storage_attr, [item.get('name') for item in data])
        else:
            self.log.error(f'Failed to fetch {log_name}: {response.status_code if response else "No response"}')
            self.notify(_(self.ERR_API), 'warning', timeout=0, close_button=_('ui.close'))

    async def get_print_types(self) -> None:
        """Fetches available print types."""
        await self._fetch_metadata_list(self.stamps_service.get_print_types, 'print_types', 'print types')

    async def get_stamp_types(self) -> None:
        """Fetches available stamp types."""
        await self._fetch_metadata_list(self.stamps_service.get_stamp_types, 'stamp_types', 'stamp types')
    
    def configure_styles(self) -> None:
        """
        Configures the page-specific styles and injects necessary CSS.

        This includes:
        - Setting body overflow and margins.
        - Injecting custom CSS for the year selection popup and range slider.
        """
        ui.query('body').style('overflow: hidden; margin: 0; padding: 0;')
        # Force dropdown items to be black when using dark mode input but light menu
        ui.add_head_html('''
            <style>
                .year-select-popup .q-item, 
                .year-select-popup .q-item__label {
                    color: black !important;
                }
                .compact-slider .q-slider__track { 
                    height: 1px !important; 
                }
                .compact-slider .q-slider__thumb { 
                    width: 15px !important; 
                    height: 15px !important; 
                }
                /* Removes the thick 'focus' ring that appears when clicking */
                .compact-slider .q-slider__thumb:after {
                    display: none !important;
                }
            </style>
        ''')

    async def filter_issues(self, e=None) -> None:
        """
        Callback for filter UI changes.
        
        This method is triggered when the filter UI changes and initiates the
        process of fetching stamp issues based on the current filter criteria.
        
        Args:
            e: The event object (optional).
        """
        await self.get_issues()

    async def load_initial_data(self) -> None:
        """
        Loads all necessary initial data sequentially.
        
        This method fetches the following data in order:
        1. Years for the range slider
        2. Print types for filtering
        3. Stamp types for filtering
        4. Initial stamp issues
        
        After loading the data, it enables the years slider.
        """
        await self.get_years()
        await self.get_print_types()
        await self.get_stamp_types()
        await self.get_issues()
        self.enable_years_slider(True)

    def enable_years_slider(self, is_active: bool = True) -> None:
        """
        Enables or disables the years range slider and toggles associated labels.

        Args:
            is_active (bool): Whether to enable the slider. Defaults to True.
        """
        if is_active:
            self.years_range.props(f'color="{self.ACTIVE_COLOR}" selection-color="{self.ACTIVE_COLOR}"')
            self.years_range.enable()
        else:
            self.years_range.props(f'color="{self.INACTIVE_COLOR}" selection-color="{self.INACTIVE_COLOR}"')
            self.years_range.disable()

        self.years_label.set_visibility(is_active)
        self.feedback_label.set_visibility(not is_active)

        self.years_range.update()

