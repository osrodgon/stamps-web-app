from nicegui import app

def _(text: str):
    """
    Translates the given text key into the current user's language.

    Args:
        text (str): The key to look up in the translation dictionary.

    Returns:
        str: The translated text, or the key itself if not found.
    """
    return Translations.translate(text)

class Translations:
    """
    A class to handle translations for the application.

    Attributes:
        translations (dict): A dictionary containing translation keys and values for supported languages.
    """
    translations = {
        'en' : {
            'account_details':              'Enter your details to sign up for an account',
            'agree':                        'I agree to the <a class="text-primary" href="#">Terms of Service</a> and <a class="text-primary" href="#">Privacy Policy</a>',
            'collectibles':                 'COLLECTIBLES',
            'confirm_password':             'Confirm Password',
            'create_account':               'Create an account',
            'email':                        'Email',
            'first_name':                   'First Name',
            'invalid_email':                'Invalid email address',
            'invalid_password':             'Password must be at least 8 characters, include uppercase, lowercase, number, and special character',
            'last_name':                    'Last Name',
            'no_account':                   'Don\'t have an account?',
            'no_response':                  'Login request failed, no response from server.',
            'page_not_found':               'The page you are looking for is **not found** on this server.',
            'password':                     'Password',
            'password_not_match':           'Passwords do not match',
            'required':                     'This field is required',
            'response_issue':               'Login failed due to a server response issue.',
            'review_form_data':             'Data invalid or missing. Please review the form and try again.',
            'sign_in':                      'Sign In',
            'sign_up':                      'Sign up',
            'sign_up_sucess':               'User registered successfully',
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
            'collectibles':                 'COLECCIONABLES',
            'confirm_password':             'Confirmar Contraseña',
            'create_account':               'Crear una cuenta',
            'email':                        'Correo electrónico',
            'first_name':                   'Nombre',
            'invalid_email':                'Dirección de correo electrónico no válida',
            'invalid_password':             'La contraseña debe tener al menos 8 caracteres, incluir mayúsculas, minúsculas, números y carácteres especiales',
            'last_name':                    'Apellidos',
            'no_account':                   '¿No tienes una cuenta?',
            'no_response':                  'Fallo en la solicitud de inicio de sesión, el servidor no responde.',
            'page_not_found':               'La página que buscas **no se encuentra** en este servidor.',
            'password':                     'Contraseña',
            'password_not_match':           'Las contraseñas no coinciden',
            'required':                     'Este campo es obligatorio',
            'response_issue':               'Error al iniciar sesión debido a un problema con la respuesta del servidor.',
            'review_form_data':             'Datos inválidos o faltantes. Por favor, revisa el formulario y inténtalo de nuevo.',
            'sign_in':                      'Iniciar sesión',
            'sign_up':                      'Regístrate',
            'sign_up_sucess':               'Usuario registrado correctamente',
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
        Retrieves the translation for a specific key based on the current user's language.

        Args:
            key (str): The translation key.

        Returns:
            str: The translated string for the current language, or the key if translation is missing.
        """
        current_language = app.storage.user.get('language', 'en')
        
        return Translations.translations.get(current_language, {}).get(key, key)
