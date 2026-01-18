from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from common.api.serializers.generic_response import GenericResponseSerializer, GenericResponse
from common.log.logger import Logger
from common.core.schemas import standardized_response
from common.api.messages import Messages

from issues_api.models import Issue
from issues_api.api.serializers.issue_request_serializer import IssueRequestSerializer
from issues_api.api.serializers.issue_response_serializer import IssueResponseSerializer
import unicodedata


@extend_schema(tags=['Database Management'])
class IssuesView(Logger, APIView):
    """
    API view for handling collections of Issue instances.

    This view provides GET (list) and POST (create) operations for issues.
    """
    serializer_class = IssueResponseSerializer
    
    @extend_schema(
        operation_id="list_issues",
        summary="List all issues",
        description="Retrieves a list of all issue entries. Can be filtered by year and name.",
        parameters=[
        OpenApiParameter(
                name='year', 
                type=OpenApiTypes.INT, 
                location=OpenApiParameter.QUERY, 
                description='Filter issues by year',
                required=False
            ),
            OpenApiParameter(
                name='name', 
                type=OpenApiTypes.STR, 
                location=OpenApiParameter.QUERY, 
                description='Filter issues by name',
                required=False
            ),
        ],
        responses={
            status.HTTP_200_OK: standardized_response(
                IssueResponseSerializer, 
                name="IssuesRetrieved",
                description="A list of issues was successfully retrieved.",
                many=True
            ),
            status.HTTP_403_FORBIDDEN: standardized_response(
                IssueResponseSerializer,
                name="IssuesListForbidden",
                success=False,
                description="Permission denied."
            )
        }
    )
    def get(self, request:Request, *args, **kwargs) -> Response:
        """
        Handles GET requests to retrieve a list of all issues.

        Args:
            request: The incoming HTTP request.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            A Response object containing a list of all serialized issues
            with a 200 OK status.
        """
        self.log.debug(Messages.Get.retrieve_all("issues"))
        year = request.query_params.get('year', None)
        issue_name = request.query_params.get('name', None)
        
        issues = Issue.objects.all().order_by('date')
        if year:
            try:
                year_int = int(year)
                self.log.debug(f"Filtering issues by year {year_int}")
                issues = issues.filter(year__year=year_int)
            except ValueError:
                self.log.warning(f"Invalid value for 'year' filter provided: {year}")
                issues = issues.none()
        if issue_name:
            self.log.debug(f"Filtering issues by issue name {issue_name}")
            normalized_search = self._normalize_string(issue_name)
            issues = [
                issue for issue in issues 
                if normalized_search in self._normalize_string(issue.name)
            ]
        
        self.log.debug(Messages.Get.retrieved_all("issues", len(issues)))
        response = IssueResponseSerializer(issues, many=True)
        
        return Response(data=response.data, status=status.HTTP_200_OK)
    
    @extend_schema(
        operation_id="create_issue",
        summary="Create a new issue",
        description="Adds a new issue entry to the database. A successful creation returns the newly created issue object with a 201 Created status code.",
        request=IssueRequestSerializer,
        responses={
            status.HTTP_201_CREATED: standardized_response( 
                IssueResponseSerializer,
                name="IssueCreated",
                description="The issue was created successfully."
            ),
            status.HTTP_400_BAD_REQUEST: standardized_response(
                GenericResponseSerializer,
                name="IssueCreateInvalidPayload",
                success=False,
                description="The request payload was invalid (e.g., missing a required field)."
            ),
            status.HTTP_403_FORBIDDEN: standardized_response(
                IssueResponseSerializer,
                name="IssueCreateForbidden",
                success=False,
                description="Permission denied."
            )
        }
    )
    def post(self, request:Request, *args, **kwargs) -> Response:
        """
        Handles POST requests to create a new issue.

        Args:
            request: The incoming HTTP request containing the new issue data.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            A Response object with the newly created issue data and a 201 Created
            status if successful. Returns a 400 Bad Request if the provided
            data is invalid.
        """
        self.log.debug(Messages.Post.create_one("issue", request.data))
        issue = IssueRequestSerializer(data = request.data)
        
        if issue.is_valid():
            instance = issue.save()
            self.log.info(Messages.Post.created_one("issue", instance.id))
            return Response(
                data=IssueResponseSerializer(instance).data, 
                status=status.HTTP_201_CREATED
            )
        
        self.log.warning(Messages.Post.validation_failed("issue", issue.errors))
        return Response(
            data=GenericResponseSerializer(GenericResponse(issue.errors)).data,
            status=status.HTTP_400_BAD_REQUEST
        )

    @staticmethod
    def _normalize_string(text: str) -> str:
        """
        Normalizes a string by converting it to lowercase and removing accents.
        """
        if not text:
            return ""
        nfd_form = unicodedata.normalize('NFD', text)
        return "".join(c for c in nfd_form if unicodedata.category(c) != 'Mn').lower()
