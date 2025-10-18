import os
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_api_key.models import APIKey
import re

from common.api.messages import Messages

class APIKeyAuthentication(BaseAuthentication):
    AUTH_SCHEME = os.getenv("AUTH_TOKEN", "Key").lower()
    REGEX_PATTERN = r'^user\d{3}$'
    
    def authenticate(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        
        if not auth_header:
            raise AuthenticationFailed(
                Messages.APIKey.invalid_key()
            )
            
        try:
            scheme, key = auth_header.split(' ', 1)
        except ValueError:
            raise AuthenticationFailed(Messages.APIKey.invalid_key())
            
        if scheme.lower() != os.getenv("AUTH_TOKEN", "user"):
            raise AuthenticationFailed(Messages.APIKey.invalid_key())
            
        try:
            api_key = APIKey.objects.get_from_key(key)
            user = api_key.name
                        
            if not re.fullmatch(self.REGEX_PATTERN, user):
                raise AuthenticationFailed(Messages.APIKey.not_a_user())
            return (user, api_key)
            
        except APIKey.DoesNotExist:
            raise AuthenticationFailed(Messages.APIKey.invalid_key())
        except Exception:
            raise AuthenticationFailed(Messages.APIKey.invalid_key())