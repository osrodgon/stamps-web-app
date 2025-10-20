from pickle import GET
import pytest
from rest_framework.exceptions import PermissionDenied

from common.api.custom_api_exceptions import DatabaseConnectionLost
from common.api.messages import Messages

class AbstractApiUnitTest:
    GET_ALL = "objects.all"
    GET_ONE = "objects.get"
    POST = "save"
    PUT = "save"
    DELETE = "delete"
    
    @pytest.fixture(autouse=True)
    def setup_mock(self, mocker):
        self.__mocker = mocker
        self.__permission_class = 'common.core.permissions.HasSpecificKeyName.has_permission'
        
    def permission(self, granted: bool, message: str = None):
        if granted:
            self.__mocker.patch(self.__permission_class, return_value=True)
        else:
            self.__mocker.patch(self.__permission_class, side_effect=PermissionDenied(message))
            
    def class_path(self, cls: object) -> str:
        return f"{cls.__module__}.{cls.__name__}.objects.get"
            
    def connection_lost(self, cls: object, method: str = None):
        path = f"{cls.__module__}.{cls.__name__}.{method}"
        
        self.__mocker.patch(path, side_effect=DatabaseConnectionLost(Messages.Database.connection_lost()))
        
