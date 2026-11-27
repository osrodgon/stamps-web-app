import pytest
from pytest_mock import MockerFixture
from rest_framework.exceptions import PermissionDenied
from django.contrib.auth.hashers import make_password

from common.api.custom_api_exceptions import DatabaseConnectionLost
from common.api.messages import Messages
from common.test.login_api_test_data import login_api_response_ok
from users_api.models import UserCollection, UserToken


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
        self.__login_view = 'users_api.api.views.login_view'
        self.__logoff_view = 'users_api.api.views.logoff_view'
        self.__jwt_class = 'common.core.jwt_token.JwtToken'
        self.__user_token_class = 'users_api.models.UserToken'
        self.__mocked_instance = None
        
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
        """Mock the API permission check for a test case.

        This method simulate the behavior of the `HasSpecificKeyName.has_permission`
        method. It can be configured to either grant permission by returning True
        or deny it by raising a `PermissionDenied` exception.

        Args:
            granted (bool): If `True`, the permission check is mock to succeed.
                            If `False`, it's mocked to raise `PermissionDenied`.
            message (str, optional): The error message for the `PermissionDenied` exception.
        """
        if granted:
            self.header("test_key")
            return self.__mocker.patch(f"{self.__permission_class}.has_permission", return_value=True)
        else:
            self.header("test_key")
            return self.__mocker.patch(f"{self.__permission_class}.has_permission", side_effect=PermissionDenied(message))
            
    def header(self, key: str):
        """Mock the authentication header processing.

        This method patches the `authenticate` method of the custom authentication
        class to simulate a successful authentication. It makes the method return
        a tuple where the first element (user) is None and the second element
        (auth) is the provided API key.

        Args:
            key (str):  The API key string to be returned by the mocked
                        authentication method.
        """
        return self.__mocker.patch(f"{self.__authentication_class}.authenticate", return_value=(None, key)) 
            
    def class_path(self, cls: object) -> str:
        """Generate the full mock path for a Django model's `objects.get` method.

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
        """Mock a database connection failure for a specific class method.

        This helper patches the specified method on a given class to raise a
        `DatabaseConnectionLost` exception, simulating a scenario where the
        database is unreachable during an operation.

        Args:
            cls (object): The class containing the method to be patched (e.g., a model).
            method (str, optional): The name of the method to patch (e.g., 'objects.all', 'save').
                                    Defaults to None.
        """
        path = f"{self.__get_class_path(cls)}.{method}"
        
        return self.__mocker.patch(path, side_effect=DatabaseConnectionLost(Messages.Database.connection_lost()))
        
    def get_name(self):
        """Mock the `ApiKeyUtils.get_name` method to return a test user.

        This helper patches the utility method responsible for extracting the
        key name, forcing it to return the static value "test_user".
        """
        return self.__mocker.patch(f"{self.__api_key_utils_class}.get_name", return_value="test_user")
        
    def get_user(self):
        """Mock the `UserCollection.objects.get` method to return a test user.

        This helper patches the `get` method on the `UserCollection` manager to
        return a hardcoded user instance. This is useful for tests that require
        an authenticated user to be "retrieved" from the database.
        """
        return self.__mocker.patch(
            f"{self.__user_collection_class}.objects.get", 
            return_value=UserCollection.objects.create(
                username="testuser3",
                email="test3@example.com",
                password_hash=make_password("password123"),
                first_name="Test",
                last_name="UserThree"
            )
        )
        
    def cursor_error(self, exception: Exception):
        """Simulate a database error by patching the Django cursor's `execute` method.

        This is a low-level utility to test how the application handles
        unexpected database exceptions (e.g., IntegrityError, OperationalError)
        during query execution.

        Args:
            exception (Exception):  The exception instance to be raised when the
                                    database cursor's `execute` method is called.
        """
        return self.__mocker.patch(self.__backend_cursor, side_effect=exception)
        
    def create_serializer_object(self, path: str, cls : object, data: object):
        """Mock the instantiation of a serializer object within the code under test.

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
        return self.__mocker.patch(
            f"{path}",
            return_value=cls(data=data)
        )
        
    def validate_password_user_not_found(self):
        """Mocks the user not being found during password validation.

        This patches `UserCollection.objects.get` to raise a `DoesNotExist`
        exception, simulating the case where a username does not exist in the
        database during a login attempt.
        """
        return self.__mocker.patch(
            f"{self.__user_collection_class}.objects.get",
            side_effect = UserCollection.DoesNotExist
        )
    
    def validate_password_user_found(self):
        """Mocks the user being found during password validation.

        This is a convenience method that calls `get_user()` to ensure that
        the `UserCollection.objects.get` call will successfully return a
        mocked user object.
        """
        self.get_user()
    
    def validate_password_match(self, match=True):
        """Mocks the password checking logic.

        This patches the `check_password` method within the login view to
        control the outcome of a password validation check.

        Args:
            match (bool, optional): If `True`, the password check is mocked to
                                    succeed. If `False`, it's mocked to fail.
                                    Defaults to True.
        """
        return self.__mocker.patch(
            f"{self.__login_view}.check_password",
            return_value = match
        )
        
    def create_jwt_token(self, success = True):
        """Mocks the JWT token creation process.

        This patches `JwtToken.create` to simulate either a successful token
        creation (returning a predefined token structure) or a failure
        (returning `None`).

        Args:
            success (bool, optional):   If `True`, returns a sample successful
                                        login response. If `False`, returns `None`.
                                        Defaults to True.
        """
        response = None
        if success:
            response = login_api_response_ok()
        
        return self.__mocker.patch(
            f"{self.__jwt_class}.create",
            return_value = response
        )
        
    def validate_jwt_token(self, valid=True):
        """Mocks the JWT token validation during logoff.

        This patches `JwtToken.validate` to simulate the outcome of token
        validation. A valid token returns a dictionary with user and JTI,
        while an invalid one returns `None`.

        Args:
            valid (bool, optional): If `True`, the mock returns a payload
                                    indicating a valid token. If `False`, it
                                    returns `None`. Defaults to True.
        """
        data = None
        if valid:
            data = {
                'user_id': 1,
                'jti': 'fake_jti'
            }
        return self.__mocker.patch(
            f"{self.__logoff_view}.JwtToken.validate",
            return_value=data
        )
        
        
    def get_user_token(self, exist=True):
        """Mocks the retrieval of a user's JWT from the database.

        This patches `UserToken.objects.get` to either return a mock token
        instance (if `exist` is True) or raise `UserToken.DoesNotExist` (if
        `exist` is False).

        Args:
            exist (bool, optional): Determines if the token is found or not.
                                    Defaults to True.
        """
        if exist:
            self.__mocked_instance = self.__mocker.Mock()
            return self.__mocker.patch(
                f"{self.__user_token_class}.objects.get",
                return_value = self.__mocked_instance
            )
        else:
            return self.__mocker.patch(
                f"{self.__user_token_class}.objects.get",
                side_effect = UserToken.DoesNotExist
            )
        
    def delete_user_token(self):
        """Asserts that the user token deletion method was called.

        This should be used after a test that is expected to log a user out
        and delete their stored token. It checks if the `delete()` method was
        called on the mocked `UserToken` instance.
        """
        if self.__mocked_instance:
            self.__mocked_instance.delete.assert_called_once()
