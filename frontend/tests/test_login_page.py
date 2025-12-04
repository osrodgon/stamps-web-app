import logging
import pytest
from nicegui.testing import User

from components.auth.login_card import LoginCard
from pages.auth.login_page import LoginPage
from tests.helpers.abstract_unit_test import AbstractUnitTest
from frontend.tests.data.users_api_responses import (
    LOGIN_RESPONSE_200_SUCCESS, 
    LOGIN_RESPONSE_200_SUCCESS_MISSING_TOKEN,
    LOGIN_RESPONSE_400_BAD_REQUEST,
    LOGIN_RESPONSE_401_UNAUTHORIZED,
    LOGIN_RESPONSE_500_SERVER_ERROR
)

@pytest.mark.asyncio
class TestLoginPage(AbstractUnitTest):
    @pytest.fixture(autouse=True)
    def init_data(self, mocker, caplog):
        caplog.set_level(logging.CRITICAL)
        self._AbstractUnitTest__mocker = mocker
        
    
    async def test_login_success_200(self, user: User, mocker):
        # Open login page
        login_object = await user.open('/login')
        
        # Get components
        login_card = self.get_component(login_object, LoginCard)
        login_page = self.get_component(login_object, LoginPage)
        
        # Set username and password
        login_card.username.value = 'testuser'
        login_card.password.value = 'testpassword'
        
        # Set mocks
        # self.set_card_valid(card=login_card.__class__, valid=True)
        self.set_backend_response(
            class_object=login_page.__class__, 
            json_data=LOGIN_RESPONSE_200_SUCCESS, 
            status_code=200
        )
        self.skip_notify(class_object=login_card.__class__)
        user_storage = self.create_user_storage(mocker)
        
        # Assert components
        assert login_card is not None
        assert login_page is not None
        
        # Simulates user hitting the submit button
        response = await login_page.call_rest_method()
        
        # Assert response
        assert response.status_code == 200
        assert response.json() == LOGIN_RESPONSE_200_SUCCESS
        assert user_storage['jwt_token'] == LOGIN_RESPONSE_200_SUCCESS['data']['token']
        
    async def test_login_success_200_missing_token(self, user: User):
        # Open login page
        login_object = await user.open('/login')
        
        # Get components
        login_card = self.get_component(login_object, LoginCard)
        login_page = self.get_component(login_object, LoginPage)
        
        # Set username and password
        login_card.username.value = 'testuser'
        login_card.password.value = 'testpassword'
        
        # Set mocks
        self.set_backend_response(
            class_object=login_page.__class__, 
            json_data=LOGIN_RESPONSE_200_SUCCESS_MISSING_TOKEN, 
            status_code=200
        )
        self.skip_notify(class_object=login_card.__class__)
        
        # Assert components
        assert login_card is not None
        assert login_page is not None
        
        # Simulates user hitting the submit button
        response = await login_page.call_rest_method()
        
        # Assert response
        assert response == "Login failed."
        
    async def test_login_fail_no_response(self, user: User):
        # Open login page
        login_object = await user.open('/login')
        
        # Get components
        login_card = self.get_component(login_object, LoginCard)
        login_page = self.get_component(login_object, LoginPage)
        
        # Set username and password
        login_card.username.value = 'testuser'
        login_card.password.value = 'testpassword'
        
        # Set mocks
        self.set_backend_response(
            class_object=login_page.__class__, 
            json_data=None, 
            status_code=500
        )
        self.skip_notify(class_object=login_card.__class__)
        self.skip_notify(class_object=login_page.__class__)
        
        # Assert components
        assert login_card is not None
        assert login_page is not None
        
        # Simulates user hitting the submit button
        response = await login_page.call_rest_method()
        
        # Assert response
        assert response == "Login request failed, no response from server."
    
    async def test_login_fail_bad_request_400(self, user: User):
        # Open login page
        login_object = await user.open('/login')
        
        # Get components
        login_card = self.get_component(login_object, LoginCard)
        login_page = self.get_component(login_object, LoginPage)
        
        # Set username and password
        login_card.username.value = 'testuser'
        login_card.password.value = 'testpassword'
        
        # Set mocks
        self.set_backend_response(
            class_object=login_page.__class__, 
            json_data=LOGIN_RESPONSE_400_BAD_REQUEST, 
            status_code=400
        )
        self.skip_notify(class_object=login_card.__class__)
        
        # Assert components
        assert login_card is not None
        assert login_page is not None
        
        # Simulates user hitting the submit button
        response = await login_page.call_rest_method()
                
        # Assert response
        assert response.status_code == 400
        assert response.json() == LOGIN_RESPONSE_400_BAD_REQUEST
    
    async def test_login_fail_unauthorized_401(self, user: User):
        # Open login page
        login_object = await user.open('/login')
        
        # Get components
        login_card = self.get_component(login_object, LoginCard)
        login_page = self.get_component(login_object, LoginPage)
        
        # Set username and password
        login_card.username.value = 'testuser'
        login_card.password.value = 'testpassword'
        
        # Set mocks
        self.set_backend_response(
            class_object=login_page.__class__, 
            json_data=LOGIN_RESPONSE_401_UNAUTHORIZED, 
            status_code=401
        )
        self.skip_notify(class_object=login_card.__class__)
        
        # Assert components
        assert login_card is not None
        assert login_page is not None
        
        # Simulates user hitting the submit button
        response = await login_page.call_rest_method()
                
        # Assert response
        assert response.status_code == 401
        assert response.json() == LOGIN_RESPONSE_401_UNAUTHORIZED
    
    async def test_login_fail_server_error_500(self, user: User):
        # Open login page
        login_object = await user.open('/login')
        
        # Get components
        login_card = self.get_component(login_object, LoginCard)
        login_page = self.get_component(login_object, LoginPage)
        
        # Set username and password
        login_card.username.value = 'testuser'
        login_card.password.value = 'testpassword'
        
        # Set mocks
        self.set_backend_response(
            class_object=login_page.__class__, 
            json_data=LOGIN_RESPONSE_500_SERVER_ERROR, 
            status_code=500
        )
        self.skip_notify(class_object=login_card.__class__)
        
        # Assert components
        assert login_card is not None
        assert login_page is not None
        
        # Simulates user hitting the submit button
        response = await login_page.call_rest_method()
                
        # Assert response
        assert response.status_code == 500
        assert response.json() == LOGIN_RESPONSE_500_SERVER_ERROR
    
    async def test_login_fail_validation_fails(self, user: User):
        # Open login page
        login_object = await user.open('/login')
        
        # Get components
        login_card = self.get_component(login_object, LoginCard)
        login_page = self.get_component(login_object, LoginPage)
        
        # Set mocks
        self.skip_notify(class_object=login_card.__class__)
        
        # Assert components
        assert login_card is not None
        assert login_page is not None
        
        # Simulates user hitting the submit button
        response = await login_page.call_rest_method()
        
        assert response == "Username and password are required."