class TranslationManager:
    TRANSLATIONS = {
    'es': {
        'app_title': 'Colección de Sellos',
        'menu_title': 'Menú de Sellos',
        'view_collection': 'Ver Colección',
        'view_database': 'Ver Base de Datos',
        'edit_mode': 'Modo Edición',
        'settings': 'Configuración',
        'language_selector_label': 'Idioma',
        'content_title': 'Contenido de la Colección de Sellos aquí.',
        'language_notif': 'Idioma cambiado a Español'
        },
    'en': {
        'app_title': 'Stamp Collection',
        'menu_title': 'Stamp Menu',
        'view_collection': 'View Collection',
        'view_database': 'View Database',
        'edit_mode': 'Edit Mode',
        'settings': 'Settings',
        'language_selector_label': 'Language',
        'content_title': 'Stamp Collection Content Here.',
        'language_notif': 'Language changed to English'
        }
    }

    def __init__(self, initial_lang: str = 'es'):
        self.current_language = initial_lang

    def t(self, key: str) -> str:
        """Simple translation function."""
        return self.TRANSLATIONS.get(self.current_language, {}).get(key, key)

# Create a singleton instance to be imported by others
# This makes it easy to share the same manager across files
t_manager = TranslationManager()
t = t_manager.t # Shorthand function for easy use