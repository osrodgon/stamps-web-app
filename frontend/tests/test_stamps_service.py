import logging
import pytest
import requests
from core.urls import URLs
from services.stamps_service import StampsService
from tests.helpers.abstract_unit_test import AbstractUnitTest

from tests.data.stamps_api_responses import (
    YEARS_RESPONSE_200_SUCCESS,
    ISSUES_RESPONSE_200_SUCCESS,
    PRINT_TYPES_RESPONSE_200_SUCCESS,
    STAMP_TYPES_RESPONSE_200_SUCCESS,
    STAMPS_RESPONSE_200_SUCCESS
)


@pytest.mark.asyncio
class TestStampsService(AbstractUnitTest):
    """
    Unit tests for the StampsService component.
    
    This class verifies the functionality of the stamp database API service,
    including fetching years, issues, print types, stamp types, and individual stamps.
    """
    
    @pytest.fixture(autouse=True)
    def init_data(self, mocker, caplog):
        """Initializes mock data and configures logging for tests."""
        caplog.set_level(logging.CRITICAL)
        self._mocker = mocker
        
    @pytest.fixture
    def stamps_service(self):
        """Fixture that creates a StampsService instance."""
        return StampsService()
        
    async def test_get_years_success_200(self, stamps_service):
        """
        Verifies that the get_years method successfully fetches available years.
        
        Tests that:
        1. A successful 200 OK response is returned from the backend.
        2. The response contains the expected years data structure.
        """
        # Set mocks
        self.set_backend_response(
            class_object=StampsService, 
            json_data=YEARS_RESPONSE_200_SUCCESS, 
            status_code=requests.codes.ok
        )
        
        response = await stamps_service.get_years()
        
        # Assert response
        assert response.status_code == requests.codes.ok
        assert response.json() == YEARS_RESPONSE_200_SUCCESS
        
    async def test_get_years_fail_no_response(self, stamps_service):
        """
        Verifies the handling of a get_years request when the backend fails to respond.
        """
        # Set mocks
        self.set_backend_response(
            class_object=StampsService, 
            json_data=None, 
            status_code=500
        )
        
        response = await stamps_service.get_years()
        
        # Assert response
        assert response is None
    
    async def test_get_issues_success_200_no_filters(self, stamps_service):
        """
        Verifies that get_issues works correctly without any filters.
        """
        # Set mocks
        self.set_backend_response(
            class_object=StampsService, 
            json_data=ISSUES_RESPONSE_200_SUCCESS, 
            status_code=requests.codes.ok
        )
        
        response = await stamps_service.get_issues()
        
        # Assert response
        assert response.status_code == requests.codes.ok
        assert response.json() == ISSUES_RESPONSE_200_SUCCESS
        
    async def test_get_issues_success_200_with_year_filter(self, stamps_service):
        """
        Verifies that get_issues works correctly with a year filter.
        """
        # Set mocks
        self.set_backend_response(
            class_object=StampsService, 
            json_data=ISSUES_RESPONSE_200_SUCCESS, 
            status_code=requests.codes.ok
        )
        
        response = await stamps_service.get_issues(year=1950)
        
        # Assert response
        assert response.status_code == requests.codes.ok
        assert response.json() == ISSUES_RESPONSE_200_SUCCESS
        
    async def test_get_issues_success_200_with_series_filter(self, stamps_service):
        """
        Verifies that get_issues works correctly with a series name filter.
        """
        # Set mocks
        self.set_backend_response(
            class_object=StampsService, 
            json_data=ISSUES_RESPONSE_200_SUCCESS, 
            status_code=requests.codes.ok
        )
        
        response = await stamps_service.get_issues(series_name="Test Series")
        
        # Assert response
        assert response.status_code == requests.codes.ok
        assert response.json() == ISSUES_RESPONSE_200_SUCCESS
        
    async def test_get_issues_success_200_with_both_filters(self, stamps_service):
        """
        Verifies that get_issues works correctly with both year and series filters.
        """
        # Set mocks
        self.set_backend_response(
            class_object=StampsService, 
            json_data=ISSUES_RESPONSE_200_SUCCESS, 
            status_code=requests.codes.ok
        )
        
        response = await stamps_service.get_issues(year=1950, series_name="Test Series")
        
        # Assert response
        assert response.status_code == requests.codes.ok
        assert response.json() == ISSUES_RESPONSE_200_SUCCESS
        
    async def test_get_issues_fail_no_response(self, stamps_service):
        """
        Verifies the handling of a get_issues request when the backend fails to respond.
        """
        # Set mocks
        self.set_backend_response(
            class_object=StampsService, 
            json_data=None, 
            status_code=500
        )
        
        response = await stamps_service.get_issues()
        
        # Assert response
        assert response is None
    
    async def test_get_print_types_success_200(self, stamps_service):
        """
        Verifies that the get_print_types method successfully fetches available print types.
        """
        # Set mocks
        self.set_backend_response(
            class_object=StampsService, 
            json_data=PRINT_TYPES_RESPONSE_200_SUCCESS, 
            status_code=requests.codes.ok
        )
        
        response = await stamps_service.get_print_types()
        
        # Assert response
        assert response.status_code == requests.codes.ok
        assert response.json() == PRINT_TYPES_RESPONSE_200_SUCCESS
        
    async def test_get_print_types_fail_no_response(self, stamps_service):
        """
        Verifies the handling of a get_print_types request when the backend fails to respond.
        """
        # Set mocks
        self.set_backend_response(
            class_object=StampsService, 
            json_data=None, 
            status_code=500
        )
        
        response = await stamps_service.get_print_types()
        
        # Assert response
        assert response is None
    
    async def test_get_stamp_types_success_200(self, stamps_service):
        """
        Verifies that the get_stamp_types method successfully fetches available stamp types.
        """
        # Set mocks
        self.set_backend_response(
            class_object=StampsService, 
            json_data=STAMP_TYPES_RESPONSE_200_SUCCESS, 
            status_code=requests.codes.ok
        )
        
        response = await stamps_service.get_stamp_types()
        
        # Assert response
        assert response.status_code == requests.codes.ok
        assert response.json() == STAMP_TYPES_RESPONSE_200_SUCCESS
        
    async def test_get_stamp_types_fail_no_response(self, stamps_service):
        """
        Verifies the handling of a get_stamp_types request when the backend fails to respond.
        """
        # Set mocks
        self.set_backend_response(
            class_object=StampsService, 
            json_data=None, 
            status_code=500
        )
        
        response = await stamps_service.get_stamp_types()
        
        # Assert response
        assert response is None
    
    async def test_get_stamps_success_200(self, stamps_service):
        """
        Verifies that the get_stamps method successfully fetches stamps for a specific issue.
        """
        # Set mocks
        self.set_backend_response(
            class_object=StampsService, 
            json_data=STAMPS_RESPONSE_200_SUCCESS, 
            status_code=requests.codes.ok
        )
        
        response = await stamps_service.get_stamps(issue_id=123)
        
        # Assert response
        assert response.status_code == requests.codes.ok
        assert response.json() == STAMPS_RESPONSE_200_SUCCESS
        
    async def test_get_stamps_fail_no_response(self, stamps_service):
        """
        Verifies the handling of a get_stamps request when the backend fails to respond.
        """
        # Set mocks
        self.set_backend_response(
            class_object=StampsService, 
            json_data=None, 
            status_code=500
        )
        
        response = await stamps_service.get_stamps(issue_id=123)
        
        # Assert response
        assert response is None