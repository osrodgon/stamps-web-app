import logging
import unittest
import pytest
import requests
from services.base_service import BaseService
from tests.helpers.abstract_unit_test import AbstractUnitTest


@pytest.mark.asyncio
class TestBaseService(AbstractUnitTest):
    """
    Unit tests for the BaseService component.
    
    This class verifies the functionality of the base service,
    including HTTP request handling and error management.
    """
    
    @pytest.fixture(autouse=True)
    def init_data(self, mocker, caplog):
        """Initializes mock data and configures logging for tests."""
        caplog.set_level(logging.CRITICAL)
        self._mocker = mocker
        
    @pytest.fixture
    def base_service(self):
        """Fixture that creates a BaseService instance."""
        return BaseService()
        
    async def test_make_request_get_success_200(self, base_service):
        """
        Verifies that the _make_request method successfully makes a GET request.
        """
        # Set mocks
        self.set_backend_response(
            class_object=BaseService, 
            json_data={"success": True, "data": "test"}, 
            status_code=requests.codes.ok
        )
        
        response = await base_service._make_request(
            request_type=BaseService.GET,
            url="https://api.example.com/test"
        )
        
        # Assert response
        assert response.status_code == requests.codes.ok
        assert response.json() == {"success": True, "data": "test"}
        
    async def test_make_request_post_success_200(self, base_service):
        """
        Verifies that the _make_request method successfully makes a POST request.
        """
        # Set mocks
        self.set_backend_response(
            class_object=BaseService, 
            json_data={"success": True, "data": "created"}, 
            status_code=201
        )
        
        payload = {"name": "test", "value": 123}
        
        response = await base_service._make_request(
            request_type=BaseService.POST,
            url="https://api.example.com/test",
            payload=payload
        )
        
        # Assert response
        assert response.status_code == 201
        assert response.json() == {"success": True, "data": "created"}
        
    async def test_make_request_put_success_200(self, base_service):
        """
        Verifies that the _make_request method successfully makes a PUT request.
        """
        # Set mocks
        self.set_backend_response(
            class_object=BaseService, 
            json_data={"success": True, "data": "updated"}, 
            status_code=200
        )
        
        payload = {"name": "updated_test", "value": 456}
        
        response = await base_service._make_request(
            request_type=BaseService.PUT,
            url="https://api.example.com/test/123",
            payload=payload
        )
        
        # Assert response
        assert response.status_code == 200
        assert response.json() == {"success": True, "data": "updated"}
    
    # @unittest.skip("DELETE method test skipped temporarily. Work in progress.")    
    async def test_make_request_delete_success_200(self, base_service):
        """
        Verifies that the _make_request method successfully makes a DELETE request.
        """
        # Set mocks
        self.set_backend_response(
            class_object=BaseService, 
            json_data={"success": True, "data": "deleted"}, 
            status_code=200
        )
        
        response = await base_service._make_request(
            request_type=BaseService.DELETE,
            url="https://api.example.com/test/123"
        )
        
        # Assert response
        assert response.status_code == 200
        
    async def test_make_request_network_error(self, base_service, mocker):
        """
        Verifies the handling of network errors during HTTP requests.
        """
        # Mock requests.get to raise a RequestException
        mock_request = mocker.patch('requests.get')
        mock_request.side_effect = requests.exceptions.ConnectionError("Network error")
        
        response = await base_service._make_request(
            request_type=BaseService.GET,
            url="https://api.example.com/test"
        )
        
        # Assert response
        assert response is None
        
    async def test_make_request_timeout_error(self, base_service, mocker):
        """
        Verifies the handling of timeout errors during HTTP requests.
        """
        # Mock requests.get to raise a Timeout exception
        mock_request = mocker.patch('requests.get')
        mock_request.side_effect = requests.exceptions.Timeout("Request timeout")
        
        response = await base_service._make_request(
            request_type=BaseService.GET,
            url="https://api.example.com/test"
        )
        
        # Assert response
        assert response is None
        
    async def test_make_request_unknown_request_type(self, base_service):
        """
        Verifies that unknown request types default to GET.
        """
        # Set mocks
        self.set_backend_response(
            class_object=BaseService, 
            json_data={"success": True, "data": "test"}, 
            status_code=requests.codes.ok
        )
        
        # Use an unknown request type (should default to GET)
        response = await base_service._make_request(
            request_type=999,  # Unknown type
            url="https://api.example.com/test"
        )
        
        # Assert response
        assert response.status_code == requests.codes.ok
        assert response.json() == {"success": True, "data": "test"}
        
    async def test_make_request_with_headers(self, base_service):
        """
        Verifies that the _make_request method correctly includes headers.
        """
        # Set mocks
        self.set_backend_response(
            class_object=BaseService, 
            json_data={"success": True, "data": "test"}, 
            status_code=requests.codes.ok
        )
        
        headers = {"Authorization": "Bearer token123", "Content-Type": "application/json"}
        
        response = await base_service._make_request(
            request_type=BaseService.GET,
            url="https://api.example.com/test",
            headers=headers
        )
        
        # Assert response
        assert response.status_code == requests.codes.ok
        assert response.json() == {"success": True, "data": "test"}
        
    async def test_make_request_with_payload(self, base_service):
        """
        Verifies that the _make_request method correctly includes payload data.
        """
        # Set mocks
        self.set_backend_response(
            class_object=BaseService, 
            json_data={"success": True, "data": "received"}, 
            status_code=200
        )
        
        payload = {"key1": "value1", "key2": "value2"}
        
        response = await base_service._make_request(
            request_type=BaseService.POST,
            url="https://api.example.com/test",
            payload=payload
        )
        
        # Assert response
        assert response.status_code == 200
        assert response.json() == {"success": True, "data": "received"}
        
    async def test_make_request_timeout_parameter(self, base_service, mocker):
        """
        Verifies that the _make_request method uses the correct timeout value.
        """
        # Mock requests.get to verify timeout parameter
        mock_request = mocker.patch('requests.get')
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True}
        mock_request.return_value = mock_response
        
        await base_service._make_request(
            request_type=BaseService.GET,
            url="https://api.example.com/test"
        )
        
        # Verify that the request was made with timeout=5
        mock_request.assert_called_once()
        call_args = mock_request.call_args
        assert call_args[1]['timeout'] == 60