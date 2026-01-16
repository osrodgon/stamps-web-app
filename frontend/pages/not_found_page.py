from nicegui import ui

from base.base_page import BasePage
from core.translations import _
from core.urls import URLs

class NotFoundPage(ui.column, BasePage):
    """
    A '404 Not Found' page for the application.

    This class creates a visually centered and informative page that is displayed
    when a user navigates to a URL that does not exist. It includes a clear
    404 message and a button to return to the application's home page.
    """
    PAGE_TITLE = "404 - Lost in the UI" 
    NICEGUI_COLOR = '#1976D2'
    
    def __init__(self):
        """
        Initializes the NotFoundPage.

        This constructor builds the user interface for the 404 error page,
        setting the page title and arranging the '404' error message, a
        descriptive text, and a navigation button to go back to the home page.
        """
        super().__init__()
        
        ui.page_title = self.PAGE_TITLE
        with ui.column().classes('absolute-center items-center'):
            ui.label('404') \
                .classes('text-[150px] font-extrabold') \
                .style(f'color: {self.NICEGUI_COLOR}; line-height: 1.0;')

            ui.label(_('you_are_lost')) \
                .classes('text-2xl font-semibold mt-[-20px] mb-4')
            
            ui.markdown(_('page_not_found')) \
                .classes('text-lg text-gray-600 mb-8')

            ui.button(_('take_me_home'), 
                    on_click=lambda: ui.navigate.to(URLs.Frontend.root),
                    icon='home') \
                    .props('size=md color=primary')
            
            ui.label('Stamps App') \
                .classes('text-sm text-gray-400 mt-10')
