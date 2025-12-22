from nicegui import app

def _(text: str):
    return Translations.translate(text)

class Translations:
    translations = {
        'en' : {
            'no_response':                  'Login request failed, no response from server.',
            'response_issue':               'Login failed due to a server response issue.',
            'username_password_required':   'Username and password are required.',
            'token_missing':                'Could not obtain token from login response.',
            'sign_in':                      'Sign In',
            'username_and_password':        'Enter your username and password to access your account',
            'username':                     'Username',
            'password':                     'Password',
            'no_account':                   'Don\'t have an account?',
            'sign_up':                      'Sign up',
            'collectibles':                 'COLLECTIBLES',
            'your_stamps_world':            'Your World of Stamps',
            'you_are_lost':                 'Oops! You seem to be lost.',
            'page_not_found':               'The page you are looking for is **not found** on this server.',
            'take_me_home':                 'TAKE ME HOME'
        },
        'es' : {
            'no_response':                  'Fallo en la solicitud de inicio de sesión, el servidor no responde.',
            'response_issue':               'Error al iniciar sesión debido a un problema con la respuesta del servidor.',
            'username_password_required':   'El nombre de usuario y la contraseña son obligatorios.',
            'token_missing':                'No se pudo obtener el token de la respuesta de inicio de sesión.',
            'sign_in':                      'Iniciar sesión',
            'username_and_password':        'Introduce tu nombre de usuario y contraseña para acceder a tu cuenta',
            'username':                     'Usuario',
            'password':                     'Contraseña',
            'no_account':                   '¿No tienes una cuenta?',
            'sign_up':                      'Regístrate',
            'collectibles':                 'COLECCIONABLES',
            'your_stamps_world':            'Tu Mundo De Sellos',
            'you_are_lost':                 '¡Ups! Parece que te has perdido.',
            'page_not_found':               'La página que buscas **no se encuentra** en este servidor.',
            'take_me_home':                 'Volver al Inicio'
        }
    }
    
    @staticmethod
    def translate(key):
        current_language = app.storage.user.get('language', 'en')
        
        return Translations.translations.get(current_language, {}).get(key, key)
