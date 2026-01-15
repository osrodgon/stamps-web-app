from nicegui import ui, app

from base.base_ui import BaseUI
from components.auth.login_card import LoginCard
from core.translations import _
from core.urls import URLs

class TopBar(ui.header, BaseUI):
    """
    A UI component representing the top navigation bar of the application.

    Inherits from `ui.header` and `BaseUI`. It displays the page title,
    user information, and a toggleable right drawer for navigation and user actions.
    """
    def __init__(self, name="Please assign a name to this page"):
        """
        Initializes the TopBar component.

        Args:
            name (str): The name/title of the current page to be displayed in the top bar.
        """
        super().__init__()
        self.log.debug("Initializing TopBar...")
        
        user_full_name = app.storage.user['first_name'].capitalize() + ' ' + app.storage.user['last_name'].capitalize()
        user_email = app.storage.user['email']
                
        # The drawer that will be used as menu
        with ui.right_drawer(value=False, fixed=True).props('bordered').classes('bg-slate-50 p-0') as drawer:
            self.log.debug("Initializing drawer...")
            with ui.column().classes('w-full p-0 gap-0'):
                
                # User Header
                with ui.element('div').classes('p-6 bg-white border-b w-full'):
                    with ui.row().classes('items-center gap-4'):
                        # Customizing the avatar color to match the blue in your image
                        ui.avatar('person', color='blue-500', text_color='white').props('size=48px')
                        with ui.column().classes('gap-0'):
                            ui.label(user_full_name).classes('font-bold text-lg text-slate-800')
                            ui.label(user_email).classes('text-sm text-blue-400')
                
                # Navigation List
                with ui.list().props('padding').classes('w-full'):
                    with ui.item(on_click=lambda: ui.notify('Profile')).props('clickable v-ripple'):
                        with ui.item_section().props('avatar'):
                            ui.icon('person', color='slate-600')
                        with ui.item_section():
                            ui.label(_('profile'))

                    with ui.item(on_click=lambda: ui.notify('Settings')).props('clickable v-ripple'):
                        with ui.item_section().props('avatar'):
                            ui.icon('settings', color='slate-600')
                        with ui.item_section():
                            ui.label(_('settings'))

                    ui.separator().classes('my-2')

                    with ui.item(on_click=lambda: self.confirm_logout()).props('clickable v-ripple').classes('text-red-500'):
                        with ui.item_section().props('avatar'):
                            ui.icon('logout', color='red')
                        with ui.item_section():
                            ui.label(_('logout')).classes('font-bold')

        # The top bar
        with self.classes('bg-white text-black items-center justify-between border-b px-6 py-2 shadow-none'):
            # Left Side
            self.log.debug("Initializing left side...")
            ui.label(name).classes('text-xl font-bold tracking-tight')
            
            # Right Side
            self.log.debug("Initializing right side...")
            with ui.row().classes('items-center gap-3'):
                ui.label(user_full_name.upper()).classes('text-xs font-bold text-slate-900 tracking-widest')
                ui.button(on_click=drawer.toggle, icon='menu').props('flat round color=black').classes('hover:bg-slate-100')
                
    def confirm_logout(self):
        """
        Opens a confirmation dialog for the logout action.

        Displays a dialog asking the user to confirm if they want to log out.
        """
        self.log.debug("Displaying the logout confirmation dialog...")
        with ui.dialog() as dialog, ui.card().classes('w-auto p-6'):
            ui.label(_('logout_confirm')).classes('text-lg font-bold mb-2')
            ui.label(_('logout_confirm_message')).classes('text-gray-600 mb-4')
            
            with ui.row().classes('w-full justify-end gap-2'):
                ui.button(_('cancel'), on_click=dialog.close).props('flat')
                ui.button(_('logout'), color='red', on_click=self.logout).props('unelevated')
                
        dialog.open()
        
    def logout(self):
        """
        Performs the logout action.

        Navigates the user to the logout URL.
        """
        self.log.debug("Performing the logout action...")
        ui.navigate.to(URLs.Frontend.logout)
        
    
