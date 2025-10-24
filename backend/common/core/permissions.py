from os import getenv
from rest_framework_api_key.permissions import HasAPIKey
from rest_framework.exceptions import PermissionDenied

from _backend.settings import USER_VIEWS
from common.api.messages import Messages
from users_api.models import UserCollection

class HasSpecificKeyName(HasAPIKey):
    def has_permission(self, request, view):
        key = request.META.get("HTTP_X_API_KEY")
        if not key:
            # If not a key, try to get the key from the user table
            # as a password hash
            try:
                user = UserCollection.objects.get(password_hash=key)
                key = user.password_hash
            except UserCollection.DoesNotExist:
                raise PermissionDenied(
                    Messages.APIKey.invalid_key()
                )
        
        if key == getenv("X_API_MASTER_KEY"):
            return True
        
        if view.__class__.__name__ in USER_VIEWS:
            return True
        
        raise PermissionDenied(
            Messages.APIKey.invalid_user()
        )
        
