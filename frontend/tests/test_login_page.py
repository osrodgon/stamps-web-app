from io import BytesIO
import json
from unittest.mock import MagicMock
import nicegui
import pytest
from nicegui.testing import User
from starlette.middleware.sessions import SessionMiddleware
from nicegui import app
import requests

from components.auth.login_card import LoginCard
from pages.auth.login_page import LoginPage

class AbstractUnitTest:
    __mocker = None
    __mocker_instance = None
        
    def __get_class_path(self, cls: object) -> str:
        """Constructs the full import path for a given class object.

        This private helper method is used to dynamically create the string
        path needed for mocking objects with `mocker.patch`.

        Args:
            cls (object): The class object for which to get the import path.

        Returns:
            str: The full import path of the class (e.g., 'module.submodule.ClassName').
        """
        return f"{cls.__module__}.{cls.__name__}"
    
    def get_component(self, page, object):
        for key, component in page.elements.items():
            if isinstance(component, object):
                return component
        return None
    
    def set_card_valid(self, card, valid):
        return self.__mocker.patch(f"{self.__get_class_path(card)}.is_valid", return_value=valid)
    
    def set_backend_response(self, class_object, status_code, json_data):
        if json_data is not None:
            json_bytes = json.dumps(json_data).encode('utf-8')
        
            response = requests.Response()
            response.status_code = status_code
            response._content = json_bytes
            response.raw = BytesIO(json_bytes)
            response.encoding = 'utf-8'
            response.headers['Content-Type'] = 'application/json'
        else:
            response = None
        
        return self.__mocker.patch(f"{self.__get_class_path(class_object)}._make_request", return_value=response)
    
    def skip_notify(self, class_object):
        return self.__mocker.patch(f"{self.__get_class_path(class_object)}.notify", return_value=None)   
    
    def create_user_storage(self, __mocker):
        mock_user_storage = {}
        mock_storage = MagicMock()
        mock_storage.user = mock_user_storage

        __mocker.patch.object(
            nicegui.app, # The class/object whose attribute you want to replace
            'storage',     # The attribute name
            new=mock_storage # The mock object to use instead
            )
        return mock_user_storage
    




login_api_response = {
    "data": {
        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ",
        "user": {
            "id": 1,
            "username": "testuser",
            "email": "test@email.com",
            "first_name": "Test",
            "last_name": "User",
            "registration_date": "2025-12-02T21:32:04.607Z",
            "is_active": True
        }
    },
    "success": True,
    "errors": None,
    "message": "Login successful"
}

@pytest.mark.asyncio
class TestLoginPage(AbstractUnitTest):
    @pytest.fixture(autouse=True)
    def init_data(self, mocker):
        self._AbstractUnitTest__mocker = mocker
    
    async def test_login_success_200(self, user: User, mocker):
        # self._AbstractUnitTest__mocker = mocker
        login_object = await user.open('/login')
        

        login_card = self.get_component(login_object, LoginCard)
        login_page = self.get_component(login_object, LoginPage)
        
        self.set_card_valid(card=login_card.__class__, valid=True)
        self.set_backend_response(class_object=login_page.__class__, json_data=login_api_response, status_code=200)
        self.skip_notify(class_object=login_card.__class__)
        user_storage = self.create_user_storage(mocker)
        
        assert login_card is not None
        assert login_page is not None
        
        # Simulates user hitting Login button
        response = await login_page.call_rest_method()
        
        assert response.status_code == 200
        assert response.json() == login_api_response
        assert user_storage['jwt_token'] == login_api_response['data']['token']
        
    async def test_login_fail_400(self, user: User, mocker):
        pass
    
    async def test_login_fail_401(self, user: User, mocker):
        pass
    
    async def test_login_fail_501(self, user: User, mocker):
        pass
    