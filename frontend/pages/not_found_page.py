from nicegui import ui

from base.base_page import BasePage

class NotFoundPage(ui.column, BasePage):
    PAGE_TITLE = "404 - Lost in the UI" 
    NICEGUI_COLOR = '#1976D2'
    
    def __init__(self):
        super().__init__()
        
        ui.page_title = self.PAGE_TITLE
        with ui.column().classes('absolute-center items-center'):
            ui.label('404') \
                .classes('text-[150px] font-extrabold') \
                .style(f'color: {self.NICEGUI_COLOR}; line-height: 1.0;')

            ui.label('Oops! You seem to be lost.') \
                .classes('text-2xl font-semibold mt-[-20px] mb-4')
            
            ui.markdown('The page you are looking for is **not found** on this server.') \
                .classes('text-lg text-gray-600 mb-8')

            ui.button('Take Me Home', 
                    on_click=lambda: ui.navigate.to('/'),
                    icon='home') \
                    .props('size=md color=primary')
            
            ui.label('Stamps App') \
                .classes('text-sm text-gray-400 mt-10')
