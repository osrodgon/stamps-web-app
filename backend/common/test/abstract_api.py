import pytest
from rest_framework.exceptions import PermissionDenied

from common.api.messages import Messages

class AbstractAPI:
    @pytest.fixture(autouse=True)
    def setup_mock(self, mocker):
        self.__mocker = mocker
        self.__permission_class = 'common.core.permissions.HasSpecificKeyName.has_permission'
        
    def permission(self, granted: bool, message: str = None):
        if granted:
            self.__mocker.patch(self.__permission_class, return_value=True)
        else:
            self.__mocker.patch(self.__permission_class, side_effect=PermissionDenied(message))
            
    def connection_lost(self, method):
        self.__mocker.patch(method, side_effect=Exception(Messages.server_error()))
        
