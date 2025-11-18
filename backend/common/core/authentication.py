from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from _backend.settings import REDOC_ENDPOINT, SCHEMA_ENDPOINT, SERVER_URL_V1, SWAGGER_ENDPOINT
from common.api.messages import Messages
from common.log.logger import Logger

class CustomAPIKeyAuthentication(Logger, BaseAuthentication):
    """
    Authentication class that uses the HasSpecificKeyName permission logic.
    """
    EXEMPT_PATHS = [
        f"/{SERVER_URL_V1}{SCHEMA_ENDPOINT}",
        f"/{SERVER_URL_V1}{SWAGGER_ENDPOINT}",
        f"/{SERVER_URL_V1}{REDOC_ENDPOINT}"
    ]
    
    def authenticate(self, request):
        self.log.debug("Checking header...")
        
        if request.path in self.EXEMPT_PATHS:
            return None
        
        key = request.META.get("HTTP_AUTHORIZATION")
        
        if not key:
            self.log.error("Header not found.")
            raise AuthenticationFailed(
                Messages.Auth.header_missing()
            )
        
        # Return a non-None value to signal successful authentication. 
        # The user is None, and the auth component is the key itself.
        # The permission class will use this key.
        self.log.debug("Header found.")
        return (None, key)

        