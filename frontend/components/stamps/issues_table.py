from core.translations import _
from nicegui import ui
from settings import BACKEND_SERVER_URL, NO_STAMP, IMAGE_DIR

class IssuesTable(ui.table):
    """
    A specialized table component for the stamp issues database.

    Provides a rich interface for managing stamp issues, including:
    - **Interactive Data Display**: Custom column rendering for complex types.
    - **Inline Editing**: Popup-based editing for dates, text, and select fields.
    - **Expandable Rows**: Detailed view for long descriptions, notes, and a stamp gallery.
    - **Lazy Loading Integration**: Emits an 'expand' event to trigger data fetching for stamps.
    - **CRUD Actions**: Integrated save and delete triggers.
    - **Styled Layout**: Custom CSS for zebra striping, sticky headers, and hover effects.
    """
    def __init__(self, on_save, on_delete):
        """
        Initializes the IssuesTable.

        Sets up the table columns, styles, and event listeners for save and delete actions.

        Args:
            on_save (callable): A callback function to be invoked when a cell edit is saved.
                                It receives the event arguments containing the edited data.
            on_delete (callable):   A callback function to be invoked when a delete action is triggered.
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
        Generates the Vue HTML template for the table's body slots.

        This template handles:
        - Recursive expansion for the details row, including a visual stamp gallery.
        - `q-popup-edit` components for all editable fields.
        - Custom form controls (date pickers, options selects).
        - Event emission (`save`, `delete`, and `expand`) to the parent component.
        - Dynamic rendering of stamp cards with lazy-loading support (spinner/data view).
        - Responsive layout for notes and descriptions using Tailwind classes.

        Returns:
            str: A raw string containing the Vue template defined in Quasar/NiceGUI style.
        """
        return f'''
            <q-tr :props="props">
                <q-td auto-width>
                    <q-btn size="sm" color="primary" round dense 
                        @click="props.expand = !props.expand; if(props.expand) $parent.$emit('expand', props.row)" 
                        :icon="props.expand ? 'keyboard_arrow_up' : 'keyboard_arrow_down'" />
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
                        label-set="{_('ok')}" label-cancel="{_('close')}"
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
                    <div class="p-6 bg-slate-50">
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">
                            
                            <!-- Description Section -->
                            <div class="cursor-pointer group relative p-4 bg-white rounded-lg shadow-sm hover:shadow-md transition-shadow duration-200 border border-slate-100">
                                <div class="flex items-center gap-2 mb-2 text-primary font-bold uppercase text-xs tracking-wider">
                                    <q-icon name="description" size="xs" />
                                    {_('description')}
                                    <q-icon name="edit" size="xs" class="opacity-0 group-hover:opacity-100 transition-opacity ml-auto text-slate-400" />
                                </div>
                                <div class="text-slate-700 leading-relaxed min-h-[3rem] whitespace-pre-line text-sm">
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
                                <div class="text-slate-700 leading-relaxed min-h-[3rem] whitespace-pre-line text-sm">
                                    {{{{ props.row.note || '{_('no_notes')}' }}}}
                                </div>
                                <q-popup-edit v-model="props.row.note" v-slot="scope" buttons
                                    @save="(val) => $parent.$emit('save', {{id: props.row.id, key: 'notes', value: val}})">
                                    <q-input type="textarea" v-model="scope.value" dense autofocus label="{_('notes')}" outlined class="min-w-[300px]" />
                                </q-popup-edit>
                            </div>
                        </div>

                        <!-- Stamps Section -->
                        <div class="p-4 bg-white rounded-lg border border-slate-100 shadow-sm">
                            <div class="flex items-center gap-2 mb-6 text-slate-800 font-bold uppercase text-sm tracking-[0.1em] border-b border-slate-100 pb-2">
                                <q-icon name="collections" size="sm" class="text-primary" />
                                {_('stamps')}
                            </div>
                            
                            <div v-if="!props.row.stamps" class="flex flex-col items-center justify-center p-8 text-slate-400">
                                <q-spinner-dots color="primary" size="40px" />
                                <div class="mt-2 text-xs">{_('loading_stamps')}</div>
                            </div>
                            
                            <div v-else-if="props.row.stamps.length === 0" class="p-8 text-center text-slate-400 text-sm italic">
                                {_('no_stamps_found')}
                            </div>
                            
                            <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                                <div v-for="stamp in props.row.stamps" :key="stamp.id" 
                                    class="flex flex-col border border-slate-100 rounded-lg overflow-hidden hover:border-primary/40 transition-all duration-300 bg-white shadow-sm hover:shadow-md">
                                    <div class="aspect-square bg-slate-50 flex items-center justify-center p-4 relative group">
                                        <q-img :src="stamp.image ? '{IMAGE_DIR}' + (stamp.image.indexOf('stamps/') === 0 ? stamp.image.substring(7) : (stamp.image.indexOf('/stamps/') === 0 ? stamp.image.substring(8) : (stamp.image.indexOf('/') === 0 ? stamp.image : '/' + stamp.image))) : '{NO_STAMP}'" 
                                            class="h-48 w-full rounded shadow-sm" 
                                            style="background-color: #505050;"
                                            fit="contain">
                                            <template v-slot:error>
                                                <q-img src="{NO_STAMP}" class="h-48 w-full" fit="contain" />
                                            </template>
                                        </q-img>
                                        <div class="absolute top-2 right-2 bg-slate-800/90 text-white text-xs px-2 py-1 rounded font-bold font-mono shadow-sm">
                                            {{{{ stamp.edifil_code }}}}
                                        </div>
                                    </div>
                                    <div class="p-4 flex flex-col gap-2">
                                        <div class="text-sm font-bold text-slate-900 leading-snug line-clamp-2 min-h-[2.5rem]">{{{{ stamp.name }}}}</div>
                                        <div class="flex items-center justify-between border-t border-slate-50 pt-2">
                                            <span class="text-xs text-slate-600 font-medium uppercase tracking-tight">{{{{ stamp.face_value }}}}</span>
                                            <span v-if="stamp.market_value" class="text-sm font-mono text-primary font-black">${{{{ stamp.market_value }}}}</span>
                                        </div>
                                        <div v-if="stamp.colors && stamp.colors.length" class="mt-1 flex flex-wrap gap-1.5">
                                            <span v-for="color in stamp.colors" :key="color" class="bg-slate-100 text-slate-700 text-[10px] px-2 py-0.5 rounded-full border border-slate-200">
                                                {{{{ color }}}}
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </q-td>
            </q-tr>
        '''
