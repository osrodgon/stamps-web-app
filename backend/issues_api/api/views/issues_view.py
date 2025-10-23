from rest_framework.views import APIView
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema

from common.api.serializers.generic_response import GenericResponseSerializer, GenericResponse
from common.log.logger import Logger
from common.core.schemas import standardized_response
from common.api.messages import Messages
from issues_api.models import Issue
from issues_api.api.serializers.issue_request_serializer import IssueRequestSerializer
from issues_api.api.serializers.issue_response_serializer import IssueResponseSerializer


@extend_schema(tags=['Database Management'])
class IssuesView(Logger, APIView):
    serializer_class = IssueResponseSerializer
    
    @extend_schema(
        operation_id="list_issues",
        summary="List all issues",
        description="Retrieves a list of all issue entries currently stored in the database.",
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
                description="Permission denied. You're likely missing X-API-Key header."
            )
        }
    )
    def get(self, request:Request, *args, **kwargs) -> Response:
        self.debug(Messages.Get.retrieve_all("issues"))
        issues = Issue.objects.all()
        self.debug(Messages.Get.retrieved_all("issues", issues.count()))
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
                description="Permission denied. You're likely missing X-API-Key header."
            )
        }
    )
    def post(self, request:Request, *args, **kwargs) -> Response:
        self.debug(Messages.Post.create_one("issue", request.data))
        issue = IssueRequestSerializer(data = request.data)
        
        if issue.is_valid():
            instance = issue.save()
            self.info(Messages.Post.created_one("issue", instance.id))
            return Response(
                data=IssueResponseSerializer(instance).data, 
                status=status.HTTP_201_CREATED
            )
        
        self.warning(Messages.Post.validation_failed("issue", issue.errors))
        return Response(
            data=GenericResponseSerializer(GenericResponse(issue.errors)).data,
            status=status.HTTP_400_BAD_REQUEST
        )
