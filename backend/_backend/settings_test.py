from .settings import * 
REST_FRAMEWORK['DEFAULT_PERMISSION_CLASSES'] = [
    'rest_framework.permissions.AllowAny', # Use DRF's built-in bypass
]

DEBUG = False