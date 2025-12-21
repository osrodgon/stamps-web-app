from nicegui import app

class Translations:
    translations = {
        'en' : {
            'E001': 'Login request failed, no response from server.',
            'E002': 'Login failed due to a server response issue.',
            'E003': 'Username and password are required.',
            'E004': 'Could not obtain token from login response.',
            'L001': 'Sign In',
            'L002': 'Enter your username and password to access your account',
            'L003': 'Username',
            'L004': 'Password',
            'L005': 'Don\'t have an account?',
            'L006': 'Sign up',
            'L007': 'COLLECTIBLES',
            'L008': 'Your World of Stamps',
            'L009': 'Oops! You seem to be lost.',
            'L010': 'The page you are looking for is **not found** on this server.',
            'L011': 'TAKE ME HOME'
        },
        'es' : {
            'E001': 'Fallo en la solicitud de inicio de sesión, el servidor no responde.',
            'E002': 'Error al iniciar sesión debido a un problema con la respuesta del servidor.',
            'E003': 'El nombre de usuario y la contraseña son obligatorios.',
            'E004': 'No se pudo obtener el token de la respuesta de inicio de sesión.',
            'L001': 'Iniciar sesión',
            'L002': 'Introduce tu nombre de usuario y contraseña para acceder a tu cuenta',
            'L003': 'Usuario',
            'L004': 'Contraseña',
            'L005': '¿No tienes una cuenta?',
            'L006': 'Regístrate',
            'L007': 'COLECCIONABLES',
            'L008': 'Tu Mundo De Sellos',
            'L009': '¡Ups! Parece que te has perdido.',
            'L010': 'La página que buscas **no se encuentra** en este servidor.',
            'L011': 'Volver al Inicio'
        }
    }
    
    @staticmethod
    def translate(key):
        current_language = app.storage.user.get('language', 'en')
        
        return Translations.translations.get(current_language, {}).get(key, key)
