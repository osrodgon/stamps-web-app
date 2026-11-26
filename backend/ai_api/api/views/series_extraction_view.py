from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from urllib.parse import urlparse

from rest_framework import status
from drf_spectacular.utils import extend_schema

from common.api.messages import Messages
from common.api.serializers.generic_response import GenericResponseSerializer, GenericResponse
from common.log.logger import Logger
from common.core.schemas import standardized_response
from ai_api.sources.errors import (
    SourceConfigurationError,
    SourceNotAllowed,
    SourceNotFound,
    SourceUnavailable,
)
from ai_api.sources.fesofi import FesofiCatalogue
from ai_api.sources.http import get_client
from ai_api.services.search_service import SearchService
from ai_api.services.scraping_service import ScrapingService
from ai_api.services.llm_service import LLMService
from ai_api.api.serializers.series_extraction_request_serializer import SeriesExtractionRequestSerializer
from ai_api.api.serializers.series_extraction_response_serializer import SeriesExtractionResponseSerializer


class SeriesExtractionView(Logger, APIView):
    """
    API view for AI-powered series extraction.

    This view handles POST requests to extract information for series with the LLM provider.
    It validates input data, calls the AI service, and returns structured research results.
    """
    serializer_class = SeriesExtractionResponseSerializer
    
    @extend_schema(
        operation_id="series_extraction_post",
        tags=['AI Services'],
        summary="Extract Information for Series using AI",
        description="Performs AI-powered extraction of series information with the LLM provider. "
                    "Requires a name (either series name or the motive of one of the stamps in the serie) and publication date.",
        request=SeriesExtractionRequestSerializer,
        responses={
            status.HTTP_200_OK: standardized_response(
                SeriesExtractionResponseSerializer, 
                name="SeriesExtractionCompleted",
                description="Series extraction completed successfully.",
                ),
            status.HTTP_400_BAD_REQUEST: standardized_response(
                GenericResponseSerializer,
                name="SeriesExtractionInvalidPayload",
                success=False,
                description="Invalid request payload (e.g., missing required fields)."
                ),
            status.HTTP_401_UNAUTHORIZED: standardized_response(
                GenericResponseSerializer,
                name="SeriesExtractionUnauthorized",
                success=False,
                description="Authentication required."
            ),
            status.HTTP_403_FORBIDDEN: standardized_response(
                GenericResponseSerializer,
                name="SeriesExtractionPermissionDenied",
                success=False,
                description="Permission denied."
            ),
            status.HTTP_404_NOT_FOUND: standardized_response(
                GenericResponseSerializer,
                name="SeriesExtractionNotFound",
                success=False,
                description="Series not found."
            ),
            status.HTTP_422_UNPROCESSABLE_ENTITY: standardized_response(
                GenericResponseSerializer,
                name="SeriesExtractionValidationError",
                success=False,
                description="AI returned invalid or unparseable data."
            ),
            status.HTTP_500_INTERNAL_SERVER_ERROR: standardized_response(
                GenericResponseSerializer,
                name="SeriesExtractionServiceError",
                success=False,
                description="AI service unavailable or internal error."
            )
        }
    )
    def post(self, request: Request, *args, **kwargs) -> Response:
        """
        Handles POST requests to perform AI series extraction.

        Args:
            request: The incoming HTTP request containing series extraction parameters.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            A Response object with extraction results and appropriate HTTP status.
        """
        self.log.debug(Messages.Post.create_one("research request", request.data))
        
        # Get payload and validate it
        payload = SeriesExtractionRequestSerializer(data=request.data)
        
        if not payload.is_valid():
            self.log.warning(Messages.Post.validation_failed("research request", payload.errors))
            return Response(
                data=GenericResponseSerializer(GenericResponse(payload.errors)).data,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Extract data from payload
        name = payload.validated_data.get('name')
        date = payload.validated_data.get('date')
        
        try:
            # Initialize the catalogue, the search, the scraper and the model
            self.log.debug(f"Starting AI research for name: {name} ({date})")
            catalogue = FesofiCatalogue()
            search_service = SearchService()
            scraping_service = ScrapingService()
            llm_service = LLMService()

            match = None
            identity_gap = None

            # A URL plus date "0" skips every lookup, but only for a host the
            # client may fetch: accepting any URL here made the endpoint an
            # authenticated HTTP proxy (SSRF, §1 #3).
            if self._is_url(name) and self._is_zero_date(date):
                if not self._is_source_url(name):
                    raise SourceNotAllowed(
                        f"{urlparse(name).hostname or name} is not an allowed host."
                    )
                self.log.debug(f"Using provided URL directly: {name}")
                clean_data = self._scraped(scraping_service, name)
            else:
                # The catalogue answers with the facts themselves; the search and
                # the scraper are what is left when it does not.
                match = catalogue.identify(name, date)
                if match.found:
                    self.log.debug(
                        f"Catalogue match: '{match.term.get('name')}' "
                        f"(score {match.score})"
                    )
                    clean_data = catalogue.facts(match.products)
                else:
                    self.log.warning(f"Catalogue has no answer: {match.gap}")
                    identity_gap = match.gap
                    url = search_service.find_series_url(name, date)
                    if url is None:
                        message = (
                            f"Could not find anything for name: {name} "
                            f"and date: {date}"
                        )
                        if match.gap:
                            message = f"{message} ({match.gap})"
                        self.log.warning(message)
                        return Response(
                            data=GenericResponseSerializer(GenericResponse({
                                "error": None,
                                "message": message
                            })).data,
                            status=status.HTTP_404_NOT_FOUND
                        )
                    clean_data = self._scraped(scraping_service, url)

            serie_info = clean_data.get("serie_info") or {}

            # Send cleaned scraped data to LLM
            name = serie_info.get("issue_name")
            date = serie_info.get("issue_date")
            llm_result = llm_service.series_extract(
                name=name,
                date=date,
                clean_data=str(clean_data),
            )
            
            # Create response serializer
            response_serializer = SeriesExtractionResponseSerializer(data=llm_result)
            
            if not response_serializer.is_valid():
                self.log.error(f"AI response validation failed: {response_serializer.errors}")
                return Response(
                    data=GenericResponseSerializer(GenericResponse({
                        "error": response_serializer.errors,
                        "message": Messages.AI.response_format_error()
                    })).data,
                    status=status.HTTP_422_UNPROCESSABLE_ENTITY
                )

            # No observation backs a price yet, so the price fields stay empty
            # even if the provider wrote something. A7 fills them from the
            # observations and A9 adds the validator that enforces this for every
            # factual field; until then, a number here would be unauditable.
            validated = response_serializer.validated_data
            validated["market_value_mnh"] = None
            validated["market_value_used"] = None
            for stamp in validated.get("stamps") or []:
                if isinstance(stamp, dict):
                    stamp["market_value_mnh"] = None
                    stamp["market_value_used"] = None

            # If the catalogue could not identify the series and the search had to
            # rescue it, say so: the next reader deserves to know which door was
            # used, and DataDesk can look at it.
            if identity_gap:
                validated["gaps"] = list(validated.get("gaps") or []) + [
                    {"field": "identity", "reason": identity_gap}
                ]

            self.log.debug(f"AI series extraction completed successfully for series: {name}")
            return Response(
                data=response_serializer.data,
                status=status.HTTP_200_OK
            )
        
        except SourceConfigurationError as e:
            # A missing URL or key is a deployment problem: it is not "not found".
            self.log.error(f"AI series extraction is not configured: {str(e)}")
            return Response(
                data=GenericResponseSerializer(GenericResponse({
                    "error": Messages.AI.error(),
                    "message": str(e)
                })).data,
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except SourceNotAllowed as e:
            self.log.error(f"AI series extraction refused a host: {str(e)}")
            return Response(
                data=GenericResponseSerializer(GenericResponse({
                    "error": Messages.AI.validation_error(),
                    "message": str(e)
                })).data,
                status=status.HTTP_400_BAD_REQUEST
            )
        except SourceNotFound as e:
            self.log.warning(f"AI series extraction found nothing: {str(e)}")
            return Response(
                data=GenericResponseSerializer(GenericResponse({
                    "error": None,
                    "message": str(e) or Messages.AI.error()
                })).data,
                status=status.HTTP_404_NOT_FOUND
            )
        except SourceUnavailable as e:
            self.log.error(f"AI series extraction source unavailable: {str(e)}")
            return Response(
                data=GenericResponseSerializer(GenericResponse({
                    "error": Messages.AI.unavailable(),
                    "message": str(e)
                })).data,
                status=status.HTTP_502_BAD_GATEWAY
            )
        except ValueError as e:
            self.log.error(f"AI series extraction validation error: {str(e)}")
            return Response(
                data=GenericResponseSerializer(GenericResponse({
                    "error": Messages.AI.validation_error(),
                    "message": str(e)
                })).data,
                status=status.HTTP_422_UNPROCESSABLE_ENTITY
            )
        except Exception as e:
            self.log.error(f"AI series extraction failed for series: {name}: {str(e)}")
            return Response(
                data=GenericResponseSerializer(GenericResponse({
                    "error": Messages.AI.error(),
                    "message": Messages.AI.unavailable()
                })).data,
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _scraped(self, scraping_service: ScrapingService, url: str) -> dict:
        """Fetch a series page and clean it, or fail with a reason (422)."""
        series_urls = scraping_service.extract_links(url)
        content = scraping_service.scrape_content(series_urls)
        clean_data = scraping_service.clean_scraped_data(content)

        if not content or not (clean_data.get("serie_info") or {}):
            # Nothing was scraped: that is a contract problem (422), not a
            # missing series (404) and not a crash behind a 500.
            self.log.warning(f"Nothing could be scraped from {url}")
            raise ValueError(f"No catalogue data could be read from {url}.")

        return clean_data

    @staticmethod
    def _is_url(name: str) -> bool:
        """Return True when the value carries an http(s) scheme."""
        if not name or not isinstance(name, str):
            return False

        return urlparse(name.strip()).scheme in ("http", "https")

    def _is_source_url(self, name: str) -> bool:
        """
        Check whether the name is a URL the source client may fetch.

        The allowlist decides, not a regex: before this, any host was accepted and
        the endpoint worked as an authenticated HTTP proxy.

        Args:
            name (str): The value received in the `name` field.

        Returns:
            bool: True when it is an http(s) URL of an allowlisted host.
        """
        if not name or not isinstance(name, str):
            return False

        return get_client().is_allowed(name.strip())

    def _is_zero_date(self, date: str) -> bool:
        """
        Check if the provided date represents zero or empty value.
        
        Args:
            date (str): The date to check
            
        Returns:
            bool: True if the date is zero, empty, or represents no date, False otherwise
        """
        if not date:
            return True
        
        # Convert to string and normalize
        date_str = str(date).strip().lower()
        
        # Check for various representations of zero/empty date
        zero_values = ['0', '00', '0000', '0000-00-00', '00/00/0000', 
                      'none', 'null', '', 'undefined', 'n/a', 'na']
        
        return date_str in zero_values
