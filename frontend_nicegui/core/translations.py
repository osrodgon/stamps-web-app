import json
from pathlib import Path

from nicegui import ui, app

from settings import USER_LANGUAGE, DEFAULT_LANGUAGE


def _(text: str, **kwargs):
    """
    Translates a given text key utilizing the application's translation service,
    allowing for optional variable interpolation.

    Usage: _('welcome_message', name='User')

    Args:
        text (str): The key for the text to be translated.
        **kwargs:   Optional arguments for dynamic string formatting.
                    To Temporarily override the language, pass '_language' kwarg.
                    e.g. _('welcome_message', name='User', _language='es')

    Returns:
        str: The translated and formatted string.
    """
    language = kwargs.pop('_language', None)
    return Translations.translate(text, language=language, **kwargs)

async def get_browser_language() -> str:
    """
    Retrieves the browser's language setting using JavaScript.

    Returns:
        str: The detected browser language code (e.g., 'en', 'es').
    """
    lang = str(await ui.run_javascript('navigator.language || navigator.userLanguage;')).split('-')[0]
    return lang
class Translations:
    """
    Manages and provides translations for the application.

    This class holds a dictionary of translations for various languages and
    provides a static method to translate keys based on the user's selected
    language, which is stored in the application's user storage.

    Attributes:
        translations (dict):    A nested dictionary where the outer keys are
                                language codes (e.g., 'en', 'es') and the inner
                                dictionaries map translation keys to strings.
    """
    DEFAULT_LANGUAGE = 'en'
    translations = {}

    @staticmethod
    def load_translations():
        """
        Loads translations from JSON files in the 'frontend/assets/locales' directory.
        
        This method scans the 'locales' folder for .json files (e.g., 'en.json', 'es.json'),
        loads their content, and populates the `translations` dictionary using the
        filename (without extension) as the language code.
        """
        try:
            # Resolve path relative to this file: ../assets/locales
            base_dir = Path(__file__).parent.parent
            locales_dir = base_dir / 'assets' / 'locales'
            
            if not locales_dir.exists():
                print(f"Warning: Locales directory not found at {locales_dir}")
                return

            for file_path in locales_dir.glob('*.json'):
                language_code = file_path.stem
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        Translations.translations[language_code] = json.load(f)
                except Exception as e:
                    print(f"Error loading translation file {file_path}: {e}")
                    
        except Exception as e:
            print(f"Error initializing translations: {e}")
    
    @staticmethod
    def _get_nested_value(lang_dict: dict, key: str):
        """
        Retrieves a value from a dictionary, supporting dot notation for nested keys.

        Args:
            lang_dict (dict): The language dictionary to search in.
            key (str): The key, potentially with dot notation (e.g., 'auth.sign_in').

        Returns:
            The value if found, or None if not found.
        """
        if '.' in key:
            parts = key.split('.')
            value = lang_dict
            for part in parts:
                if isinstance(value, dict):
                    value = value.get(part)
                else:
                    return None
            return value
        return lang_dict.get(key)

    @staticmethod
    def translate(key: str, language: str = None,**kwargs) -> str:
        """
        Translates a key into the user's language with support for fallback and interpolation.

        1. Determines the user's language safely (handling non-request contexts).
        2. Looks up the key in the selected language (supports dot notation for nested keys).
        3. Falls back to default language ('en') if key is missing.
        4. Applies string formatting if kwargs are provided.

        Args:
            key (str): The translation key, optionally with dot notation (e.g., 'auth.sign_in').
            **kwargs: Variables for string interpolation.

        Returns:
            str: The translated (and formatted) string, or the key if not found.
        """
        # 1. Determine Language safely
        if not language:
            try:
                current_language = app.storage.user.get(USER_LANGUAGE, Translations.DEFAULT_LANGUAGE)
            except (RuntimeError, AttributeError):
                # Fallback if accessed outside of a page context
                current_language = Translations.DEFAULT_LANGUAGE
        else:
            current_language = language
        
        # 2. Fetch Translation with Fallback (supports dot notation)
        # Try selected language
        lang_dict = Translations.translations.get(current_language, {})
        translation = Translations._get_nested_value(lang_dict, key)
        
        # Fallback to default language if missing
        if translation is None and current_language != Translations.DEFAULT_LANGUAGE:
            fallback_dict = Translations.translations.get(Translations.DEFAULT_LANGUAGE, {})
            translation = Translations._get_nested_value(fallback_dict, key)
            
        # If still None, return key
        if translation is None:
            return key
            
        # 3. Handle Interpolation
        if kwargs:
            try:
                return translation.format(**kwargs)
            except (KeyError, ValueError):
                # Fallback if format keys are missing or malformed
                return translation
                
        return translation

# Load translations immediately when this module is imported
Translations.load_translations()
