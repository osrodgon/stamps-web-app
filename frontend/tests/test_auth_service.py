import logging
import pytest
import requests
from core.urls import URLs
from services.auth_service import AuthService
from tests.helpers.abstract_unit_test import AbstractUnitTest

from tests.data.users_api_responses import (
    LOGIN_RESPONSE_200_SUCCESS,
    SIGNUP_RESPONSE_201_SUCCESS,
    LOGIN_RESPONSE_400_BAD_REQUEST,
    SIGNUP_RESPONSE_400_FAIL
)


@pytest.mark.asyncio
class TestAuthService(AbstractUnitTest):
    """
    Unit tests for the AuthService component.
    
    This class verifies the functionality of the authentication service,
    including login and signup operations.
    """
    
    @pytest.fixture(autouse=True)
    def init_data(self, mocker, caplog):
        """Initializes mock data and configures logging for tests."""
        caplog.set_level(logging.CRITICAL)
        self._mocker = mocker
        
    @pytest.fixture
    def auth_service(self):
        """Fixture that creates an AuthService instance."""
        return AuthService()
        
    async def test_login_success_200(self, auth_service):
        """
        Verifies that the login method successfully authenticates a user.
        """
        # Set mocks
        self.set_backend_response(
            class_object=AuthService, 
            json_data=LOGIN_RESPONSE_200_SUCCESS, 
            status_code=requests.codes.ok
        )
        
        payload = {
            'username': 'testuser',
            'password': 'testpassword'
        }
        
        response = await auth_service.login(payload)
        
        # Assert response
        assert response.status_code == requests.codes.ok
        assert response.json() == LOGIN_RESPONSE_200_SUCCESS
        
    async def test_login_fail_no_response(self, auth_service):
        """
        Verifies the handling of a login request when the backend fails to respond.
        """
        # Set mocks
        self.set_backend_response(
            class_object=AuthService, 
            json_data=None, 
            status_code=500
        )
        
        payload = {
            'username': 'testuser',
            'password': 'testpassword'
        }
        
        response = await auth_service.login(payload)
        
        # Assert response
        assert response is None
    
    async def test_login_fail_bad_request_400(self, auth_service):
        """
        Verifies the response handling for a 400 Bad Request error.
        """
        # Set mocks
        self.set_backend_response(
            class_object=AuthService, 
            json_data=LOGIN_RESPONSE_400_BAD_REQUEST, 
            status_code=requests.codes.bad_request
        )
        
        payload = {
            'username': 'testuser',
            'password': 'testpassword'
        }
        
        response = await auth_service.login(payload)
        
        # Assert response
        assert response.status_code == requests.codes.bad_request
        assert response.json() == LOGIN_RESPONSE_400_BAD_REQUEST
        
    async def test_signup_success_201(self, auth_service):
        """
        Verifies that the signup method successfully creates a new user.
        """
        # Set mocks
        self.set_backend_response(
            class_object=AuthService, 
            json_data=SIGNUP_RESPONSE_201_SUCCESS, 
            status_code=201
        )
        
        payload = {
            'name': 'John',
            'last_name': 'Doe',
            'username': 'johndoe',
            'email': 'john@example.com',
            'password': 'Password123!'
        }
        
        response = await auth_service.signup(payload)
        
        # Assert response
        assert response.status_code == 201
        assert response.json() == SIGNUP_RESPONSE_201_SUCCESS
        
    async def test_signup_fail_no_response(self, auth_service):
        """
        Verifies the handling of a signup request when the backend fails to respond.
        """
        # Set mocks
        self.set_backend_response(
            class_object=AuthService, 
            json_data=None, 
            status_code=500
        )
        
        payload = {
            'name': 'John',
            'last_name': 'Doe',
            'username': 'johndoe',
            'email': 'john@example.com',
            'password': 'Password123!'
        }
        
        response = await auth_service.signup(payload)
        
        # Assert response
        assert response is None
    
    async def test_signup_fail_bad_request_400(self, auth_service):
        """
        Verifies the response handling for a 400 Bad Request error during signup.
        """
        # Set mocks
        self.set_backend_response(
            class_object=AuthService, 
            json_data=SIGNUP_RESPONSE_400_FAIL, 
            status_code=400
        )
        
        payload = {
            'name': 'John',
            'last_name': 'Doe',
            'username': 'johndoe',
            'email': 'john@example.com',
            'password': 'Password123!'
        }
        
        response = await auth_service.signup(payload)
        
        # Assert response
        assert response.status_code == 400
        assert response.json() == SIGNUP_RESPONSE_400_FAIL