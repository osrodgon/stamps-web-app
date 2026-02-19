from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema

from common.api.messages import Messages
from common.log.logger import Logger
from common.core.schemas import standardized_response
from common.api.serializers.generic_response import GenericResponse, GenericResponseSerializer
from issues_api.api.serializers.issue_collection_request_serializer import IssueCollectionRequestSerializer
from issues_api.api.serializers.issue_collection_response_serializer import IssueCollectionResponseSerializer
from issues_api.services.issue_collection_service import IssueCollectionService

@extend_schema(tags=['Database Management'])
class IssuesCollectionsView(Logger, APIView):
    """
    API view for handling the creation of issues with all related entities.
    """
    @extend_schema(
        operation_id="create_issue_collections",
        summary="Creates a new issue with all related entities in a single request",
        description="Creates a complete issue entry in the database. This includes all related entities such as year, stamp type, print type, location, country, and color. The endpoint expects a comprehensive payload containing all necessary information to create the issue and its related entities in a single request.",
        request=IssueCollectionRequestSerializer,
        responses={
            status.HTTP_201_CREATED: standardized_response( 
                IssueCollectionResponseSerializer,
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
    def post(self, request: Request, *args, **kwargs) -> Response:
        """
        Handles POST requests to create a new issue with all related entities.

        Args:
            request: The incoming HTTP request containing the issue and related entities data.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            A Response object with the result of the creation operation.
        """
        self.log.debug(Messages.Post.create_one("issue collection", f"{str(request.data)[:35]}..."))
        
        collection = IssueCollectionRequestSerializer(data=request.data)
        
        if collection.is_valid():
            validated_data = collection.validated_data
            
            try:
                # Use the service to handle all business logic
                service = IssueCollectionService()
                issue_collection = service.create_issue_collection(validated_data)
                
                self.log.debug(Messages.Post.created_one("issue collection", issue_collection["issue_name"]))
                return Response(
                    data=IssueCollectionResponseSerializer(issue_collection).data,
                    status=status.HTTP_201_CREATED
                )
            except ValueError as e:
                self.log.warning(f"Invalid data for creating issue collection: {e}")
                return Response(
                    data=GenericResponseSerializer(GenericResponse([str(e)])).data,
                    status=status.HTTP_400_BAD_REQUEST
                )
            
        self.log.warning(Messages.Post.validation_failed("issue", collection.errors))
        return Response(
            data=GenericResponseSerializer(GenericResponse(collection.errors)).data,
            status=status.HTTP_400_BAD_REQUEST
        )
