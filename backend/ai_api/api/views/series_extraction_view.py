from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema
import re

from common.api.messages import Messages
from common.api.serializers.generic_response import GenericResponseSerializer, GenericResponse
from common.log.logger import Logger
from common.core.schemas import standardized_response
from common.api.messages import Messages
from ai_api.services.search_service import SearchService
from ai_api.services.scraping_service import ScrapingService
from ai_api.services.llm_service import LLMService
from ai_api.api.serializers.series_extraction_request_serializer import SeriesExtractionRequestSerializer
from ai_api.api.serializers.series_extraction_response_serializer import SeriesExtractionResponseSerializer


class SeriesExtractionView(Logger, APIView):
    """
    API view for AI-powered series extraction.

    This view handles POST requests to extract information for series using Google Gemini AI.
    It validates input data, calls the AI service, and returns structured research results.
    """
    serializer_class = SeriesExtractionResponseSerializer
    
    @extend_schema(
        operation_id="series_extraction_post",
        tags=['AI Services'],
        summary="Extract Information for Series using AI",
        description="Performs AI-powered extraction of series information using Google Gemini. "
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
            # Initialize Search, Scrape and AI services
            self.log.debug(f"Starting AI research for name: {name} ({date})")
            search_service = SearchService()
            scraping_service = ScrapingService()
            llm_service = LLMService()
            
            # Check if name is already a URL and date is 0 - skip search service
            if self._is_valid_url(name) and self._is_zero_date(date):
                self.log.debug(f"Using provided URL directly: {name}")
                url = name
            else:
                # Search for an URL that matches the name and date
                url = search_service.find_series_url(name, date)
                if url is None:
                    # No URL found
                    message = f"Could not find anything for name: {name} and date: {date}"
                    self.log.warning(message)
                    return Response(
                        data=GenericResponseSerializer(GenericResponse({
                            "error": None,
                            "message": message
                        })).data,
                        status=status.HTTP_404_NOT_FOUND
                    )
            
            # Get all URLs that have information about the series
            series_urls = scraping_service.extract_links(url)
            
            # Scrap and clean all information from URLs
            content = scraping_service.scrape_content(series_urls)
            clean_data = scraping_service.clean_scraped_data(content)
            
            # Send cleaned scraped data to LLM
            name = clean_data.get("serie_info").get("título serie")
            date = clean_data.get("serie_info").get("fecha de emisión")
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
            
            self.log.debug(f"AI series extraction completed successfully for series: {name}")
            return Response(
                data=response_serializer.data,
                status=status.HTTP_200_OK
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
    
    def _is_valid_url(self, name: str) -> bool:
        """
        Check if the provided name is a valid URL.
        
        Args:
            name (str): The name to check for URL validity
            
        Returns:
            bool: True if the name is a valid URL, False otherwise
        """
        if not name or not isinstance(name, str):
            return False
        
        # Basic URL pattern matching (supports http, https, www)
        url_pattern = re.compile(
            r'^(https?:\/\/)?'  # Optional protocol
            r'([www]\.)?'        # Optional www
            r'([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}'  # Domain
            r'([\/\w\.-]*)*'     # Path
            r'(\?[^\s]*)?'       # Optional query parameters
            r'$', re.IGNORECASE
        )
        
        return bool(url_pattern.match(name.strip()))
    
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
