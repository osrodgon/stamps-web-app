# from pickle import GET
import pytest
from pytest_mock import MockerFixture
from rest_framework.exceptions import PermissionDenied
from django.contrib.auth.hashers import make_password

from common.api.custom_api_exceptions import DatabaseConnectionLost
from common.api.messages import Messages
from users_api.models import UserCollection

class AbstractApiUnitTest:
    """Abstract base class for API unit tests.

    This class provides a collection of helper methods and fixtures to simplify
    the process of writing unit tests for Django REST Framework API views. It
    centralizes common mocking patterns for authentication, permissions,
    database interactions, and serializer behavior.

    Attributes:
        GET_ALL (str): String constant for mocking `objects.all`.
        GET_ONE (str): String constant for mocking `objects.get`.
        POST (str): String constant for mocking `save` on creation.
        PUT (str): String constant for mocking `save` on update.
        DELETE (str): String constant for mocking `delete`.
    """
    GET_ALL = "objects.all"
    GET_ONE = "objects.get"
    POST = "save"
    PUT = "save"
    DELETE = "delete"
    
    @pytest.fixture(autouse=True)
    def setup_mock(self, mocker: MockerFixture):
        """Initializes the test environment for API unit tests.

        This autouse fixture is executed before each test. It stores the `mocker`
        fixture and defines the string paths for various classes and methods that
        are frequently patched in the unit tests. This centralization simplifies
        the creation of mocks in individual test cases.
        
        Args:
            mocker (MockerFixture): The pytest-mock fixture used to patch objects.
        """
        self.__mocker = mocker
        self.__permission_class = 'common.core.permissions.HasSpecificKeyName'
        self.__api_key_utils_class = 'common.core.api_key_utils.ApiKeyUtils'
        self.__user_collection_class = 'users_api.models.UserCollection'
        self.__authentication_class = 'common.core.authentication.CustomAPIKeyAuthentication'
        self.__backend_cursor = 'django.db.backends.utils.CursorWrapper.execute'
        
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
        
    def permission(self, granted: bool, message: str = None):
        """Mocks the API permission check for a test case.

        This method simulates the behavior of the `HasSpecificKeyName.has_permission`
        method. It can be configured to either grant permission by returning True
        or deny it by raising a `PermissionDenied` exception.

        Args:
            granted (bool): If `True`, the permission check is mocked to succeed.
                            If `False`, it's mocked to raise `PermissionDenied`.
            message (str, optional): The error message for the `PermissionDenied` exception.
        """
        if granted:
            self.header("test_key")
            self.__mocker.patch(f"{self.__permission_class}.has_permission", return_value=True)
        else:
            self.header("test_key")
            self.__mocker.patch(f"{self.__permission_class}.has_permission", side_effect=PermissionDenied(message))
            
    def header(self, key: str):
        """Mocks the authentication header processing.

        This method patches the `authenticate` method of the custom authentication
        class to simulate a successful authentication. It makes the method return
        a tuple where the first element (user) is `None` and the second element
        (auth) is the provided API key.

        Args:
            key (str):  The API key string to be returned by the mocked
                        authentication method.
        """
        self.__mocker.patch(f"{self.__authentication_class}.authenticate", return_value=(None, key)) 
            
    def class_path(self, cls: object) -> str:
        """Generates the full mock path for a Django model's `objects.get` method.

        This is a convenience method that combines the class's import path with
        the standard Django ORM accessor for retrieving a single object.

        Args:
            cls (object): The model class for which to create the mock path.

        Returns:
            str:    A string representing the full path to the `objects.get` method
                    (e.g., 'app.models.MyModel.objects.get').
        """
        return f"{self.__get_class_path(cls)}.objects.get"
            
    def connection_lost(self, cls: object, method: str = None):
        """Mocks a database connection failure for a specific class method.

        This helper patches the specified method on a given class to raise a
        `DatabaseConnectionLost` exception, simulating a scenario where the
        database is unreachable during an operation.

        Args:
            cls (object): The class containing the method to be patched (e.g., a model).
            method (str, optional): The name of the method to patch (e.g., 'objects.all', 'save').
                                    Defaults to None.
        """
        path = f"{self.__get_class_path(cls)}.{method}"
        
        self.__mocker.patch(path, side_effect=DatabaseConnectionLost(Messages.Database.connection_lost()))
        
    def get_name(self):
        """Mocks the `ApiKeyUtils.get_name` method to return a test user.

        This helper patches the utility method responsible for extracting the
        key name, forcing it to return the static value "test_user".
        """
        self.__mocker.patch(f"{self.__api_key_utils_class}.get_name", return_value="test_user")
        
    def get_user(self):
        """Mocks the `UserCollection.objects.get` method to return a test user.

        This helper patches the `get` method on the `UserCollection` manager to
        return a hardcoded user instance. This is useful for tests that require
        an authenticated user to be "retrieved" from the database.
        """
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
        
    def cursor_error(self, exception: Exception):
        """Simulates a database error by patching the Django cursor's `execute` method.

        This is a low-level utility to test how the application handles
        unexpected database exceptions (e.g., IntegrityError, OperationalError)
        during query execution.

        Args:
            exception (Exception):  The exception instance to be raised when the
                                    database cursor's `execute` method is called.
        """
        self.__mocker.patch(self.__backend_cursor, side_effect=exception)
        
    def create_serializer_object(self, path: str, cls : object, data: object):
        """Mocks the instantiation of a serializer object within the code under test.

        This helper patches the code at the specified `path` to return a
        pre-constructed serializer instance. This allows for fine-grained control
        over the serializer's state (e.g., its `is_valid` status or `validated_data`)
        during a unit test.

        Args:
            path (str): The full import path to the serializer class as used in the
                        view or function being tested (e.g., 'app.views.MySerializer').
            cls (object): The serializer class that will be instantiated.
            data (object):  The data payload (typically a dictionary) to initialize
                            the serializer instance with.
        """
        self.__mocker.patch(
            f"{path}",
            return_value=cls(data=data)
        )
        
