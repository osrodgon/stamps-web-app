import logging
import pytest
import requests
from components.auth.login_card import LoginCard
from core.translations import _
from core.urls import URLs
from nicegui.testing import User
from pages.auth.login_page import LoginPage
from services.auth_service import AuthService
from tests.helpers.abstract_unit_test import AbstractUnitTest

from frontend.tests.data.users_api_responses import (
    LOGIN_RESPONSE_200_SUCCESS, LOGIN_RESPONSE_200_SUCCESS_MISSING_TOKEN,
    LOGIN_RESPONSE_400_BAD_REQUEST, LOGIN_RESPONSE_401_UNAUTHORIZED,
    LOGIN_RESPONSE_500_SERVER_ERROR)


@pytest.mark.asyncio
class TestLoginPage(AbstractUnitTest):
    """
    Unit tests for the LoginPage component.
    
    This class verifies the user authentication flow, including successful login,
    various authentication failure scenarios, redirection logic based on user roles,
    and user configuration synchronization.
    """
    
    @pytest.fixture(autouse=True)
    def init_data(self, mocker, caplog):
        """Initializes mock data and configures logging for tests."""
        caplog.set_level(logging.CRITICAL)
        self._mocker = mocker
        
    @pytest.fixture
    async def login_page_components(self, user: User):
        """
        Fixture that opens the login page and retrieves key components.
        
        Args:
            user (User): The NiceGUI testing user instance.
            
        Returns:
            tuple: A tuple containing (login_page, login_card).
        """
        login_object = await user.open(URLs.Frontend.login)
        login_card = self.get_component(login_object, LoginCard)
        login_page = self.get_component(login_object, LoginPage)
        
        assert login_card is not None
        assert login_page is not None
        yield login_page, login_card
        
    async def test_login_success_200(self, user: User, login_page_components, mocker):
        """
        Verifies a successful login attempt with valid credentials.
        
        Tests that:
        1. Valid credentials lead to a successful 200 OK response from the backend.
        2. User session information (JWT token) is correctly stored in local storage.
        """
        # Get components
        login_page, login_card = login_page_components
        
        # Set username and password
        login_card.username.value = 'testuser'
        login_card.password.value = 'testpassword'
        
        # Set mocks
        self.set_backend_response(
            class_object=AuthService, 
            json_data=LOGIN_RESPONSE_200_SUCCESS, 
            status_code=requests.codes.ok
        )
        self.skip_notify(class_object=login_card.__class__)
        user_storage = self.create_user_storage(mocker)
        
        # Simulates user hitting the submit button
        response = await login_page.call_rest_method()
        
        # Assert response
        assert response.status_code == requests.codes.ok
        assert response.json() == LOGIN_RESPONSE_200_SUCCESS
        assert user_storage['jwt_token'] == LOGIN_RESPONSE_200_SUCCESS['data']['token']
        
    async def test_login_success_200_missing_token(self, user: User, login_page_components):
        """
        Verifies the handling of a 200 OK response that is missing the JWT token.
        
        Tests that the application identifies this as an issue and notifies the user accordingly.
        """
        # Get components
        login_page, login_card = login_page_components
        
        # Set username and password
        login_card.username.value = 'testuser'
        login_card.password.value = 'testpassword'
        
        # Set mocks
        self.set_backend_response(
            class_object=AuthService, 
            json_data=LOGIN_RESPONSE_200_SUCCESS_MISSING_TOKEN, 
            status_code=requests.codes.ok
        )
        self.skip_notify(class_object=login_page.__class__)
        self.skip_notify(class_object=login_card.__class__)
        
        # Simulates user hitting the submit button
        response = await login_page.call_rest_method()
        
        # Assert response
        assert response == _('response_issue')
        
    async def test_login_fail_no_response(self, user: User, login_page_components):
        """
        Verifies the handling of a login attempt when the backend fails to respond.
        """
        # Get components
        login_page, login_card = login_page_components
        
        # Set username and password
        login_card.username.value = 'testuser'
        login_card.password.value = 'testpassword'
        
        # Set mocks
        self.set_backend_response(
            class_object=AuthService, 
            json_data=None, 
            status_code=500
        )
        self.skip_notify(class_object=login_card.__class__)
        self.skip_notify(class_object=login_page.__class__)
        
        # Simulates user hitting the submit button
        response = await login_page.call_rest_method()
        
        # Assert response
        assert response == _('no_response')
    
    async def test_login_fail_bad_request_400(self, user: User, login_page_components):
        """
        Verifies the response handling for a 400 Bad Request error.
        
        Ensures that field-specific errors returned by the API are correctly processed.
        """
        # Get components
        login_page, login_card = login_page_components
        
        # Set username and password
        login_card.username.value = 'testuser'
        login_card.password.value = 'testpassword'
        
        # Set mocks
        self.set_backend_response(
            class_object=AuthService, 
            json_data=LOGIN_RESPONSE_400_BAD_REQUEST, 
            status_code=requests.codes.bad_request
        )
        self.skip_notify(class_object=login_card.__class__)
        
        # Simulates user hitting the submit button
        response = await login_page.call_rest_method()
                
        # Assert response
        assert response.status_code == requests.codes.bad_request
        assert response.json() == LOGIN_RESPONSE_400_BAD_REQUEST
    
    async def test_login_fail_unauthorized_401(self, user: User, login_page_components):
        """
        Verifies handling of 401 Unauthorized errors (invalid credentials).
        """
        # Get components
        login_page, login_card = login_page_components
        
        # Set username and password
        login_card.username.value = 'testuser'
        login_card.password.value = 'testpassword'
        
        # Set mocks
        self.set_backend_response(
            class_object=AuthService, 
            json_data=LOGIN_RESPONSE_401_UNAUTHORIZED, 
            status_code=requests.codes.unauthorized
        )
        self.skip_notify(class_object=login_card.__class__)
        
        # Simulates user hitting the submit button
        response = await login_page.call_rest_method()
                
        # Assert response
        assert response.status_code == requests.codes.unauthorized
        assert response.json() == LOGIN_RESPONSE_401_UNAUTHORIZED
    
    async def test_login_fail_server_error_500(self, user: User, login_page_components):
        """
        Verifies handling of 500 Internal Server Errors from the backend.
        """
        # Get components
        login_page, login_card = login_page_components
        
        # Set username and password
        login_card.username.value = 'testuser'
        login_card.password.value = 'testpassword'
        
        # Set mocks
        self.set_backend_response(
            class_object=AuthService, 
            json_data=LOGIN_RESPONSE_500_SERVER_ERROR, 
            status_code=requests.codes.internal_server_error
        )
        self.skip_notify(class_object=login_card.__class__)
        
        # Simulates user hitting the submit button
        response = await login_page.call_rest_method()
                
        # Assert response
        assert response.status_code == requests.codes.internal_server_error
        assert response.json() == LOGIN_RESPONSE_500_SERVER_ERROR
    
    async def test_login_fail_validation_fails(self, user: User, login_page_components):
        """
        Verifies that form submission is blocked if frontend validation fails.
        """
        # Get components
        login_page, login_card = login_page_components
        
        # Set mocks
        self.skip_notify(class_object=login_card.__class__)
        
        # Simulates user hitting the submit button
        response = await login_page.call_rest_method()
        
        assert response == _('username_password_required')

    async def test_login_redirection_admin(self, user: User, login_page_components, mocker):
        """
        Verifies that an admin user is redirected to the stamps manager page upon successful login.
        """
        # Get components
        login_page, login_card = login_page_components
        
        # Set mocks
        self.set_backend_response(
            class_object=AuthService, 
            json_data=LOGIN_RESPONSE_200_SUCCESS, 
            status_code=requests.codes.ok
        )
        self.skip_notify(class_object=login_card.__class__)
        self.skip_notify(class_object=login_page.__class__)
        
        # Mock navigate and config
        mock_navigate = mocker.patch('nicegui.ui.navigate.to')
        mocker.patch('pages.auth.login_page.ConfigService.load_user_config')

        # Set valid credentials
        login_card.username.value = 'admin'
        login_card.password.value = 'password'
        
        # Execute login
        await login_page.call_rest_method()
        
        # Verify redirection to stamps manager (since is_admin is True in mock)
        mock_navigate.assert_called_with(URLs.Frontend.stamps_manager)

    async def test_login_redirection_user(self, user: User, login_page_components, mocker):
        """
        Verifies that a regular user is redirected to the collections page upon successful login.
        """
        # Get components
        login_page, login_card = login_page_components
        
        # Mock a non-admin response
        user_response = {
            "success": True,
            "data": {
                "token": "user-token",
                "payload": {
                    "user_id": 2,
                    "username": "regularuser",
                    "is_admin": False
                }
            }
        }
        
        self.set_backend_response(
            class_object=AuthService, 
            json_data=user_response, 
            status_code=requests.codes.ok
        )
        self.skip_notify(class_object=login_card.__class__)
        self.skip_notify(class_object=login_page.__class__)
        
        # Mock navigate and config
        mock_navigate = mocker.patch('nicegui.ui.navigate.to')
        mocker.patch('pages.auth.login_page.ConfigService.load_user_config')

        # Set valid credentials
        login_card.username.value = 'user'
        login_card.password.value = 'password'
        
        # Execute login
        await login_page.call_rest_method()
        
        # Verify redirection to collections (since is_admin is False)
        mock_navigate.assert_called_with(URLs.Frontend.collections)

    async def test_login_config_load_called(self, user: User, login_page_components, mocker):
        """
        Verifies that user configuration is synchronized from the backend after a successful login.
        """
        # Get components
        login_page, login_card = login_page_components
        
        # Set mocks
        self.set_backend_response(
            class_object=AuthService, 
            json_data=LOGIN_RESPONSE_200_SUCCESS, 
            status_code=requests.codes.ok
        )
        self.skip_notify(class_object=login_card.__class__)
        self.skip_notify(class_object=login_page.__class__)
        
        # Mock config load
        mock_load_config = mocker.patch('pages.auth.login_page.ConfigService.load_user_config')
        mocker.patch('nicegui.ui.navigate.to')

        # Set valid credentials
        login_card.username.value = 'testuser'
        login_card.password.value = 'password'
        
        # Execute login
        await login_page.call_rest_method()
        
        # Verify load_user_config was called
        mock_load_config.assert_called_once()
