import os
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_api_key.models import APIKey
import re

from common.api.messages import Messages
from common.log.logger import Logger

# TODO. This class is not needed anymore. File can be removed.
class ApiKeyUtils(Logger, BaseAuthentication):
    AUTH_SCHEME = os.getenv("AUTH_TOKEN", "Key").lower()
    REGEX_PATTERN = r'^user\d{3}$'
    
    def get_name(self, request):
        key = request.META.get('HTTP_X_API_KEY')
        
        api_key = APIKey.objects.get_from_key(key)
        return api_key.name
    
    def authenticate(self, request):
        self.warning("Trying to authenticate user...")
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        
        if not auth_header:
            self.error("No auth header found.")
            raise AuthenticationFailed(
                Messages.Auth.invalid_api_key()
            )
            
        try:
            scheme, key = auth_header.split(' ', 1)
        except ValueError:
            self.error("Invalid auth header format.")
            raise AuthenticationFailed(Messages.Auth.invalid_api_key())
            
        if scheme.lower() != os.getenv("AUTH_TOKEN", "user"):
            self.error("Invalid auth scheme.")
            raise AuthenticationFailed(Messages.Auth.invalid_api_key())
            
        try:
            api_key = APIKey.objects.get_from_key(key)
            user = api_key.name
                        
            if not re.fullmatch(self.REGEX_PATTERN, user):
                self.error("Invalid user name.")
                raise AuthenticationFailed(Messages.Auth.user_not_found())
            self.warning("User authenticated.")
            return (user, api_key)
            
        except APIKey.DoesNotExist:
            self.error("API key does not exist.")
            raise AuthenticationFailed(Messages.Auth.invalid_api_key())
        except Exception:
            self.error("An error occurred during authentication.")
            raise AuthenticationFailed(Messages.Auth.invalid_api_key())