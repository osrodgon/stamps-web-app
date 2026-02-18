from base.base_ui import BaseUI
from core.translations import _
from nicegui import app, ui
from settings import USER_LANGUAGE
from core.numbers import Numbers


class AISeriesLookupDrawer(ui.right_drawer, BaseUI):
    """
    A right drawer component for AI-powered stamp series lookup.
    
    Provides input fields for series name and date, extracts information
    using AI, and displays results.
    """
    SLATE_50 = '#f8fafc'
    GRAY_400 = '#bdbdbd'
    GRAY_900 = '#212121'
    
    def __init__(self, on_extract: callable = None, on_save: callable = None):
        """
        Initializes the AI Series Lookup drawer.
        
        Args:
            on_extract (callable):  Callback when user clicks extract button.
                                    Receives (name, date) tuple.
            on_save (callable): Callback when user clicks save button.
                                Receives extracted data dict.
        """
        super().__init__(value=False)
        self.classes('bg-slate-50')
        self.props('bordered width=600')
        
        # Store callbacks
        self._on_extract = on_extract
        self._on_save = on_save
        
        # UI Components (public)
        self.name_input = None
        self.date_input = None
        self.result_container = None
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Sets up the drawer UI."""
        with self.classes('w-full gap-4 p-4'):
            ui.label(_('ai_series_lookup.title')).classes('text-h6 font-bold')
            
            # Input fields
            with ui.row().classes('w-full gap-4'):
                self.name_input = ui.input(
                    label=_('ai_series_lookup.name_label'),
                    placeholder=_('ai_series_lookup.name_placeholder')
                ).classes('w-full')
                
                self.date_input = ui.input(
                    label=_('ai_series_lookup.date_label'),
                    placeholder=_('ai_series_lookup.date_placeholder')
                ).classes('w-full')
            
            # Extract button
            with ui.row().classes('w-full justify-end gap-2'):
                ui.button(
                    _('ai_series_lookup.extract_button'),
                    on_click=lambda: self._handle_extract()  # Wrap to avoid async callback warning
                ).props('color=teal')
            
            # Results container
            self.result_container = ui.column().classes('w-auto gap-2')
            
        ui.add_head_html(f'''
            <style>
                /* Avoid blue background in autofill */
                input:-webkit-autofill,
                input:-webkit-autofill:hover, 
                input:-webkit-autofill:focus, 
                input:-webkit-autofill:active  {{
                    -webkit-box-shadow: 0 0 0 30px { self.SLATE_50 } inset !important;
                    box-shadow: 0 0 0 30px { self.SLATE_50} inset !important;
                    border-bottom: 1px solid { self.GRAY_400 } !important;
                    border-radius: 0px !important;
                }}
                input:-webkit-autofill:hover {{
                    border-bottom: 1px solid { self.GRAY_900 } !important; /* Darker gray for hover*/
                }}
            </style>
        ''')
    
    async def _handle_extract(self):
        """Handles extract button click - calls parent's callback."""
        name = (self.name_input.value or "").strip()
        date = (self.date_input.value or "").strip()
        
        if not name or not date:
            self.notify(_('ai_series_lookup.error_empty_fields'), 'warning')
            return
        
        if self._on_extract:
            await self._on_extract(name, date)
    
    def show_loading(self):
        """Shows loading state in the results container."""
        self.result_container.clear()
        self.result_container.classes('w-full justify-center items-center')
        
        with self.result_container:
            ui.spinner(size='sm').props('color=teal')
            ui.label(_('ai_series_lookup.loading'))
    
    def display_results(self, data: dict):
        """
        Displays extracted results in the container.
        
        Args:
            data: The AI response data dictionary
        """
        self.result_container.clear()
        
        with self.result_container:
            # Get user language
            lang = app.storage.user.get(USER_LANGUAGE, 'en')

            # Header
            ui.label(data.get('issue_name', 'N/A')).classes('text-h6 w-full font-bold')
            
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
                ui.label(_('ai_series_lookup.field_description')).classes('text-subtitle2 w-full font-bold mt-2')
                ui.label(data.get('description')).classes('text-body2 text-justify')
                
            # Notes
            if data.get('notes'):
                ui.label(_('ai_series_lookup.field_notes')).classes('text-subtitle2 w-full font-bold mt-2')
                ui.label(data.get('notes')).classes('text-body2 text-justify')
            
            # Stamps list
            stamps = data.get('stamps', [])
            if stamps:
                ui.label(_('ai_series_lookup.stamps_title')).classes('text-subtitle2 w-full font-bold mt-4')
                for stamp in stamps:
                    with ui.card().classes('w-full pa-2 mb-2'):
                        ui.label(stamp.get('motive', 'N/A')).classes('font-bold')
                        
                        if stamp.get('description'):
                            ui.label(stamp.get('description')).classes('text-body2 text-justify')
                            
                        with ui.grid().classes('w-full grid-cols-2 gap-2 text-sm'):
                            self._add_result_field(_('ai_series_lookup.field_edifil_code'), stamp.get('edifil_code', 'N/A'))
                            self._add_result_field(_('ai_series_lookup.field_fesofi_code'), stamp.get('fesofi_code', 'N/A'))
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
                    on_click=lambda: self._handle_save(data) if self._on_save else None
                ).props('color=teal')
    
    async def _handle_save(self, data: dict):
        """Handles save button click - calls parent's callback."""
        if self._on_save:
            self._on_save(data)
    
    def display_error(self, message: str):
        """
        Displays an error message in the results container.
        
        Args:
            message: The error message to display
        """
        self.result_container.clear()
        
        with self.result_container:
            with ui.row().classes('w-full items-center gap-2 text-negative'):
                ui.icon('error', size='lg')
                ui.label(message).classes('font-bold')
            
            ui.label(_('ai_series_lookup.error_help')).classes('text-caption text-grey-7 mt-2')
    
    def _add_result_field(self, label: str, value) -> None:
        """Helper to display a label-value pair in results."""
        ui.label(f"{label}:").classes('font-bold')
        ui.label(str(value) if value else 'N/A')
