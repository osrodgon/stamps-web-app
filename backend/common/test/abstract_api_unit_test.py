# from pickle import GET
import pytest
from rest_framework.exceptions import PermissionDenied
from django.contrib.auth.hashers import make_password

from common.api.custom_api_exceptions import DatabaseConnectionLost
from common.api.messages import Messages
from users_api.models import UserCollection

class AbstractApiUnitTest:
    GET_ALL = "objects.all"
    GET_ONE = "objects.get"
    POST = "save"
    PUT = "save"
    DELETE = "delete"
    
    @pytest.fixture(autouse=True)
    def setup_mock(self, mocker):
        self.__mocker = mocker
        self.__permission_class = 'common.core.permissions.HasSpecificKeyName'
        self.__api_key_utils_class = 'common.core.api_key_utils.ApiKeyUtils'
        self.__user_collection_class = 'users_api.models.UserCollection'
        self.__authentication_class = 'common.core.authentication.CustomAPIKeyAuthentication'
        self.__backend_cursor = 'django.db.backends.utils.CursorWrapper.execute'
          
    def permission(self, granted: bool, message: str = None):
        if granted:
            self.header("test_key")
            self.__mocker.patch(f"{self.__permission_class}.has_permission", return_value=True)
        else:
            self.header("test_key")
            self.__mocker.patch(f"{self.__permission_class}.has_permission", side_effect=PermissionDenied(message))
            
    def header(self, key: str):
        self.__mocker.patch(f"{self.__authentication_class}.authenticate", return_value=(None, key)) 
            
    def class_path(self, cls: object) -> str:
        return f"{cls.__module__}.{cls.__name__}.objects.get"
            
    def connection_lost(self, cls: object, method: str = None):
        path = f"{cls.__module__}.{cls.__name__}.{method}"
        
        self.__mocker.patch(path, side_effect=DatabaseConnectionLost(Messages.Database.connection_lost()))
        
    def get_name(self):
        self.__mocker.patch(f"{self.__api_key_utils_class}.get_name", return_value="test_user")
        
    def get_user(self):
        self.__mocker.patch(
            f"{self.__user_collection_class}.objects.get", 
            return_value=UserCollection.objects.create(
                username="testuser1",
                email="test1@example.com",
                password_hash=make_password("password123"),
                first_name="Test",
                last_name="UserOne"
            )
        )
        
    def cursor_error(self, exception):
        self.__mocker.patch(self.__backend_cursor, side_effect=exception)
            
