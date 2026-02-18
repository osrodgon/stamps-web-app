from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema

from common.log.logger import Logger
from common.core.schemas import standardized_response
from common.api.serializers.generic_response import GenericResponse, GenericResponseSerializer
from issues_api.api.serializers.issue_request_serializer import IssueRequestSerializer
from issues_api.api.serializers.issue_response_serializer import IssueResponseSerializer

@extend_schema(tags=['Database Management'])
class IssuesCollectionsView(Logger, APIView):
    """
    API view for handling the creation of issues with all related entities.
    """
    # serializer_class = IssueRequestSerializer
    
    @extend_schema(
        operation_id="create_issue_collections",
        summary="Creates a new issue with all related entities in a single request",
        description="Creates a complete issue entry in the database. This includes all related entities such as year, stamp type, print type, location, country, and color. The endpoint expects a comprehensive payload containing all necessary information to create the issue and its related entities in a single request.",
        request=IssueRequestSerializer,
        responses={
            status.HTTP_201_CREATED: standardized_response( 
                IssueResponseSerializer,
                name="IssueCollectionsCreated",
                description="The issue was created successfully."
            ),
            status.HTTP_400_BAD_REQUEST: standardized_response(
                GenericResponseSerializer,
                name="IssueCollectionsCreateInvalidPayload",
                success=False,
                description="The request payload was invalid (e.g., missing a required field)."
            ),
            status.HTTP_403_FORBIDDEN: standardized_response(
                GenericResponseSerializer,
                name="IssueCollectionsCreateForbidden",
                success=False,
                description="Permission denied."
            )
        }
    )
    def post(self, request:Request, *args, **kwargs) -> Response:
        """
        Handles POST requests to create a new issue with all related entities.

        Args:
            request: The incoming HTTP request containing the issue and related entities data.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            A Response object with the result of the creation operation.
        """
        message = "This endpoint is a placeholder for future implementation."
        self.log.error(request.data)
        return Response(
            data=GenericResponseSerializer(GenericResponse(message)).data, 
            status=status.HTTP_400_BAD_REQUEST
        )
        