import pytest
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
from ai_api.sources.errors import SourceConfigurationError, SourceUnavailable
from ai_api.budget import BudgetExpired
from ai_api.sources.base import Observation
from ai_api.sources.fesofi import Match


class TestSeriesExtractionAPI(AbstractApiUnitTest):
    """Test class for AI Manager API endpoints (No Database)."""

    @pytest.fixture(autouse=True)
    def no_catalogue_match(self):
        """By default the catalogue knows nothing: these tests are the fallback.

        The tests that care about the catalogue path patch it themselves.
        """
        stub = Mock()
        stub.identify.return_value = Match(gap="not in the catalogue")
        stub.facts.return_value = {}

        shop = Mock()
        shop.prices.return_value = []

        search = Mock()
        search.prices.return_value = []

        with patch(
            'ai_api.api.views.series_extraction_view.FesofiCatalogue',
            return_value=stub,
        ), patch(
            'ai_api.api.views.series_extraction_view.FilateliaCatalogue',
            return_value=shop,
        ), patch(
            'ai_api.api.views.series_extraction_view.SearchPrices',
            return_value=search,
        ):
            yield stub
    
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
        
        # Test data with an allowlisted URL and zero date
        test_data = {
            "name": "https://catalogodesellos.fesofi.es/producto/0199/",
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
        mock_scraping_service.extract_links.assert_called_once_with(
            "https://catalogodesellos.fesofi.es/producto/0199/"
        )
        
        # Verify service was called with correct parameters
        mock_service.series_extract.assert_called_once_with(
            name="Castillos",
            date="2007-09-10",
            clean_data=str(series_extraction_cleaned_data)
        )
        
    def test_the_catalogue_facts_are_used_without_scraping(
        self,
        api_client,
        series_extraction_request_payload_ok,
        series_extraction_response_data,
    ):
        """When the catalogue identifies the series, its facts go to the model."""
        self.permission(granted=True)

        facts = {
            "serie_info": {"issue_name": "Navidad", "issue_date": "16 noviembre 1986"},
            "stamps": [{"edifil_code": "2867", "face_value": "19 pta"}],
        }

        catalogue = Mock()
        catalogue.identify.return_value = Match(
            products=[{"name": "2883"}],
            term={"name": "Navidad"},
            score=1.0,
        )
        catalogue.facts.return_value = facts

        scraping = Mock()
        llm = Mock()
        llm.series_extract.return_value = series_extraction_response_data

        with patch(
            'ai_api.api.views.series_extraction_view.FesofiCatalogue',
            return_value=catalogue,
        ), patch(
            'ai_api.api.views.series_extraction_view.ScrapingService',
            return_value=scraping,
        ), patch(
            'ai_api.api.views.series_extraction_view.SearchService',
        ) as search_class, patch(
            'ai_api.api.views.series_extraction_view.LLMService',
            return_value=llm,
        ):
            response = api_client.post(
                self.__get_url(), series_extraction_request_payload_ok, format='json'
            )

        assert response.status_code == status.HTTP_200_OK
        scraping.extract_links.assert_not_called()
        search_class.return_value.find_series_url.assert_not_called()
        llm.series_extract.assert_called_once_with(
            name="Navidad", date="16 noviembre 1986", clean_data=str(facts)
        )

    def test_a_fallback_says_the_catalogue_did_not_identify_it(
        self,
        api_client,
        series_extraction_request_payload_ok,
        series_extraction_response_data,
        series_extraction_cleaned_data,
    ):
        """If the search rescues it, the response still records the identity gap."""
        self.permission(granted=True)

        catalogue = Mock()
        catalogue.identify.return_value = Match(gap="Ambiguous: Navidad, Navidad 2004.")

        search = Mock()
        search.find_series_url.return_value = "https://catalogodesellos.fesofi.es/producto/0199/"

        scraping = Mock()
        scraping.extract_links.return_value = ["https://catalogodesellos.fesofi.es/producto/0199/"]
        scraping.scrape_content.return_value = "content"
        scraping.clean_scraped_data.return_value = series_extraction_cleaned_data

        llm = Mock()
        llm.series_extract.return_value = series_extraction_response_data

        with patch(
            'ai_api.api.views.series_extraction_view.FesofiCatalogue',
            return_value=catalogue,
        ), patch(
            'ai_api.api.views.series_extraction_view.SearchService', return_value=search
        ), patch(
            'ai_api.api.views.series_extraction_view.ScrapingService', return_value=scraping
        ), patch(
            'ai_api.api.views.series_extraction_view.LLMService', return_value=llm
        ):
            response = api_client.post(
                self.__get_url(), series_extraction_request_payload_ok, format='json'
            )

        assert response.status_code == status.HTTP_200_OK
        gaps = response.json()["data"]["gaps"]
        assert gaps[0]["field"] == "identity"
        assert "Ambiguous" in gaps[0]["reason"]

    def test_both_doors_failing_says_why(
        self,
        api_client,
        series_extraction_request_payload_ok,
    ):
        """A 404 carries the catalogue's reason instead of only "nothing found"."""
        self.permission(granted=True)

        catalogue = Mock()
        catalogue.identify.return_value = Match(gap="No series contains navidad.")

        search = Mock()
        search.find_series_url.return_value = None

        with patch(
            'ai_api.api.views.series_extraction_view.FesofiCatalogue',
            return_value=catalogue,
        ), patch(
            'ai_api.api.views.series_extraction_view.SearchService', return_value=search
        ):
            response = api_client.post(
                self.__get_url(), series_extraction_request_payload_ok, format='json'
            )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "No series contains navidad" in response.json()["errors"][0]["message"]

    def test_a_stamp_is_valued_from_the_prices_the_shop_has(
        self,
        api_client,
        series_extraction_request_payload_ok,
        series_extraction_response_data,
    ):
        """The value comes from the observations, and says which code it prices."""
        self.permission(granted=True)

        facts = {
            "serie_info": {"issue_name": "Castillos", "year": "2007"},
            "stamps": [{"edifil_code": "4349", "face_value": "2,49"}],
        }
        catalogue = Mock()
        catalogue.identify.return_value = Match(products=[{"name": "4604"}], score=1.0)
        catalogue.facts.return_value = facts

        def prices(code, year="", timeout=None):
            return [
                Observation(source="filatelia", price=10, condition="used"),
                Observation(source="filatelia", price=11, condition="used"),
                Observation(source="filatelia", price=12, condition="used"),
                Observation(source="filatelia", price=500, condition="used"),
                Observation(source="filatelia", price=99, condition="mnh"),
            ]

        shop = Mock()
        shop.prices.side_effect = prices

        llm = Mock()
        llm.series_extract.return_value = series_extraction_response_data

        with patch(
            'ai_api.api.views.series_extraction_view.FesofiCatalogue',
            return_value=catalogue,
        ), patch(
            'ai_api.api.views.series_extraction_view.FilateliaCatalogue',
            return_value=shop,
        ), patch(
            'ai_api.api.views.series_extraction_view.LLMService', return_value=llm
        ):
            response = api_client.post(
                self.__get_url(), series_extraction_request_payload_ok, format='json'
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()["data"]

        # 10 and 500 go; 11 and 12 stay.
        assert data["stamps"][0]["market_value_used"] == 11.5
        # One mint price is not an estimate.
        assert data["stamps"][0]["market_value_mnh"] is None
        # The series is not the sum of its stamps.
        assert data["market_value_used"] is None

        assert len(data["observations"]) == 5
        assert data["observations"][0]["subject_code"] == "4349"
        assert data["observations"][0]["kind"] == "ask"

    def test_the_search_fills_in_when_the_shop_has_one_price(
        self,
        api_client,
        series_extraction_request_payload_ok,
        series_extraction_response_data,
    ):
        """One shop price is not an estimate, so the search is asked too."""
        self.permission(granted=True)

        facts = {
            "serie_info": {"issue_name": "Castillos", "year": "2007"},
            "stamps": [{"edifil_code": "4349"}],
        }
        catalogue = Mock()
        catalogue.identify.return_value = Match(products=[{"name": "4604"}], score=1.0)
        catalogue.facts.return_value = facts

        shop = Mock()
        shop.prices.return_value = [
            Observation(source="filatelia", price=10, condition="used")
        ]

        search = Mock()
        search.prices.return_value = [
            Observation(source="search", price=12, condition="used"),
            Observation(source="search", price=14, condition="used"),
        ]

        llm = Mock()
        llm.series_extract.return_value = series_extraction_response_data

        with patch(
            'ai_api.api.views.series_extraction_view.FesofiCatalogue',
            return_value=catalogue,
        ), patch(
            'ai_api.api.views.series_extraction_view.FilateliaCatalogue',
            return_value=shop,
        ), patch(
            'ai_api.api.views.series_extraction_view.SearchPrices',
            return_value=search,
        ), patch(
            'ai_api.api.views.series_extraction_view.LLMService', return_value=llm
        ):
            response = api_client.post(
                self.__get_url(), series_extraction_request_payload_ok, format='json'
            )

        data = response.json()["data"]

        search.prices.assert_called_once()
        assert data["stamps"][0]["market_value_used"] == 12.0  # 10, 12, 14
        assert sorted({row["source"] for row in data["observations"]}) == [
            "filatelia",
            "search",
        ]

    def test_running_out_of_budget_answers_with_what_it_has(
        self,
        api_client,
        series_extraction_request_payload_ok,
        series_extraction_response_data,
    ):
        """A partial answer with its reason beats a request that never returns."""
        self.permission(granted=True)

        facts = {
            "serie_info": {"issue_name": "Castillos", "year": "2007"},
            "stamps": [{"edifil_code": "4349"}],
        }
        catalogue = Mock()
        catalogue.identify.return_value = Match(products=[{"name": "4604"}], score=1.0)
        catalogue.facts.return_value = facts

        exhausted = Mock()
        exhausted.total = 25
        exhausted.expired = True
        exhausted.timeout_for.side_effect = BudgetExpired("no time")

        llm = Mock()
        llm.series_extract.return_value = series_extraction_response_data

        with patch(
            'ai_api.api.views.series_extraction_view.FesofiCatalogue',
            return_value=catalogue,
        ), patch(
            'ai_api.api.views.series_extraction_view.Budget', return_value=exhausted
        ), patch(
            'ai_api.api.views.series_extraction_view.FilateliaCatalogue'
        ) as shop_class, patch(
            'ai_api.api.views.series_extraction_view.LLMService', return_value=llm
        ):
            response = api_client.post(
                self.__get_url(), series_extraction_request_payload_ok, format='json'
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()["data"]

        assert data["partial"] is True
        assert "budget" in [gap["field"] for gap in data["gaps"]]
        shop_class.return_value.prices.assert_not_called()

    def test_a_complete_answer_is_not_partial(
        self,
        api_client,
        series_extraction_request_payload_ok,
        series_extraction_response_data,
    ):
        self.permission(granted=True)

        facts = {
            "serie_info": {"issue_name": "Castillos", "year": "2007"},
            "stamps": [{"edifil_code": "4349"}],
        }
        catalogue = Mock()
        catalogue.identify.return_value = Match(products=[{"name": "4604"}], score=1.0)
        catalogue.facts.return_value = facts

        shop = Mock()
        shop.prices.return_value = [
            Observation(source="filatelia", price=11, condition="mnh"),
            Observation(source="filatelia", price=12, condition="mnh"),
            Observation(source="filatelia", price=13, condition="mnh"),
        ]

        llm = Mock()
        llm.series_extract.return_value = series_extraction_response_data

        with patch(
            'ai_api.api.views.series_extraction_view.FesofiCatalogue',
            return_value=catalogue,
        ), patch(
            'ai_api.api.views.series_extraction_view.FilateliaCatalogue',
            return_value=shop,
        ), patch(
            'ai_api.api.views.series_extraction_view.LLMService', return_value=llm
        ):
            response = api_client.post(
                self.__get_url(), series_extraction_request_payload_ok, format='json'
            )

        data = response.json()["data"]

        assert data["partial"] is False
        assert data["stamps"][0]["market_value_mnh"] == 12.0

    def test_no_price_is_a_gap_not_a_zero(
        self,
        api_client,
        series_extraction_request_payload_ok,
        series_extraction_response_data,
        series_extraction_cleaned_data,
    ):
        self.permission(granted=True)

        search = Mock()
        search.find_series_url.return_value = "https://catalogodesellos.fesofi.es/producto/0199/"
        scraping = Mock()
        scraping.extract_links.return_value = ["https://catalogodesellos.fesofi.es/producto/0199/"]
        scraping.scrape_content.return_value = "content"
        scraping.clean_scraped_data.return_value = series_extraction_cleaned_data
        llm = Mock()
        llm.series_extract.return_value = series_extraction_response_data

        with patch(
            'ai_api.api.views.series_extraction_view.SearchService', return_value=search
        ), patch(
            'ai_api.api.views.series_extraction_view.ScrapingService', return_value=scraping
        ), patch(
            'ai_api.api.views.series_extraction_view.LLMService', return_value=llm
        ):
            response = api_client.post(
                self.__get_url(), series_extraction_request_payload_ok, format='json'
            )

        data = response.json()["data"]
        fields = [gap["field"] for gap in data["gaps"]]

        assert "market_value" in fields
        assert data["stamps"][0]["market_value_used"] is None
        assert data["observations"] == []

    def test_post_series_extraction_refuses_a_host_outside_the_allowlist(
        self,
        api_client,
        series_extraction_response_data,
        series_extraction_cleaned_data
    ):
        """A URL plus date "0" only bypasses the search for an allowlisted host.

        Before this, any URL was fetched: the endpoint worked as an authenticated
        HTTP proxy (SSRF).
        """
        self.permission(granted=True)

        mock_scraping_service = Mock()
        mock_scraping_service.extract_links.return_value = "links"
        mock_scraping_service.scrape_content.return_value = "content"
        mock_scraping_service.clean_scraped_data.return_value = series_extraction_cleaned_data

        mock_service = Mock()
        mock_service.series_extract.return_value = series_extraction_response_data

        test_data = {"name": "http://169.254.169.254/latest/meta-data/", "date": "0"}

        with patch('ai_api.api.views.series_extraction_view.ScrapingService', return_value=mock_scraping_service), \
            patch('ai_api.api.views.series_extraction_view.LLMService', return_value=mock_service):
            response = api_client.post(self.__get_url(), test_data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        mock_scraping_service.extract_links.assert_not_called()

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
    
    def test_post_series_extraction_returns_502_when_a_source_is_down(
        self,
        api_client,
        series_extraction_request_payload_ok,
    ):
        """A source that cannot be asked is not "not found": it is a 502."""
        self.permission(granted=True)

        mock_search_service = Mock()
        mock_search_service.find_series_url.side_effect = SourceUnavailable("down")

        with patch(
            'ai_api.api.views.series_extraction_view.SearchService',
            return_value=mock_search_service,
        ):
            response = api_client.post(
                self.__get_url(), series_extraction_request_payload_ok, format='json'
            )

        assert response.status_code == status.HTTP_502_BAD_GATEWAY

    def test_post_series_extraction_returns_500_when_a_source_is_not_configured(
        self,
        api_client,
        series_extraction_request_payload_ok,
    ):
        """A missing URL or key is a deployment problem, not a 404."""
        self.permission(granted=True)

        with patch(
            'ai_api.api.views.series_extraction_view.SearchService',
            side_effect=SourceConfigurationError("SERPER_URL is required"),
        ):
            response = api_client.post(
                self.__get_url(), series_extraction_request_payload_ok, format='json'
            )

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "SERPER_URL" in response.json()['message']
        assert response.json()['data'] is None

    def test_post_series_extraction_returns_422_when_nothing_is_scraped(
        self,
        api_client,
        series_extraction_response_data,
        series_extraction_request_payload_ok,
    ):
        """An empty scrape is a contract problem (422), not a crash behind a 500."""
        self.permission(granted=True)

        mock_search_service = Mock()
        mock_search_service.find_series_url.return_value = (
            "https://catalogodesellos.fesofi.es/producto/0001/"
        )

        mock_scraping_service = Mock()
        mock_scraping_service.extract_links.return_value = []
        mock_scraping_service.scrape_content.return_value = []
        mock_scraping_service.clean_scraped_data.return_value = {}

        mock_service = Mock()
        mock_service.series_extract.return_value = series_extraction_response_data

        with patch(
            'ai_api.api.views.series_extraction_view.SearchService',
            return_value=mock_search_service,
        ), patch(
            'ai_api.api.views.series_extraction_view.ScrapingService',
            return_value=mock_scraping_service,
        ), patch(
            'ai_api.api.views.series_extraction_view.LLMService',
            return_value=mock_service,
        ):
            response = api_client.post(
                self.__get_url(), series_extraction_request_payload_ok, format='json'
            )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        mock_service.series_extract.assert_not_called()

    def __get_url(self):
        """Get the base URL for AI Manager API endpoints."""
        return f"/{AI_ISSUES_EXTRACTION_URL_V1}"