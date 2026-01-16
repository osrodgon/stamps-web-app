from nicegui import app

def _(text: str):
    """
    Translates a given text key using the application's translation service.

    This is a convenience function that wraps `Translations.translate` to provide
    a shorter, more common syntax for translation, often used as `_('key')`.

    Args:
        text (str): The key for the text to be translated.

    Returns:
        str:    The translated string for the user's current language, or the key
                if no translation is found.
    """
    return Translations.translate(text)

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
    translations = {
        'en' : {
            'account_details':              'Enter your details to sign up for an account',
            'agree':                        'I agree to the <a class="text-primary" href="#">Terms of Service</a> and <a class="text-primary" href="#">Privacy Policy</a>',
            'cancel':                       'Cancel',
            'close':                        'Close',
            'collectibles':                 'COLLECTIBLES',
            'collections_tile':             'Collections',
            'confirm_password':             'Confirm Password',
            'create_account':               'Create an account',
            'email':                        'Email',
            'first_name':                   'First Name',
            'invalid_email':                'Invalid email address',
            'invalid_password':             'Password must be at least 8 characters, include uppercase, lowercase, number, and special character',
            'last_name':                    'Last Name',
            'logout':                       'Logout',
            'logout_confirm':               'Confirm Logout',
            'logout_confirm_message':       'Are you sure you want to log out of your account?',
            'no_account':                   'Don\'t have an account?',
            'no_response':                  'Login request failed, no response from server.',
            'page_not_found':               'The page you are looking for is **not found** on this server.',
            'password':                     'Password',
            'password_not_match':           'Passwords do not match',
            'profile':                      'Profile',
            'required':                     'This field is required',
            'response_issue':               'Login failed due to a server response issue.',
            'response_mock_login':          'Could not mock login. Review environment variables and ensure database is running.',
            'review_form_data':             'Data invalid or missing. Please review the form and try again.',
            'settings':                     'Settings',
            'sign_in':                      'Sign In',
            'sign_up':                      'Sign up',
            'sign_up_sucess':               'User registered successfully',
            'stamps_manager_title':         'Stamps Manager',
            'take_me_home':                 'TAKE ME HOME',
            'token_missing':                'Could not obtain token from login response.',
            'username':                     'Username',
            'username_and_password':        'Enter your username and password to access your account',
            'username_password_required':   'Username and password are required.',
            'you_are_lost':                 'Oops! You seem to be lost.',
            'your_stamps_world':            'Your World of Stamps',
        },
        'es' : {
            'account_details':              'Introduce tus datos para crear una cuenta',
            'agree':                        'Acepto los <a class="text-primary" href="#">Términos de servicio</a> y la <a class="text-primary" href="#">Política de privacidad</a>',
            'cancel':                       'Cancelar',
            'close':                        'Cerrar',
            'collectibles':                 'COLECCIONABLES',
            'collections_tile':             'Colecciones',
            'confirm_password':             'Confirmar Contraseña',
            'create_account':               'Crear una cuenta',
            'email':                        'Correo electrónico',
            'first_name':                   'Nombre',
            'invalid_email':                'Dirección de correo electrónico no válida',
            'invalid_password':             'La contraseña debe tener al menos 8 caracteres, incluir mayúsculas, minúsculas, números y carácteres especiales',
            'last_name':                    'Apellidos',
            'logout':                       'Cerrar sesión',
            'logout_confirm':               'Confirmar cierre de sesión',
            'logout_confirm_message':       '¿Estás seguro de que quieres cerrar tu sesión?',
            'no_account':                   '¿No tienes una cuenta?',
            'no_response':                  'Fallo en la solicitud de inicio de sesión, el servidor no responde.',
            'page_not_found':               'La página que buscas **no se encuentra** en este servidor.',
            'password':                     'Contraseña',
            'password_not_match':           'Las contraseñas no coinciden',
            'profile':                      'Perfil',
            'required':                     'Este campo es obligatorio',
            'response_issue':               'Error al iniciar sesión debido a un problema con la respuesta del servidor.',
            'response_mock_login':          'No se pudo simular el inicio de sesión. Revise las variables de entorno y asegúrese de que la base de datos esté funcionando.',
            'review_form_data':             'Datos inválidos o faltantes. Por favor, revisa el formulario y inténtalo de nuevo.',
            'settings':                     'Ajustes',
            'sign_in':                      'Iniciar sesión',
            'sign_up':                      'Regístrate',
            'sign_up_sucess':               'Usuario registrado correctamente',
            'stamps_manager_title':         'Gestión de Sellos',
            'take_me_home':                 'Volver al Inicio',
            'token_missing':                'No se pudo obtener el token de la respuesta de inicio de sesión.',
            'username':                     'Usuario',
            'username_and_password':        'Introduce tu nombre de usuario y contraseña para acceder a tu cuenta',
            'username_password_required':   'El nombre de usuario y la contraseña son obligatorios.',
            'you_are_lost':                 '¡Ups! Parece que te has perdido.',
            'your_stamps_world':            'Tu Mundo De Sellos',
        }
    }
    
    @staticmethod
    def translate(key):
        """
        Translates a key into the user's language.

        This static method determines the user's language from `app.storage.user`,
        with a default of 'en'. It then looks up the provided key in the
        `translations` dictionary.

        Args:
            key (str): The translation key to look up.

        Returns:
            str:    The translated string. If the language or key is not found,
                    it gracefully returns the original key.
        """
        current_language = app.storage.user.get('language', 'en')
        
        return Translations.translations.get(current_language, {}).get(key, key)
