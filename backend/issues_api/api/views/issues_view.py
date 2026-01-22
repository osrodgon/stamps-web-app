import unicodedata

from common.api.messages import Messages
from common.api.serializers.generic_response import (
    GenericResponse,
    GenericResponseSerializer,
)
from common.core.schemas import standardized_response
from common.log.logger import Logger
from django.db import connection
from django.db.models import Q
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from issues_api.api.serializers.issue_request_serializer import IssueRequestSerializer
from issues_api.api.serializers.issue_response_serializer import IssueResponseSerializer
from issues_api.models import Issue


@extend_schema(tags=['Database Management'])
class IssuesView(Logger, APIView):
    """
    API view for handling collections of Issue instances.

    This view provides GET (list) and POST (create) operations for issues,
    supporting filtering by year and name.
    """
    serializer_class = IssueResponseSerializer
    
    @extend_schema(
        operation_id="list_issues",
        summary="List all issues",
        description="Retrieves a list of all issue entries. Can be filtered by year and name.",
        parameters=[
        OpenApiParameter(
                name='year', 
                type=OpenApiTypes.STR, 
                location=OpenApiParameter.QUERY, 
                description='Filter issues by year or year range (e.g., 2002 or 2000-2010)',
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

        Supports filtering by:
        - year: A single year (e.g., '2002') or a range (e.g., '2000-2010').
        - name: A case-insensitive search string for the issue name.

        Args:
            request: The incoming HTTP request containing query parameters.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            A Response object containing a list of all serialized issues
            matching the filters with a 200 OK status.
        """
        self.log.debug(Messages.Get.retrieve_all("issues"))
        year_param = request.query_params.get('year', None)
        issue_name = request.query_params.get('name', '').strip() or None
        query_conditions = Q()
        issues = Issue.objects.all()
        
        name_lookup = "name__unaccent__icontains" if connection.vendor == 'postgresql' else "name__icontains"

        if year_param:
            if '-' in year_param:
                # Filter by year range AND then by name (if present)
                try:
                    self.log.debug(f"Adding year range filter to query: {year_param}")
                    start_year_str, end_year_str = year_param.split('-', 1)
                    start_year = int(start_year_str)
                    end_year = int(end_year_str)
                    query_conditions &= Q(year__year__range=(start_year, end_year))

                    if issue_name:
                        self.log.debug(f"Adding name filter to query:{issue_name}")
                        query_conditions &= Q(**{name_lookup: issue_name})
                except (ValueError, TypeError):
                    self.log.warning(f"Invalid format for 'year' range filter provided: {year_param}")
            else:
                # Filter by year OR by name (if present)
                try:
                    self.log.debug(f"Adding year filter to query: {year_param}")
                    year_int = int(year_param)
                    query_conditions |= Q(year__year=year_int)

                    if issue_name:
                        self.log.debug(f"Adding name filter to query:{issue_name}")
                        query_conditions |= Q(**{name_lookup: issue_name})
                except ValueError:
                    self.log.warning(f"Invalid value for 'year' filter provided: {year_param}")
                
        elif issue_name:
            # Filter by name only
            self.log.debug(f"Adding name filter to query:{issue_name}")
            query_conditions &= Q(**{name_lookup: issue_name})
            
        
        issues = issues.filter(query_conditions).order_by('date')
        
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

        Args:
            text: The string to normalize.

        Returns:
            The normalized lowercase string without accents, or an empty string if input is None.
        """
        if not text:
            return ""
        nfd_form = unicodedata.normalize('NFD', text)
        return "".join(c for c in nfd_form if unicodedata.category(c) != 'Mn').lower()
