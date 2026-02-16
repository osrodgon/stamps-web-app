from base.base_ui import BaseUI
from core.translations import _
from core.urls import URLs
from nicegui import app, ui
from settings import ORG_LOGO, USER_EMAIL, USER_FIRST_NAME, USER_LAST_NAME   


class TopBar(ui.header, BaseUI):
    """
    A UI component for the top navigation bar.

    This component inherits from `ui.header` and `BaseUI`. It features the page
    title, user information, and a right drawer that can be toggled. The drawer
    contains navigation links and user-specific actions like logging out.
    """
    extra_controls = None

    def __init__(self, name="Please assign a name to this page"):
        """
        Initializes the TopBar component.

        This method sets up the header, including the page title and user-specific
        elements like the user's full name, email, and the navigation drawer.

        Args:
            name (str): The title of the page to be displayed in the top bar.
                        Defaults to "Please assign a name to this page".
        """
        super().__init__()
        self.log.debug("Initializing TopBar...")
        self.title = name

        user_full_name = (
            app.storage.user.get(USER_FIRST_NAME, 'Unknown').capitalize() + ' ' + app.storage.user.get(USER_LAST_NAME, 'Unknown').capitalize()
        ).strip()
        user_email = app.storage.user.get(USER_EMAIL, 'Unknown')

        # The drawer that will be used as menu
        with ui.right_drawer(value=False, fixed=True).props('bordered').classes('bg-slate-50 p-0') as drawer:
            self.log.debug("Initializing drawer...")
            with ui.column().classes('w-full h-full p-0 gap-0 no-wrap'):
                # Content Area (Header + List)
                with ui.column().classes('w-full flex-grow p-0 gap-0'):
                    # User Header
                    with ui.element('div').classes('p-6 bg-white border-b w-full'):
                        with ui.row().classes('items-center gap-4'):
                            # Customizing the avatar color to match the blue in your image
                            ui.avatar('person', color='blue-500',
                                    text_color='white').props('size=48px')
                            with ui.column().classes('gap-0'):
                                ui.label(user_full_name).classes(
                                    'font-bold text-lg text-slate-800')
                                ui.label(user_email).classes(
                                    'text-sm text-blue-400')

                    # Navigation List
                    with ui.list().props('padding').classes('w-full'):
                        with ui.item(on_click=lambda: ui.notify('Profile')).props('clickable v-ripple'):
                            with ui.item_section().props('avatar'):
                                ui.icon('person', color='slate-600')
                            with ui.item_section():
                                ui.label(_('profile.profile'))

                        with ui.item(on_click=lambda: ui.notify('Settings')).props('clickable v-ripple'):
                            with ui.item_section().props('avatar'):
                                ui.icon('settings', color='slate-600')
                            with ui.item_section():
                                ui.label(_('profile.settings'))

                        ui.separator().classes('my-2')

                        with ui.item(on_click=lambda: self.confirm_logout()).props('clickable v-ripple').classes('text-red-500'):
                            with ui.item_section().props('avatar'):
                                ui.icon('logout', color='red')
                            with ui.item_section():
                                ui.label(_('auth.logout')).classes('font-bold')

                # Branding Image at the bottom right
                with ui.row().classes('w-full justify-end p-4'):
                    ui.image(ORG_LOGO).classes('w-16 opacity-90')

        # The top bar
        with self.classes('bg-slate-800 text-white items-center justify-between border-b border-slate-700 px-6 py-2 shadow-md'):
            # Left Side
            with ui.row().classes('items-center gap-10'):
                self.log.debug("Initializing left side...")
                ui.label(name).classes('text-xl font-bold tracking-tight text-white')
                self.extra_controls = ui.row()

            # Right Side
            self.log.debug("Initializing right side...")
            with ui.row().classes('items-center gap-3'):
                ui.label(user_full_name.upper()).classes(
                    'text-xs font-bold text-slate-200 tracking-widest')
                ui.button(on_click=drawer.toggle, icon='menu').props(
                    'flat round color=white').classes('hover:bg-slate-700')

    def confirm_logout(self):
        """
        Displays a confirmation dialog for logging out.

        This method opens a dialog box to confirm whether the user wants to
        proceed with logging out. If confirmed, the `logout` method is called.
        """
        self.log.debug("Displaying the logout confirmation dialog...")
        with ui.dialog() as dialog, ui.card().classes('w-auto p-6 rounded-lg'):
            ui.label(_('auth.logout_confirm')).classes('text-lg font-bold mb-2')
            ui.label(_('auth.logout_confirm_message')).classes('text-gray-600 mb-4')

            with ui.row().classes('w-full justify-end gap-2'):
                ui.button(_('ui.cancel'), on_click=dialog.close).props('flat')
                ui.button(_('auth.logout'), color='red',
                          on_click=self.logout).props('unelevated')

        dialog.open()

    def logout(self):
        """
        Logs the user out and redirects to the logout page.

        This method is called after the user confirms the logout action. It
        navigates the user to the application's designated logout URL.
        """
        self.log.debug("Performing the logout action...")
        ui.navigate.to(URLs.Frontend.logout)
