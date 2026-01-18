from core.translations import _
from nicegui import ui

class IssuesTable(ui.table):
    """
    A specific table component for displaying and managing stamp issues.
    
    This component renders a table of stamp issues with functionalities for 
    viewing details, editing fields inline, and deleting records. It defines 
    specific columns and custom templates for the table body to handle complex 
    types and interactions.
    """
    def __init__(self, on_save, on_delete):
        """
        Initializes the IssuesTable.

        Sets up the table columns, styles, and event listeners for save and delete actions.

        Args:
            on_save (callable): A callback function to be invoked when a cell edit is saved.
                                It receives the event arguments containing the edited data.
            on_delete (callable): A callback function to be invoked when a delete action is triggered.
                                  It receives the event arguments containing the ID of the item to delete.
        """
        columns = [
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
        
        super().__init__(columns=columns, rows=[], row_key='id')
        
        # Custom CSS for the table
        ui.add_head_html('''
            <style>
                .issues-table thead tr:first-child th {
                    background-color: #1e293b !important; /* Slate 800 */
                    color: white;
                    font-weight: bold;
                    text-transform: uppercase;
                    letter-spacing: 0.05em;
                    position: sticky;
                    top: 0;
                    z-index: 1;
                }
                /* Zebra striping: Target every second item.
                   Each item has 2 rows (Main + Expand).
                   Item 1: rows 1, 2
                   Item 2: rows 3, 4  <- Target these
                   Item 3: rows 5, 6
                   Item 4: rows 7, 8  <- Target these
                   Formula: 4n+3, 4n+4
                */
                .issues-table tbody tr:nth-child(4n+3),
                .issues-table tbody tr:nth-child(4n+4) {
                    background-color: #f8fafc; /* Slate 50 */
                }
                .issues-table tbody tr:hover {
                    background-color: #e2e8f0; /* Slate 200 */
                }
            </style>
        ''')
        
        self.classes('issues-table w-full flex-grow')
        self.style('height: 100%;')
        self.props('flat bordered square')
        
        self.add_slot('body', self._get_body_template())
        
        self.on('save', on_save)
        self.on('delete', on_delete)

    def _get_body_template(self):
        """
        Generates the HTML template for the table body slots.

        This template defines how rows are rendered, including:
        - Expand/collapse buttons for detailed views.
        - Inline editing popups for various fields (date, name, perforation, etc.).
        - Custom form controls like date pickers and selects.
        - Delete buttons.
        - Expanded detailed view showing descriptions and notes.

        Returns:
            str: The raw HTML string for the body slot.
        """
        return f'''
            <q-tr :props="props">
                <q-td auto-width>
                    <q-btn size="sm" color="primary" round dense 
                        @click="props.expand = !props.expand" :icon="props.expand ? 'keyboard_arrow_down' : 'keyboard_arrow_right'" />
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
                        label-set="{_('ok')}" label-cancel="{_('close')}"
                        @save="(val) => $parent.$emit('save', {{id: props.row.id, key: 'stamp_type', value: val}})">
                        <q-select 
                            v-model="scope.value"  
                            :options="props.row.opts_stamp_types"
                            dense 
                            autofocus 
                        />
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
                
                <q-td key="total_printed" :props="props">
                    {{{{ props.row.total_printed }}}}
                    <q-popup-edit v-model="props.row.total_printed" v-slot="scope" buttons
                        label-set="{'ok'}" label-cancel="{'close'}"
                        @save="(val) => $parent.$emit('save', {{id: props.row.id, key: 'total_printed', value: val}})">
                        <q-input v-model="scope.value" dense autofocus />
                    </q-popup-edit>
                </q-td>
                
                <q-td key="market_value" :props="props">
                    ${{{{ props.row.market_value }}}}
                    <q-popup-edit v-model="props.row.market_value" v-slot="scope" buttons
                        label-set="{'ok'}" label-cancel="{'close'}"
                        @save="(val) => $parent.$emit('save', {{id: props.row.id, key: 'market_value', value: val}})">
                        <q-input v-model="scope.value" dense autofocus />
                    </q-popup-edit>
                </q-td>
                
                <q-td key="delete" :props="props">
                    <q-btn size="sm" color="red" icon="delete" @click="$parent.$emit('delete', props.row.id)" />
                </q-td>
            </q-tr>

            <q-tr v-show="props.expand" :props="props">
                <q-td colspan="100%">
                    <div class="p-6 grid grid-cols-1 md:grid-cols-2 gap-8">
                        
                        <!-- Description Section -->
                        <div class="cursor-pointer group relative p-4 bg-white rounded-lg shadow-sm hover:shadow-md transition-shadow duration-200 border border-slate-100">
                            <div class="flex items-center gap-2 mb-2 text-primary font-bold uppercase text-xs tracking-wider">
                                <q-icon name="description" size="xs" />
                                {_('description')}
                                <q-icon name="edit" size="xs" class="opacity-0 group-hover:opacity-100 transition-opacity ml-auto text-slate-400" />
                            </div>
                            <div class="text-slate-700 leading-relaxed min-h-[3rem] whitespace-pre-line">
                                {{{{ props.row.description || '{_('no_description')}' }}}}
                            </div>
                            <q-popup-edit v-model="props.row.description" v-slot="scope" buttons
                                @save="(val) => $parent.$emit('save', {{id: props.row.id, key: 'description', value: val}})">
                                <q-input type="textarea" v-model="scope.value" dense autofocus label="{_('description')}" outlined class="min-w-[300px]" />
                            </q-popup-edit>
                        </div>
                        
                        <!-- Notes Section -->
                        <div class="cursor-pointer group relative p-4 bg-white rounded-lg shadow-sm hover:shadow-md transition-shadow duration-200 border border-slate-100">
                            <div class="flex items-center gap-2 mb-2 text-secondary font-bold uppercase text-xs tracking-wider">
                                <q-icon name="note" size="xs" />
                                {_('notes')}
                                <q-icon name="edit" size="xs" class="opacity-0 group-hover:opacity-100 transition-opacity ml-auto text-slate-400" />
                            </div>
                            <div class="text-slate-700 leading-relaxed min-h-[3rem] whitespace-pre-line">
                                {{{{ props.row.note || '{_('no_notes')}' }}}}
                            </div>
                            <q-popup-edit v-model="props.row.note" v-slot="scope" buttons
                                @save="(val) => $parent.$emit('save', {{id: props.row.id, key: 'notes', value: val}})">
                                <q-input type="textarea" v-model="scope.value" dense autofocus label="{_('notes')}" outlined class="min-w-[300px]" />
                            </q-popup-edit>
                        </div>

                    </div>
                </q-td>
            </q-tr>
        '''
