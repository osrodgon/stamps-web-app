from os import getenv
from rest_framework_api_key.permissions import HasAPIKey
from rest_framework_api_key.models import APIKey
from rest_framework.exceptions import PermissionDenied

from _backend.settings import USER_VIEWS
from common.api.messages import Messages
from common.log.logger import Logger
from common.core.jwt_token import JwtToken

class HasSpecificKeyName(Logger, HasAPIKey):
    def __check_api_key_is_valid(self, key):
        try:
            self.log.debug("Checking API Key...")
            APIKey.objects.get_from_key(key)
        except APIKey.DoesNotExist:
            self.log.error("API Key not found.")
            raise PermissionDenied(
                Messages.Auth.invalid_api_key()
            )
        self.log.debug("User authenticated with API Key.")
        
    def __check_jwt_is_valid(self, key):
        if (JwtToken().validate(key) is None):
            self.log.error("JWT not valid.")
            raise PermissionDenied(
                Messages.Auth.invalid_jwt()
            )
        
    def __apply_permissions(self, view, key):
        if key == getenv("X_API_MASTER_KEY"):
            self.log.debug("User authenticated with master key.")
            return True
        
        if view.__class__.__name__ in USER_VIEWS:
            self.log.debug("User authenticated with user token.")
            return True
        
        self.log.error("User authenticated, but not authorized.")
        raise PermissionDenied(
            Messages.Auth.not_enough_rights()
        )
        
    def has_permission(self, request, view):
        self.log.debug("Trying to authenticate user...")
        try:
            auth_type, key = request.META.get("HTTP_AUTHORIZATION").split(" ")
        except ValueError:
            self.log.error("Header has an invalid format.")
            raise PermissionDenied(
                Messages.Auth.invalid_format()
            )
        
        match auth_type.upper():
            case "API-KEY":
                self.__check_api_key_is_valid(key)        
            case "JWT":
                self.__check_jwt_is_valid(key)
            case _:
                self.log.error("Invalid authentication type.")
                raise PermissionDenied(
                    Messages.Auth.not_supported()
                )
                
        return self.__apply_permissions(view, key)
        
