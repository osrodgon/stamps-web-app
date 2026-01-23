import os
from pathlib import Path
from base.base_page import BasePage
from components.common.top_bar import TopBar
from components.stamps.issues_table import IssuesTable
from core.translations import _
from nicegui import ui
from services.stamps_service import StampsService
from settings import API_MASTER_KEY, IMAGE_DIR, NO_STAMP
import unicodedata


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
    ERR_API = 'api_error'

    top_bar: TopBar = None
    years_range = None
    series_filter = None
    table: IssuesTable = None
    stamps_service: StampsService = None
    print_types = []
    stamp_types = []
    all_issues = []
    
    def __init__(self) -> None:
        """
        Initializes the StampsManagerPage component.
        """
        super().__init__()
        self.log.debug('Initializing StampsManagerPage...')
        self.stamps_service = StampsService()

        self.configure_styles()
        self._setup_ui()

        ui.timer(0, self.load_initial_data, once=True)

    def _setup_ui(self) -> None:
        """Sets up the main UI components."""
        self.top_bar = TopBar(_('stamps_manager_title'))
        self.classes('w-full h-screen no-wrap p-0 m-0 overflow-hidden')

        with self.classes('fixed inset-0 flex flex-col no-wrap overflow-hidden bg-white'):
            with ui.column().classes('w-full flex-grow p-4 mt-[80px] overflow-hidden flex flex-col no-wrap'):
                self._setup_filters()
                self._setup_table()

    def _setup_filters(self) -> None:
        """Sets up the filtering controls in the top bar."""
        with self.top_bar.extra_controls:
            with ui.row().classes('items-center gap-8'):
                self.series_filter = ui.input(label=_("filter_series_year"), on_change=self.filter_issues)
                self.series_filter.classes(self.CONTROL_WIDTH)
                self.series_filter.props('dark clearable debounce=600')
                with ui.tooltip().classes('bg-blue-grey-9 text-white px-4 py-2'):
                    # Using HTML or multiple labels to simulate the list
                    ui.label(_("filter_series_year_tooltip_header")).classes('font-bold mb-1')
                    ui.label(_("filter_series_year_tooltip_1"))
                    ui.label(_("filter_series_year_tooltip_2"))
                    ui.label(_("filter_series_year_tooltip_3"))
                    ui.label(_("filter_series_year_tooltip_4"))

                with ui.column().classes('items-center gap-2 self-end'):
                    self.slider_container = ui.row().classes(f'items-center {self.TEXT_OPACITY} pb-3')
                    with self.slider_container:
                        # This spinner will disappear once we load data
                        self.loading_spinner = ui.spinner(size='sm', color=self.ACTIVE_COLOR)

    def _setup_table(self) -> None:
        """Initializes and configures the issues table."""
        self.table = IssuesTable(
            on_save=lambda e: self.notify(e.args, timeout=0, close_button=_('close')),
            on_delete=lambda e: self.notify(e.args)
        )
        self.table.on('expand', lambda e: self.handle_expand(e.args))

    def _convert_year_pattern_to_range(self, year_pattern: str) -> str:
        """Converts a year pattern to a range."""
        s = year_pattern.strip()
        
        if len(s) == 4 and s.endswith('*') and s[:-1].isdigit():
            prefix = s[:-1]
            return f'{prefix}0-{prefix}9'

        if len(s) == 3 and s.endswith('*') and s[:-1].isdigit():
            prefix = s[:-1]
            return f'{prefix}00-{prefix}99'

        if len(s) == 4 and s.isdigit():
            return int(s)

        return None
        
    async def handle_expand(self, row_data: dict) -> None:
        """
        Handles the expansion event for a row in the IssuesTable.
        """
        issue_id = row_data.get(self.ID_KEY)
        if not issue_id:
            return

        row = next((r for r in self.table.rows if r.get(self.ID_KEY) == issue_id), None)
        if not row or row.get(self.STAMPS_KEY) is not None:
            return

        self.log.debug(f'Fetching stamps for issue {issue_id}...')
        response = await self.stamps_service.get_stamps(issue_id, api_key=API_MASTER_KEY)

        if self._is_valid_response(response):
            stamps_data = response.json().get('data', [])
            for stamp in stamps_data:
                stamp['url'] = self._resolve_stamp_image_url(stamp.get('image'))

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

    def _resolve_stamp_image_url(self, image_name: str) -> str:
        """Resolves the full URL/path for a stamp image, falling back to NO_STAMP."""
        if not image_name:
            return str(NO_STAMP)

        image_path = f"{IMAGE_DIR}{image_name}"
        root_path = Path(__file__).resolve().parent.parent.parent
        full_physical_path = os.path.join(root_path, image_path.lstrip('/'))

        if os.path.exists(full_physical_path):
            return image_path
        return str(NO_STAMP)

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

    async def get_years(self) -> None:
        """
        Asynchronously fetches the available years from the backend.

        On success, it calculates the range and initializes the range slider
        in the top bar for year-based filtering. On failure, it notifies the user.
        """
        self.log.debug('Getting years...')
        
        response = await self.stamps_service.get_years(api_key=API_MASTER_KEY)
        
        if self._is_valid_response(response):
            data = response.json()['data']
        
            min_year = data[0]['year']
            max_year = data[-1]['year']
            
            self.slider_container.clear()
            self.slider_container.delete()
            
            with self.top_bar.extra_controls:
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
                        backward=lambda v: f"{_('years_available')}: {v['min']} - {v['max']}"
                    ).classes(f'text-{self.ACTIVE_COLOR} mb-[-4px] {self.TEXT_OPACITY} order-first gap-10')

                    self.feedback_label = ui.label() \
                        .classes(f'text-{self.ACTIVE_COLOR} mb-[-4px] {self.TEXT_OPACITY} order-first gap-10 italic')

                    # Show total collection span as a hint
                    total_range = f"{min_year} - {max_year}"
                    self.feedback_label.set_text(f"{_('use_filter_to_enable_slider')} ({total_range})")

                    self.enable_years_slider(False)
        else:
            self.log.error(_(self.ERR_API, _language='en'))
            self.notify(_(self.ERR_API), 'warning', timeout=0, close_button=_('close'))

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

    async def get_issues(self) -> None:
        """
        Fetches stamp issues based on the current filter criteria.
        """
        series_input = self.series_filter.value
        if not series_input or len(series_input) <= self.MIN_SEARCH_LENGTH:
            self.log.debug('Filter input too short or empty.')
            self.table.rows = []
            self.enable_years_slider(False)
            return

        normalized_series = self._normalize_string(series_input)
        year_filter = self._convert_year_pattern_to_range(normalized_series)

        if year_filter:
            self.enable_years_slider(False)
            
            self.log.debug(f'Searching by year or year range: {year_filter}')
            
            response = await self.stamps_service.get_issues(
                year=year_filter, 
                api_key=API_MASTER_KEY
            )
        else:
            self.enable_years_slider(True)

            year_range_val = self.years_range.value
            year_range_str = f"{year_range_val['min']}-{year_range_val['max']}"
            
            self.log.debug(f'Searching by series: "{normalized_series}" in range: {year_range_str}')
            self.enable_years_slider(True)
            response = await self.stamps_service.get_issues(
                year=year_range_str, 
                series_name=normalized_series, 
                api_key=API_MASTER_KEY
            )

        if self._is_valid_response(response):
            data = response.json().get('data', [])
            
            # Enrich data with metadata for editing
            for row in data:
                row['opts_print_types'] = self.print_types
                row['opts_stamp_types'] = self.stamp_types
                if row['market_value']:
                    row['market_value'] = f"{row['market_value']} €"
            
            self.all_issues = data
            self.table.rows[:] = data
        else:
            self.log.error(f'API error fetching issues: {response.status_code if response else "No response"}')
            self.notify(_(self.ERR_API), 'warning', timeout=0, close_button=_('close'))

    async def filter_issues(self, e=None) -> None:
        """Callback for filter UI changes."""
        await self.get_issues()

    async def load_initial_data(self) -> None:
        """
        Loads all necessary initial data sequentially.
        """
        await self.get_years()
        await self.get_print_types()
        await self.get_stamp_types()

    async def _fetch_metadata_list(self, service_method, storage_attr: str, log_name: str) -> None:
        """
        Generic helper to fetch a list of items from the service and store them.

        Args:
            service_method (Callable): The service method to call.
            storage_attr (str): The attribute name on self to store the resulting list.
            log_name (str): A descriptive name for logging/errors.
        """
        self.log.debug(f'Fetching {log_name}...')
        response = await service_method(api_key=API_MASTER_KEY)

        if self._is_valid_response(response):
            data = response.json().get('data', [])
            setattr(self, storage_attr, [item.get('name') for item in data])
        else:
            self.log.error(f'Failed to fetch {log_name}: {response.status_code if response else "No response"}')
            self.notify(_(self.ERR_API), 'warning', timeout=0, close_button=_('close'))

    async def get_print_types(self) -> None:
        """Fetches available print types."""
        await self._fetch_metadata_list(self.stamps_service.get_print_types, 'print_types', 'print types')

    async def get_stamp_types(self) -> None:
        """Fetches available stamp types."""
        await self._fetch_metadata_list(self.stamps_service.get_stamp_types, 'stamp_types', 'stamp types')
    
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

