from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema

from common.api.messages import Messages
from common.api.serializers.generic_response import GenericResponseSerializer, GenericResponse
from common.log.logger import Logger
from common.core.schemas import standardized_response
from common.api.messages import Messages
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
                    "Requires issue name, publication date, and starting Edifil catalog number.",
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
        
        # Validate input data
        research_request = SeriesExtractionRequestSerializer(data=request.data)
        
        if not research_request.is_valid():
            self.log.warning(Messages.Post.validation_failed("research request", research_request.errors))
            return Response(
                data=GenericResponseSerializer(GenericResponse(research_request.errors)).data,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Extract validated data
        validated_data = research_request.validated_data
        issue_name = validated_data['issue_name']
        issue_date = validated_data['issue_date']
        edifil_start_number = validated_data['edifil_start_number']
        
        self.log.info(f"Starting AI research for series: {issue_name} ({issue_date}) - Edifil: {edifil_start_number}")
        
        try:
            # Initialize AI service
            llm_service = LLMService()
            
            # Perform series extraction
            llm_result = llm_service.series_extract(
                issue_name=issue_name,
                issue_date=issue_date,
                edifil_start_number=edifil_start_number
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
            
            self.log.info(f"AI series extraction completed successfully for series: {issue_name}")
            return Response(
                data=response_serializer.data,
                status=status.HTTP_200_OK
            )
        
        except ValueError as e:
            self.log.warning(f"AI series extraction validation error: {str(e)}")
            return Response(
                data=GenericResponseSerializer(GenericResponse({
                    "error": Messages.AI.validation_error(),
                    "message": str(e)
                })).data,
                status=status.HTTP_422_UNPROCESSABLE_ENTITY
            )
        except Exception as e:
            self.log.error(f"AI series extraction failed for series: {issue_name}: {str(e)}")
            return Response(
                data=GenericResponseSerializer(GenericResponse({
                    "error": Messages.AI.error(),
                    "message": Messages.AI.unavailable()
                })).data,
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )