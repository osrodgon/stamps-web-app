from os import getenv
from rest_framework_api_key.permissions import HasAPIKey
from rest_framework.exceptions import PermissionDenied

from _backend.settings import USER_VIEWS
from common.api.messages import Messages

class HasSpecificKeyName(HasAPIKey):
    def has_permission(self, request, view):
        # Check initial permisions
        if not super().has_permission(request, view):
            raise PermissionDenied(
                Messages.APIKey.invalid_key()
            )

        # Check API Key
        key = request.META.get("HTTP_X_API_KEY")
        if key == getenv("X_API_MASTER_KEY"):
            return True
        
        if view.__class__.__name__ in USER_VIEWS:
            return True
        
        
        print(view.__class__.__name__)
        print(USER_VIEWS)
        raise PermissionDenied(
            Messages.APIKey.invalid_user()
        )
        
