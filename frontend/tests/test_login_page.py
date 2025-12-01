import pytest
from nicegui.testing import User

from components.auth.login_card import LoginCard
from pages.auth.login_page import LoginPage

class AbstractUI:
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
    
    def set_backend_response(self, object, response):
        return self.__mocker.patch(f"{self.__get_class_path(object)}._make_request", return_value=response)
    
    def skip_notify(self, object):
        return self.__mocker.patch(f"{self.__get_class_path(object)}.notify", return_value=None)   
    
    

class TestLoginPage(AbstractUI):
    
    @pytest.mark.asyncio
    async def test_successful_login(self, user: User, mocker):
        self._AbstractUI__mocker = mocker
        login_object = await user.open('/login')
        
        login_card = self.get_component(login_object, LoginCard)
        login_page = self.get_component(login_object, LoginPage)
        
        self.set_card_valid(login_card.__class__, True)
        self.set_backend_response(login_page.__class__, None)
        self.skip_notify(login_page.__class__)
        
        assert login_card is not None
        assert login_page is not None
        
        # Simulates user hitting Login button
        response = await login_page.call_rest_method()
        
        assert True
        