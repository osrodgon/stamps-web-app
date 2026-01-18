from base.base_page import BasePage
from components.common.top_bar import TopBar
from core.translations import _
from nicegui import ui
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
    table = None
    stamps_service: StampsService = None
    columns = []
    print_types = []
    
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
        
        self.columns = [
            {'name': 'expand', 'label': _('details'), 'field': 'expand', 'align': 'center'},
            {'name': 'country', 'label': _('country'), 'field': 'country', 'align': 'left', 'width': '1px'},
            {'name': 'date', 'label': _('date'), 'field': 'date', 'align': 'left', 'sortable': True, 'width': '1px'},
            {'name': 'name', 'label': _('issue_name'), 'field': 'name', 'align': 'left', 'sortable': True, 'width': '1px'},
            {'name': 'perforation', 'label': _('perforation'), 'field': 'perforation', 'align': 'left', 'width': '1px'},
            {'name': 'stamp_type', 'label': _('stamp_type'), 'field': 'stamp_type', 'align': 'left','width': '1px'},
            {'name': 'print_type', 'label': _('print_type'), 'field': 'print_type', 'align': 'left','width': '1px'},
            {'name': 'total_printed', 'label': _('total_printed'), 'field': 'total_printed', 'align': 'left','width': '1px'},
            {'name': 'market_value', 'label': _('value'), 'field': 'market_value', 'align': 'left', 'width': '1px'},
            {'name': 'delete', 'label': _('actions'), 'field': 'delete', 'align': 'right', 'width': '100%'},
        ]
        
        ui.query('body').style('overflow: hidden; margin: 0; padding: 0;')
        ui.add_head_html('''
            <style>
                .sticky-header-table .q-table__top,
                .sticky-header-table .q-table__bottom,
                .sticky-header-table thead tr:first-child th {
                    /* bg-white is important so rows don't bleed through the header */
                    background-color: white;
                    position: sticky;
                    top: 0;
                    z-index: 2;
                }
            </style>
        ''')
        
        self.top_bar = TopBar(_('stamps_manager_title'))
        self.classes('w-full h-screen no-wrap p-0 m-0 overflow-hidden')
        
        with self.classes('fixed inset-0 flex flex-col no-wrap overflow-hidden bg-white'):
            with ui.column().classes('w-full flex-grow p-4 mt-[80px] overflow-hidden flex flex-col no-wrap'):
                with self.top_bar.extra_controls:
                    self.years_select = ui.select([], label=_("select_year"), on_change=lambda e: self.get_issues(e.value)).classes('w-48')

                self.table = ui.table(
                    columns=self.columns, 
                    rows=[], 
                    row_key='id'
                    ).props(
                        'fixed-height'
                    )
                self.table.classes('w-full flex-grow sticky-header-table')
                self.table.style('height: 100%; border: 1px solid #e5e7eb;')
                
                self.table.add_slot('body', f'''
                    <q-tr :props="props">
                        <q-td auto-width>
                            <q-btn size="sm" color="primary" round dense 
                                @click="props.expand = !props.expand" :icon="props.expand ? 'remove' : 'add'" />
                        </q-td>
                        
                        <q-td key="country" :props="props">{{{{ props.row.country }}}}</q-td>
                        
                        <q-td key="date" :props="props">
                            <div class="row items-center q-gutter-x-sm cursor-pointer">
                                <span>{{{{ props.row.date }}}}</span>
                                
                                <q-icon name="event" color="primary" size="xs">
                                    <q-menu transition-show="scale" transition-hide="scale">
                                        <q-date 
                                            v-model="props.row.date" 
                                            minimal 
                                            mask="YYYY-MM-DD"
                                            :first-day-of-week="1"
                                        >
                                        <div class="row items-center justify-end q-gutter-sm">
                                            <q-btn label="{_('today')}" color="secondary" flat 
                                                @click="props.row.date = new Date().toISOString().split('T')[0]" />
                                            
                                            <q-btn v-close-popup label="{_('ok')}" color="primary" flat 
                                                @click="$parent.$emit('save', {{id: props.row.id, key: 'date', value: props.row.date}})" />
                                            
                                        </div>
                                        </q-date>
                                    </q-menu>
                                </q-icon>
                            </div>
                        </q-td>
                                                                        
                        <q-td key="name" :props="props">
                            {{{{ props.row.name }}}}
                            <q-popup-edit v-model="props.row.name" v-slot="scope" buttons
                                @save="(val) => $parent.$emit('save', {{id: props.row.id, key: 'name', value: val}})">
                                <q-input v-model="scope.value" dense autofocus />
                            </q-popup-edit>
                        </q-td>
                        
                        <q-td key="perforation" :props="props">
                            {{{{ props.row.perforation }}}}
                            <q-popup-edit v-model="props.row.perforation" v-slot="scope" buttons
                                @save="(val) => $parent.$emit('save', {{id: props.row.id, key: 'perforation', value: val}})">
                                <q-input v-model="scope.value" dense autofocus />
                            </q-popup-edit>
                        </q-td>
                        
                        <q-td key="stamp_type" :props="props">
                            {{{{ props.row.stamp_type }}}}
                            <q-popup-edit v-model="props.row.stamp_type" v-slot="scope" buttons
                                @save="(val) => $parent.$emit('save', {{id: props.row.id, key: 'stamp_type', value: val}})">
                                <q-input v-model="scope.value" dense autofocus />
                            </q-popup-edit>
                        </q-td>
                        
                        <q-td key="print_type" :props="props">
                            {{{{ props.row.print_type }}}}
                            <q-popup-edit v-model="props.row.print_type" v-slot="scope" buttons
                                label-set="{_('ok')}" label-cancel="{_('close')}"
                                @save="(val) => $parent.$emit('save', {{id: props.row.id, key: 'print_type', value: val}})">
                                <q-select 
                                    v-model="scope.value"  
                                    :options="props.row.opts_print_types"
                                    dense 
                                    autofocus 
                                />
                            </q-popup-edit>
                        </q-td>
                        
                        <q-td key="total_printed" :props="props">{{{{ props.row.total_printed }}}}</q-td>
                        
                        <q-td key="market_value" :props="props">${{{{ props.row.market_value }}}}</q-td>
                        
                        <q-td key="delete" :props="props">
                            <q-btn size="sm" color="red" icon="delete" @click="$parent.$emit('delete', props.row.id)" />
                        </q-td>
                    </q-tr>

                    <q-tr v-show="props.expand" :props="props">
                        <q-td colspan="4">
                            <div class="p-4 bg-blue-50 border rounded grid grid-cols-1 gap-4">
                                <div class="cursor-pointer">
                                    <strong>{_('description')}:</strong> {{{{ props.row.description }}}}
                                    <q-popup-edit v-model="props.row.description" v-slot="scope" buttons
                                        @save="(val) => $parent.$emit('save', {{id: props.row.id, key: 'description', value: val}})">
                                        <q-input type="textarea" v-model="scope.value" dense autofocus label="Edit Description" />
                                    </q-popup-edit>
                                </div>
                                
                                <div class="cursor-pointer">
                                    <strong>{_('notes')}:</strong> {{{{ props.row.note }}}}
                                    <q-popup-edit v-model="props.row.note" v-slot="scope" buttons
                                        @save="(val) => $parent.$emit('save', {{id: props.row.id, key: 'notes', value: val}})">
                                        <q-input type="textarea" v-model="scope.value" dense autofocus label="Edit Notes" />
                                    </q-popup-edit>
                                </div>

                            </div>
                        </q-td>
                    </q-tr>
                ''')
                
                self.table.on('save', lambda e: self.notify(e.args, timeout=0, close_button=_('close')))
                self.table.on('delete', lambda e: self.notify(e.args))
            
        ui.timer(0, self.get_years, once=True)
        ui.timer(0, self.get_print_types, once=True)
    
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
            
            self.table.rows[:] = data
        else:
            self.log.error(_('api_error', _language='en'))
            self.notify(_('api_error'), 'warning', timeout=0, close_button=_('close'))
        
    async def get_print_types(self):
        self.log.debug('Getting print types...')
        
        response = await self.stamps_service.get_print_types(api_key=API_MASTER_KEY)
        
        if self._is_valid_response(response):
            data = response.json()['data']
            list = []
            
            for print_type in data:
                list.append(print_type['name'])
                
            self.print_types = list
        else:
            self.log.error(_('api_error', _language='en'))
            self.notify(_('api_error'), 'warning', timeout=0, close_button=_('close'))
