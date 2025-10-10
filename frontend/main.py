# main.py
from nicegui import ui
from app.stamp_collection_app import StampCollectionApp
from common.translation_manager import t, t_manager

# Create the main application controller
app = StampCollectionApp()

@ui.page('/')
def main_page():
    app.page = ui.column().classes('p-8 w-full')
    app.side_bar = ui.left_drawer(value=False).classes('bg-gray-100 p-4 w-56 shadow-lg')

    # Setup default language (spanish)
    ui.context.client.language = t_manager.current_language
    
    with ui.header().classes('items-center bg-primary text-white'):
        # Add header
        app.create_header_content() # Call the class method
    
    # Add content to the left drawer
    with app.side_bar:
        app.create_sidebar_content() # Call the class method
        
    # Main page.
    with app.page:
        ui.label(t('content_title')).classes('text-2xl')

if __name__ in {"__main__", "__mp_main__"}:
    ui.run()