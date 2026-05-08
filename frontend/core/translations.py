import json
import flet as ft
from pathlib import Path
from settings import DEFAULT_LANGUAGE, USER_LANGUAGE

current_language = DEFAULT_LANGUAGE  # Default language fallback

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
        # 1. Determine Language
        lang = language or current_language
        
        # 2. Fetch Translation with Fallback (supports dot notation)
        # Try selected language
        lang_dict = Translations.translations.get(lang, {})
        translation = Translations._get_nested_value(lang_dict, key)
        
        # Fallback to default language if missing
        if translation is None and lang != DEFAULT_LANGUAGE:
            fallback_dict = Translations.translations.get(DEFAULT_LANGUAGE, {})
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
    
def set_language(lang: str):
    """
    Sets the current application language for translations (synchronous).

    This function updates the module-level `current_language` variable
    which is used by the `translate()` method to determine which language
    dictionary to use when resolving translation keys.

    This is a synchronous operation intended to be called after language
    changes (e.g., from a language selector button) to keep the translation
    system in sync with the persisted language preference.

    Args:
        lang (str): The language code to set (e.g., 'en', 'es').

    Note:
        This does NOT persist the language to SharedPreferences. To persist
        the change, also call `ft.SharedPreferences().set("language", lang)`.
    """
    global current_language
    
    current_language = lang
    
def get_language() -> str:
    """
    Retrieves the current application language code (synchronous).

    This function returns the module-level `current_language` variable
    which represents the active language for translations. It can be
    used to check the current language state or to conditionally
    display language-specific UI elements.

    Returns:
        str: The current language code (e.g., 'en', 'es').

    Example:
        current = get_language()
        if current == 'es':
            display_spanish_content()
    """
    global current_language
    
    return current_language

async def init_language():
    """
    Initializes the current language from SharedPreferences (async).

    This function should be called once during application startup to load
    the user's previously selected language from persistent storage. If no
    language is found in SharedPreferences, or if an error occurs during
    retrieval, the default language (DEFAULT_LANGUAGE) is used.

    This is an async function because it reads from Flet's SharedPreferences,
    which requires an await. Call this with `await init_language()` in an
    async context (e.g., in the main() function).

    Returns:
        None

    Example:
        async def main(page: ft.Page):
            await init_language()
            # ... rest of initialization
    """
    global current_language
    prefs = ft.SharedPreferences()
    
    try:
        stored_language = await prefs.get(USER_LANGUAGE)
        if stored_language:
            current_language = stored_language
    except Exception:
        current_language = DEFAULT_LANGUAGE
    
# Load translations immediately when this module is imported
Translations.load_translations()
