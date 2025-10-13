from rest_framework_api_key.permissions import HasAPIKey
from rest_framework.exceptions import PermissionDenied
from rest_framework_api_key.models import APIKey

from common.api.messages import Messages

class HasSpecificKeyName(HasAPIKey):
    """
    Custom permission that requires a valid API Key AND checks if the 
    API Key's name is in the list of ALLOWED_KEY_NAMES.
    """
    def has_permission(self, request, view):
        # 1. First, run the parent's (HasAPIKey) authentication check.
        # This ensures the raw key is valid, unrevoked, and not expired.
        # If this fails, it raises PermissionDenied/NotAuthenticated (401/403).
        if not super().has_permission(request, view):
            message = "THis is an error"
            return False

        # 2. Authorization Check (Name Check)
        # The APIKey instance is attached to request.auth upon successful validation
        key = request.META.get("HTTP_X_API_KEY")
        api_key_name = APIKey.objects.get_from_key(key)
        api_user = request.META.get("HTTP_X_API_USER")
        
        # Check if the name of the valid key is the same as the one passed as header
        if str(api_key_name) == str(api_user):
            return True
        else:
            # If the key is valid but the name doesn't match, raise a specific error
            message = "This is another error"
            raise PermissionDenied(
                Messages.APIKey.invalid_user()
            )
