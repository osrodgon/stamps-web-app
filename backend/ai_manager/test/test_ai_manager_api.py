import re
import pytest
from rest_framework import status
from unittest.mock import Mock, patch

from _backend.settings import AI_URL_V1
from common.api.messages import Messages
from common.test.abstract_api_unit_test import AbstractApiUnitTest
from common.test.api_client import api_client
from common.test.ai_manager_api_test_data import (
    research_request_payload_ok,
    research_request_payload_minimal,
    research_request_payload_invalid,
    research_response_data
)

from ai_manager.api.serializers.research_response_serializer import ResearchResponseSerializer
from ai_manager.services.stamp_research_service import StampResearchService


class TestAImanagerAPI(AbstractApiUnitTest):
    """Test class for AI Manager API endpoints (No Database)."""
    
    def test_post_research_series_returns_200_ok(
        self, 
        api_client, 
        research_request_payload_ok, 
        research_response_data
    ):
        """Test successful research request returns 200 OK."""
        self.permission(granted=True)
        
        # Mock the AI service response
        mock_service = Mock()
        mock_service.research_series.return_value = research_response_data
        
        with patch('ai_manager.api.views.research_series_view.StampResearchService', return_value=mock_service):
            response = api_client.post(self.__get_url(), research_request_payload_ok, format='json')

        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.success()
        assert response.json()['errors'] == None
        assert response.json()['data']['confidence_score'] == 95
        assert response.json()['data']['description'] == "Castillos de España series"
        assert response.status_code == status.HTTP_200_OK
        
        # Verify service was called with correct parameters
        mock_service.research_series.assert_called_once_with(
            issue_name="Castillos",
            issue_date="2007-09-10", 
            edifil_start_number="4349"
        )
        
    def test_post_research_series_minimal_payload_returns_200_ok(
        self, 
        api_client, 
        research_request_payload_minimal, 
        research_response_data
    ):
        """Test research request with minimal payload (optional field omitted) returns 200 OK."""
        self.permission(granted=True)
        
        mock_service = Mock()
        mock_service.research_series.return_value = research_response_data
        
        with patch('ai_manager.api.views.research_series_view.StampResearchService', return_value=mock_service):
            response = api_client.post(self.__get_url(), research_request_payload_minimal, format='json')

        assert response.json()['success'] == True
        assert response.status_code == status.HTTP_200_OK
        
        # Verify service was called with None for optional field
        mock_service.research_series.assert_called_once_with(
            issue_name="Navidad",
            issue_date="1978-12-22",
            edifil_start_number=None
        )
        
    def test_post_research_series_returns_400_missing_required_field(
        self, 
        api_client, 
        research_request_payload_invalid
    ):
        """Test research request with missing required field returns 400 Bad Request."""
        self.permission(granted=True)
        del research_request_payload_invalid["issue_name"]  # Remove required field
        
        response = api_client.post(self.__get_url(), research_request_payload_invalid, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['errors'][0]['field'] == 'issue_name'
        assert response.json()['errors'][0]['message'] == Messages.field_required()
        assert response.json()['errors'][0]['code'] == Messages.Code.required()
        assert response.json()['data'] == None
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
    def test_post_research_series_returns_400_invalid_field(
        self, 
        api_client, 
        research_request_payload_ok
    ):
        """Test research request with invalid field returns 400 Bad Request."""
        self.permission(granted=True)
        research_request_payload_ok['new_field'] = 'new_value'  # Add invalid field
        
        response = api_client.post(self.__get_url(), research_request_payload_ok, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['errors'][0]['field'] == 'new_field'
        assert response.json()['errors'][0]['message'] == Messages.field_not_allowed()
        assert response.json()['errors'][0]['code'] == Messages.Code.invalid()
        assert response.json()['data'] == None
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
    def test_post_research_series_returns_403_header_missing(
        self, 
        api_client
    ):
        """Test research request without authentication header returns 403 Forbidden."""
        response = api_client.post(self.__get_url())

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.header_missing()
        assert response.json()['errors'][0]['code'] == Messages.Code.authentication_failed()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_post_research_series_returns_403_invalid_api_key(
        self, 
        api_client, 
        research_request_payload_ok
    ):
        """Test research request with invalid API key returns 403 Forbidden."""
        self.permission(granted=False, message=Messages.Auth.invalid_api_key())
        
        response = api_client.post(self.__get_url(), research_request_payload_ok, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == "detail"
        assert response.json()['errors'][0]['message'] == Messages.Auth.invalid_api_key()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
    def test_post_research_series_returns_403_not_enough_rights(
        self, 
        api_client, 
        research_request_payload_ok
    ):
        """Test research request without sufficient rights returns 403 Forbidden."""
        self.permission(granted=False, message=Messages.Auth.not_enough_rights())
        
        response = api_client.post(self.__get_url(), research_request_payload_ok, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == "detail"
        assert response.json()['errors'][0]['message'] == Messages.Auth.not_enough_rights()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_post_research_series_returns_500_service_error(
        self, 
        api_client, 
        research_request_payload_ok
    ):
        """Test research request when AI service fails returns 500 Internal Server Error."""
        self.permission(granted=True)
        
        # Mock service to raise an exception
        mock_service = Mock()
        mock_service.research_series.side_effect = Exception("AI service unavailable")
        
        with patch('ai_manager.api.views.research_series_view.StampResearchService', return_value=mock_service):
            response = api_client.post(self.__get_url(), research_request_payload_ok, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.AI.unavailable()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['message'] == Messages.AI.error()
        assert response.json()['errors'][0]['code'] == Messages.Code.other()
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_post_research_series_returns_422_ai_validation_error(
        self, 
        api_client, 
        research_request_payload_ok
    ):
        """Test research request when AI returns invalid data returns 422 Unprocessable Entity."""
        self.permission(granted=True)
        
        # Mock service to return invalid data
        mock_service = Mock()
        mock_service.research_series.return_value = {"invalid": "data"}  # Missing required fields
        
        with patch('ai_manager.api.views.research_series_view.StampResearchService', return_value=mock_service):
            response = api_client.post(self.__get_url(), research_request_payload_ok, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.AI.response_format_error()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'confidence_score'
        assert response.json()['errors'][0]['message'] == Messages.field_required()
        assert response.json()['errors'][0]['code'] == Messages.Code.required()
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
    def test_post_research_series_returns_422_ai_value_error(
        self, 
        api_client, 
        research_request_payload_ok
    ):
        """Test research request when AI validation fails returns 422 Unprocessable Entity."""
        self.permission(granted=True)
        
        # Mock service to raise ValueError
        mock_service = Mock()
        mock_service.research_series.side_effect = ValueError(Messages.failed())
        
        with patch('ai_manager.api.views.research_series_view.StampResearchService', return_value=mock_service):
            response = api_client.post(self.__get_url(), research_request_payload_ok, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == None
        assert response.json()['errors'][0]['message'] == Messages.AI.validation_error()
        assert response.json()['errors'][0]['code'] == Messages.Code.other()
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def __get_url(self):
        """Get the base URL for AI Manager API endpoints."""
        return f"/{AI_URL_V1}"