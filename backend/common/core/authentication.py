import os
from tabnanny import check
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from common.api.messages import Messages
from common.core.permissions import HasSpecificKeyName # Import your permission class

class CustomAPIKeyAuthentication(BaseAuthentication):
    """
    Authentication class that uses the HasSpecificKeyName permission logic.
    """
    def authenticate(self, request):
        key = request.META.get("HTTP_X_API_KEY")
        
        if not key:
            return None
        
        # Return a non-None value to signal successful authentication. 
        # The user is None, and the auth component is the key itself.
        # The permission class will use this key.
        return (None, key)

        