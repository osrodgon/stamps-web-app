from io import BytesIO
import json
import sys
from unittest.mock import MagicMock
import nicegui
import pytest
import requests

from frontend.utils.log_setup import log_setup

class AbstractUnitTest:
    """Abstract base class for unit tests, providing helper methods for mocking and component interaction."""
    __mocker = None
    __mocker_instance = None
    
    # @pytest.fixture(scope="session", autouse=True)
    # def setup_logging_for_test(self):
    #     log_setup(is_testing=True)
    #     yield
        
    def __get_class_path(self, cls: object) -> str:
        """
        Get the full import path of a class.

        Args:
            cls (object): The class object.

        Returns:
            str: The full import path string of the class.
        """
        return f"{cls.__module__}.{cls.__name__}"
    
    def get_component(self, page, object):
        """
        Find a component of a specific type on a given page.

        Args:
            page: The page object containing elements to search through.
            object: The class of the component to find.

        Returns:
            The component instance if found, otherwise None.
        """
        for key, component in page.elements.items():
            if isinstance(component, object):
                return component
        return None
    
    def set_card_valid(self, card, valid):
        """
        Mock the 'is_valid' method of a card component.

        Args:
            card: The card class to be mocked.
            valid (bool): The boolean value to be returned by 'is_valid'.

        Returns:
            The mocker patch object.
        """
        return self.__mocker.patch(f"{self.__get_class_path(card)}.is_valid", return_value=valid)
    
    def set_backend_response(self, class_object, status_code, json_data):
        """
        Mock a backend API response for a given class's '_make_request' method.

        Args:
            class_object: The class whose '_make_request' method will be mocked.
            status_code (int): The HTTP status code for the mock response.
            json_data (dict or None): The JSON data for the mock response body. If None, the response will be None.

        Returns:
            The mocker patch object.
        """
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
        """
        Mock the 'notify' method of a class to prevent notifications during tests.

        Args:
            class_object: The class whose 'notify' method will be mocked.

        Returns:
            The mocker patch object.
        """
        return self.__mocker.patch(f"{self.__get_class_path(class_object)}.notify", return_value=None)   
    
    def create_user_storage(self, __mocker):
        """
        Mock 'nicegui.app.storage' to provide a testable user storage dictionary.

        Args:
            __mocker: The mocker fixture instance.

        Returns:
            dict: The mocked user storage dictionary.
        """
        mock_user_storage = {}
        mock_storage = MagicMock()
        mock_storage.user = mock_user_storage

        __mocker.patch.object(
            nicegui.app, # The class/object whose attribute you want to replace
            'storage',     # The attribute name
            new=mock_storage # The mock object to use instead
            )
        return mock_user_storage