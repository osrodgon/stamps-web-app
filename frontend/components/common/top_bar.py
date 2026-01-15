from nicegui import ui

from base.base_ui import BaseUI
from core.translations import _

class TopBar(ui.header, BaseUI):
    def __init__(self, name="Please assign a name to this page"):
        super().__init__()
        self.log.debug("Initializing TopBar...")
        
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
                            ui.label('John Doe').classes('font-bold text-lg text-slate-800')
                            ui.label('john.doe@example.com').classes('text-sm text-blue-400')
                
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

                    with ui.item(on_click=lambda: ui.notify('Logout')).props('clickable v-ripple').classes('text-red-500'):
                        with ui.item_section().props('avatar'):
                            ui.icon('logout', color='red')
                        with ui.item_section():
                            ui.label(_('logout')).classes('font-bold')

        # The top bar
        with self.classes('bg-white text-black items-center justify-between border-b px-6 py-2 shadow-none'):
            # Left Side
            ui.label(name).classes('text-xl font-bold tracking-tight')
            
            # Right Side
            with ui.row().classes('items-center gap-3'):
                ui.label('JOHN DOE').classes('text-xs font-bold text-slate-900 tracking-widest')
                ui.button(on_click=drawer.toggle, icon='menu').props('flat round color=black').classes('hover:bg-slate-100')
