import logging
import asyncio
import pytest
import requests
from components.auth.signup_card import SignUpCard
from core.translations import _
from core.urls import URLs
from nicegui.testing import User
from pages.auth.signup_page import SignUpPage
from services.auth_service import AuthService
from tests.helpers.abstract_unit_test import AbstractUnitTest

from tests.data.users_api_responses import (
    SIGNUP_RESPONSE_201_SUCCESS, SIGNUP_RESPONSE_400_FAIL
)


@pytest.mark.asyncio
class TestSignUpPage(AbstractUnitTest):
    """
    Unit tests for the SignUpPage component.
    
    This class contains tests to verify the functionality of the user registration 
    process, including successful signup, validation handling, and error scenarios.
    """
    
    @pytest.fixture(autouse=True)
    def init_data(self, mocker, caplog):
        """Initializes mock data and configures logging for tests."""
        caplog.set_level(logging.CRITICAL)
        self._mocker = mocker
        
    @pytest.fixture
    async def signup_page_components(self, user: User):
        """
        Fixture that opens the signup page and retrieves key components.
        
        Args:
            user (User): The NiceGUI testing user instance.
            
        Returns:
            tuple: A tuple containing (signup_page, signup_card).
        """
        signup_object = await user.open(URLs.Frontend.signup)
        signup_card = self.get_component(signup_object, SignUpCard)
        signup_page = self.get_component(signup_object, SignUpPage)
        
        assert signup_card is not None
        assert signup_page is not None
        yield signup_page, signup_card
        
    async def test_signup_success_201(self, user: User, signup_page_components, mocker):
        """
        Verifies that a user can successfully sign up when providing valid information.
        
        Tests the flow:
        1. Fill in registration form details.
        2. Mock a successful 201 Created response from the backend.
        3. Assert that the signup process completes successfully.
        """
        # Get components
        signup_page, signup_card = signup_page_components
        
        # Set form data
        signup_card.name_input.value = 'John'
        signup_card.last_name_input.value = 'Doe'
        signup_card.username_input.value = 'johndoe'
        signup_card.email_input.value = 'john@example.com'
        signup_card.password_input.value = 'Password123!'
        signup_card.confirm_password_input.value = 'Password123!'
        
        # Set mocks
        self.set_backend_response(
            class_object=AuthService, 
            json_data=SIGNUP_RESPONSE_201_SUCCESS, 
            status_code=201
        )
        self.skip_notify(class_object=signup_page.__class__)
        
        # Simulate signup
        # Note: In SignUpPage.call_rest_method, there is an asyncio.sleep(3)
        # We mock sleep to speed up tests execution.
        mocker.patch('asyncio.sleep', return_value=None)
        
        response = await signup_page.call_rest_method()
        
        # Assert response
        assert response.status_code == 201
        assert response.json() == SIGNUP_RESPONSE_201_SUCCESS
        
    async def test_signup_fail_validation(self, user: User, signup_page_components):
        """
        Verifies that the signup process fails when frontend validation rules are not met.
        
        Tests that an appropriate error message is returned when the form is submitted 
        without the required data.
        """
        # Get components
        signup_page, signup_card = signup_page_components
        
        # Leave fields empty
        self.skip_notify(class_object=signup_card.__class__)
        
        response = await signup_page.call_rest_method()
        
        assert response == _('review_form_data')
        
    async def test_signup_fail_backend_error_400(self, user: User, signup_page_components):
        """
        Verifies that backend error responses (e.g., username taken) are correctly handled.
        
        Ensures that the application properly displays errors returned by the API 
        during the signup attempt.
        """
        # Get components
        signup_page, signup_card = signup_page_components
        
        # Set form data (valid enough for frontend validation)
        signup_card.name_input.value = 'John'
        signup_card.last_name_input.value = 'Doe'
        signup_card.username_input.value = 'existinguser'
        signup_card.email_input.value = 'john@example.com'
        signup_card.password_input.value = 'Password123!'
        signup_card.confirm_password_input.value = 'Password123!'
        
        # Set mocks
        self.set_backend_response(
            class_object=AuthService, 
            json_data=SIGNUP_RESPONSE_400_FAIL, 
            status_code=400
        )
        self.skip_notify(class_object=signup_card.__class__)
        
        response = await signup_page.call_rest_method()
        
        assert response.status_code == 400
        assert response.json() == SIGNUP_RESPONSE_400_FAIL
        
    async def test_signup_fail_no_response(self, user: User, signup_page_components):
        """
        Verifies the handling of scenarios where the backend fails to provide a response.
        
        Tests that the user is notified with a 'no response' message when the API call 
        encounters a failure.
        """
        # Get components
        signup_page, signup_card = signup_page_components
        
        # Set form data
        signup_card.name_input.value = 'John'
        signup_card.password_input.value = 'Password123!'
        signup_card.confirm_password_input.value = 'Password123!'
        
        # Mock validation to pass if we want to skip it, or fill all fields
        signup_card.last_name_input.value = 'Doe'
        signup_card.username_input.value = 'johndoe'
        signup_card.email_input.value = 'john@example.com'
        
        # Set mocks
        self.set_backend_response(
            class_object=AuthService, 
            json_data=None, 
            status_code=500
        )
        self.skip_notify(class_object=signup_page.__class__)
        
        response = await signup_page.call_rest_method()
        
        assert response == _('no_response')

    async def test_back_to_login(self, user: User, signup_page_components, mocker):
        """
        Verifies that the 'back to login' functionality correctly redirects the user.
        
        Ensures that clicking the cancel/back button navigates the user back to 
        the login page.
        """
        # Get components
        signup_page, signup_card = signup_page_components
        
        # Mock navigate.to
        mock_navigate = mocker.patch('nicegui.ui.navigate.to')
        
        signup_page.back_to_login()
        
        mock_navigate.assert_called_once_with(URLs.Frontend.login)
