from rest_framework import status
from unittest.mock import Mock, patch

from _backend.settings import AI_ISSUES_EXTRACTION_URL_V1
from common.api.messages import Messages
from common.test.abstract_api_unit_test import AbstractApiUnitTest
from common.test.api_client import api_client
from common.test.ai_api_test_data import (
    series_extraction_request_payload_ok,
    series_extraction_request_payload_invalid,
    series_extraction_response_data,
    series_extraction_cleaned_data
)

from ai_api.api.serializers.series_extraction_response_serializer import SeriesExtractionResponseSerializer
from ai_api.services.llm_service import LLMService


class TestSeriesExtractionAPI(AbstractApiUnitTest):
    """Test class for AI Manager API endpoints (No Database)."""
    
    def test_post_series_extraction_returns_200_ok(
        self, 
        api_client, 
        series_extraction_request_payload_ok, 
        series_extraction_response_data,
        series_extraction_cleaned_data
    ):
        """Test successful extraction request returns 200 OK."""
        self.permission(granted=True)
        
        # Mock the AI service response
        mock_search_service = Mock()
        mock_search_service.find_series_url.return_value = "some test value for search"
        
        mock_scraping_service = Mock()
        mock_scraping_service.extract_links.return_value = "some test value for scrape links"
        mock_scraping_service.scrape_content.return_value = "some test value for scrape data"
        mock_scraping_service.clean_scraped_data.return_value = series_extraction_cleaned_data
        
        mock_service = Mock()
        mock_service.series_extract.return_value = series_extraction_response_data
        
        with patch('ai_api.api.views.series_extraction_view.SearchService', return_value=mock_search_service), \
            patch('ai_api.api.views.series_extraction_view.ScrapingService', return_value=mock_scraping_service), \
            patch('ai_api.api.views.series_extraction_view.LLMService', return_value=mock_service):
            response = api_client.post(self.__get_url(), series_extraction_request_payload_ok, format='json')

        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.success()
        assert response.json()['errors'] == None
        assert response.json()['data']['description'] == "Castillos de España series"
        assert response.status_code == status.HTTP_200_OK
        
        # Verify service was called with correct parameters
        mock_service.series_extract.assert_called_once_with(
            name="Castillos",
            date="2007-09-10",
            clean_data=str(series_extraction_cleaned_data)
        )
        
    def test_post_series_extraction_returns_400_missing_required_field(
        self, 
        api_client, 
        series_extraction_request_payload_invalid
    ):
        """Test series extraction request with missing required field returns 400 Bad Request."""
        self.permission(granted=True)
        del series_extraction_request_payload_invalid["name"]  # Remove required field
        
        response = api_client.post(self.__get_url(), series_extraction_request_payload_invalid, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['errors'][0]['field'] == 'name'
        assert response.json()['errors'][0]['message'] == Messages.field_required()
        assert response.json()['errors'][0]['code'] == Messages.Code.required()
        assert response.json()['data'] == None
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
    def test_post_series_extraction_returns_400_invalid_field(
        self, 
        api_client, 
        series_extraction_request_payload_ok
    ):
        """Test series extraction request with invalid field returns 400 Bad Request."""
        self.permission(granted=True)
        series_extraction_request_payload_ok['new_field'] = 'new_value'  # Add invalid field
        
        response = api_client.post(self.__get_url(), series_extraction_request_payload_ok, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['errors'][0]['field'] == 'new_field'
        assert response.json()['errors'][0]['message'] == Messages.field_not_allowed()
        assert response.json()['errors'][0]['code'] == Messages.Code.invalid()
        assert response.json()['data'] == None
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
    def test_post_series_extraction_returns_403_header_missing(
        self, 
        api_client
    ):
        """Test series extraction request without authentication header returns 403 Forbidden."""
        response = api_client.post(self.__get_url())

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.header_missing()
        assert response.json()['errors'][0]['code'] == Messages.Code.authentication_failed()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_post_series_extraction_returns_403_invalid_api_key(
        self, 
        api_client, 
        series_extraction_request_payload_ok
    ):
        """Test series extraction request with invalid API key returns 403 Forbidden."""
        self.permission(granted=False, message=Messages.Auth.invalid_api_key())
        
        response = api_client.post(self.__get_url(), series_extraction_request_payload_ok, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == "detail"
        assert response.json()['errors'][0]['message'] == Messages.Auth.invalid_api_key()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
    def test_post_series_extraction_returns_403_not_enough_rights(
        self, 
        api_client, 
        series_extraction_request_payload_ok
    ):
        """Test series extraction request without sufficient rights returns 403 Forbidden."""
        self.permission(granted=False, message=Messages.Auth.not_enough_rights())
        
        response = api_client.post(self.__get_url(), series_extraction_request_payload_ok, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == "detail"
        assert response.json()['errors'][0]['message'] == Messages.Auth.not_enough_rights()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_post_series_extraction_returns_500_service_error(
        self, 
        api_client, 
        series_extraction_request_payload_ok
    ):
        """Test series extraction request when AI service fails returns 500 Internal Server Error."""
        self.permission(granted=True)
        
        # Mock services to raise an exception
        mock_search_service = Mock()
        mock_search_service.find_series_url.return_value = "some test value for search"
        
        mock_scraping_service = Mock()
        mock_scraping_service.extract_links.return_value = "some test value for scrape links"
        mock_scraping_service.scrape_content.return_value = "some test value for scrape data"
        mock_scraping_service.clean_scraped_data.return_value = "some test value for clean data"
        
        mock_llm_service = Mock()
        mock_llm_service.series_extract.side_effect = Exception(Messages.AI.error())
        
        with patch('ai_api.api.views.series_extraction_view.SearchService', return_value=mock_search_service), \
            patch('ai_api.api.views.series_extraction_view.ScrapingService', return_value=mock_scraping_service), \
            patch('ai_api.api.views.series_extraction_view.LLMService', return_value=mock_llm_service):
            
            response = api_client.post(self.__get_url(), series_extraction_request_payload_ok, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.AI.unavailable()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['message'] == Messages.AI.error()
        assert response.json()['errors'][0]['code'] == Messages.Code.other()
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_post_series_extraction_returns_422_ai_validation_error(
        self, 
        api_client, 
        series_extraction_request_payload_ok,
        series_extraction_cleaned_data
    ):
        """Test series extraction request when AI returns invalid data returns 422 Unprocessable Entity."""
        self.permission(granted=True)
        
        # Mock service to return invalid data
        mock_search_service = Mock()
        mock_search_service.find_series_url.return_value = "some test value for search"
        
        mock_scraping_service = Mock()
        mock_scraping_service.extract_links.return_value = "some test value for scrape links"
        mock_scraping_service.scrape_content.return_value = "some test value for scrape data"
        mock_scraping_service.clean_scraped_data.return_value = series_extraction_cleaned_data
        
        mock_llm_service = Mock()
        mock_llm_service.series_extract.return_value = {"invalid": "data"}  # Missing required fields
        
        with patch('ai_api.api.views.series_extraction_view.SearchService', return_value=mock_search_service), \
            patch('ai_api.api.views.series_extraction_view.ScrapingService', return_value=mock_scraping_service), \
            patch('ai_api.api.views.series_extraction_view.LLMService', return_value=mock_llm_service):
            
            response = api_client.post(self.__get_url(), series_extraction_request_payload_ok, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.AI.response_format_error()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'issue_name'
        assert response.json()['errors'][0]['message'] == Messages.field_required()
        assert response.json()['errors'][0]['code'] == Messages.Code.required()
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
    def test_post_series_extraction_returns_422_ai_value_error(
        self, 
        api_client, 
        series_extraction_request_payload_ok,
        series_extraction_cleaned_data
    ):
        """Test series extraction request when AI validation fails returns 422 Unprocessable Entity."""
        self.permission(granted=True)
        
        # Mock service to raise ValueError
        mock_search_service = Mock()
        mock_search_service.find_series_url.return_value = "some test value for search"
        
        mock_scraping_service = Mock()
        mock_scraping_service.extract_links.return_value = "some test value for scrape links"
        mock_scraping_service.scrape_content.return_value = "some test value for scrape data"
        mock_scraping_service.clean_scraped_data.return_value = series_extraction_cleaned_data
        
        mock_llm_service = Mock()
        mock_llm_service.series_extract.side_effect = ValueError(Messages.failed())
        
        with patch('ai_api.api.views.series_extraction_view.SearchService', return_value=mock_search_service), \
            patch('ai_api.api.views.series_extraction_view.ScrapingService', return_value=mock_scraping_service), \
            patch('ai_api.api.views.series_extraction_view.LLMService', return_value=mock_llm_service):
            response = api_client.post(self.__get_url(), series_extraction_request_payload_ok, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == None
        assert response.json()['errors'][0]['message'] == Messages.AI.validation_error()
        assert response.json()['errors'][0]['code'] == Messages.Code.other()
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_post_series_extraction_with_url_and_zero_date_skips_search(
        self, 
        api_client, 
        series_extraction_response_data,
        series_extraction_cleaned_data
    ):
        """Test that providing a URL with date=0 skips search service and uses URL directly."""
        self.permission(granted=True)
        
        # Mock the AI service response
        mock_search_service = Mock()
        mock_scraping_service = Mock()
        mock_scraping_service.extract_links.return_value = "some test value for scrape links"
        mock_scraping_service.scrape_content.return_value = "some test value for scrape data"
        mock_scraping_service.clean_scraped_data.return_value = series_extraction_cleaned_data
        
        mock_service = Mock()
        mock_service.series_extract.return_value = series_extraction_response_data
        
        # Test data with URL and zero date
        test_data = {
            "name": "https://example.com/series/123",
            "date": "0"
        }
        
        with patch('ai_api.api.views.series_extraction_view.SearchService', return_value=mock_search_service), \
            patch('ai_api.api.views.series_extraction_view.ScrapingService', return_value=mock_scraping_service), \
            patch('ai_api.api.views.series_extraction_view.LLMService', return_value=mock_service):
            response = api_client.post(self.__get_url(), test_data, format='json')

        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.success()
        assert response.json()['errors'] == None
        assert response.json()['data']['description'] == "Castillos de España series"
        assert response.status_code == status.HTTP_200_OK
        
        # Verify search service was NOT called (URL bypassed)
        mock_search_service.find_series_url.assert_not_called()
        
        # Verify scraping service was called with the direct URL
        mock_scraping_service.extract_links.assert_called_once_with("https://example.com/series/123")
        
        # Verify service was called with correct parameters
        mock_service.series_extract.assert_called_once_with(
            name="Castillos",
            date="2007-09-10",
            clean_data=str(series_extraction_cleaned_data)
        )
        
    def test_post_series_extraction_with_url_and_non_zero_date_uses_search(
        self, 
        api_client, 
        series_extraction_request_payload_ok, 
        series_extraction_response_data,
        series_extraction_cleaned_data
    ):
        """Test that providing a URL with non-zero date still uses search service."""
        self.permission(granted=True)
        
        # Mock the AI service response
        mock_search_service = Mock()
        mock_search_service.find_series_url.return_value = "some test value for search"
        
        mock_scraping_service = Mock()
        mock_scraping_service.extract_links.return_value = "some test value for scrape links"
        mock_scraping_service.scrape_content.return_value = "some test value for scrape data"
        mock_scraping_service.clean_scraped_data.return_value = series_extraction_cleaned_data
        
        mock_service = Mock()
        mock_service.series_extract.return_value = series_extraction_response_data
        
        # Test data with URL and non-zero date
        test_data = {
            "name": "https://example.com/series/123",
            "date": "2023"
        }
        
        with patch('ai_api.api.views.series_extraction_view.SearchService', return_value=mock_search_service), \
            patch('ai_api.api.views.series_extraction_view.ScrapingService', return_value=mock_scraping_service), \
            patch('ai_api.api.views.series_extraction_view.LLMService', return_value=mock_service):
            response = api_client.post(self.__get_url(), test_data, format='json')

        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.success()
        assert response.json()['errors'] == None
        assert response.json()['data']['description'] == "Castillos de España series"
        assert response.status_code == status.HTTP_200_OK
        
        # Verify search service WAS called (URL not bypassed due to non-zero date)
        mock_search_service.find_series_url.assert_called_once_with("https://example.com/series/123", "2023")
        
        # Verify scraping service was called with the search result URL
        mock_scraping_service.extract_links.assert_called_once_with("some test value for search")
        
        # Verify service was called with correct parameters
        mock_service.series_extract.assert_called_once_with(
            name="Castillos",
            date="2007-09-10",
            clean_data=str(series_extraction_cleaned_data)
        )
    
    def __get_url(self):
        """Get the base URL for AI Manager API endpoints."""
        return f"/{AI_ISSUES_EXTRACTION_URL_V1}"