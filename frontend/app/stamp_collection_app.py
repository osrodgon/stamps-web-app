from nicegui import ui
from nicegui.elements.drawer import Drawer
from common.translation_manager import t, t_manager # Import the manager

class StampCollectionApp:
    def __init__(self):
        # References to the refreshable UI parts, stored as attributes
        # self.sidebar_content_ref = None
        # self.header_content_ref = None
        self.__side_bar: Drawer = None
        self.__page = None
        
    @property
    def side_bar(self):
        return self.__side_bar
    
    @side_bar.setter
    def side_bar(self, side_bar):
        self.__side_bar = side_bar
        
    @property
    def page(self):
        return self.__page
    
    @page.setter
    def page(self, page):
        self.__page = page
        
    # Creates an entry in the left drawer
    def __create_sidebar_menu_item(self, text_key: str, icon_name: str, action_handler: callable):
        """Creates a standardized sidebar menu item with icon and click handler."""
        TIGHT_CLASSES = 'w-full py-2 my-0 min-h-0 uppercase hover:bg-sky-100'

        with ui.menu_item(on_click=action_handler).classes(TIGHT_CLASSES):
            with ui.row().classes('items-center gap-2'):
                ui.icon(icon_name).classes('text-xl')
                ui.label(t(text_key))
        
    # Creates header
    @ui.refreshable
    def create_header_content(self):
        """Draws the internal content of the header."""
        ui.button(on_click=self.__side_bar.toggle, icon='menu').props('flat color=white')
        ui.label(t('app_title')).classes('ml-4 text-xl')
        ui.space()

    # Creates sidebar (left drawer)
    @ui.refreshable
    def create_sidebar_content(self):
        """Draws the internal content of the sidebar drawer."""
        TIGHT_CLASSES = 'w-full py-2 my-0 min-h-0 uppercase hover:bg-sky-100'
        
        ui.label(t('menu_title')).classes('text-lg font-bold mb-4 text-gray-700')
        ui.separator()
        # ui.menu_item(t('view_database'), on_click=self.left_drawer_ref.toggle).classes(TIGHT_CLASSES)
        self.__create_sidebar_menu_item('view_collection', 'collections', self.menu_collections_clicked)
        self.__create_sidebar_menu_item('edit_mode', 'edit', self.menu_edit_clicked)
        self.__create_sidebar_menu_item('settings', 'settings', self.menu_settings_clicked)
        
    def menu_collections_clicked(self):
        self.__side_bar.set_value(False)
        with self.__page:
            ui.label("Collection")

    def menu_edit_clicked(self):
        self.__side_bar.set_value(False)
        with self.__page:
            ui.label("Edit")

    def menu_settings_clicked(self):
        self.__side_bar.set_value(False)
        with self.__page:
            ui.label("Settings")