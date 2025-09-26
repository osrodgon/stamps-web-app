from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema

from common.log.logger import Logger
from issues_api.models import Issue
from issues_api.api.serializers.issue_request_serializer import IssueRequestSerializer
from issues_api.api.serializers.issue_response_serializer import IssueResponseSerializer
from common.api.messages import Messages
from common.core.schemas import standardized_response
from common.api.serializers.generic_response import GenericResponse, GenericResponseSerializer


@extend_schema(tags=["Issues"])
class IssuesByIdView(Logger, APIView):
    def __get_object(self, pk):
        try:
            Messages.Database.querying_one("issue", pk) 
            return Issue.objects.get(pk=pk)
        except Issue.DoesNotExist:
            Messages.Database.not_found("issue", pk)
            return None

    @extend_schema(
        operation_id="retrieve_issue",
        summary="Retrieve an issue by ID",
        description="Retrieves the details of a specific issue by its unique ID.",
        responses={
            status.HTTP_200_OK: standardized_response(
                IssueResponseSerializer,
                name="IssueRetrieved",
                description="The requested issue's data was retrieved successfully."
            ),
            status.HTTP_404_NOT_FOUND: standardized_response(
                GenericResponseSerializer,
                name="RetrieveIssueNotFound",
                success=False,
                description="No issue was found for the provided ID."
            ),
        }
    )
    def get(self, request: Request, pk: int, *args, **kwargs) -> Response:
        self.debug(Messages.Get.retrieve_one("issue", pk))
        issue = self.__get_object(pk)
        if issue is None:
            message = Messages.Get.not_found("issue", pk)
            self.warning(message)
            return Response(data=GenericResponseSerializer(GenericResponse(message)).data, status=status.HTTP_404_NOT_FOUND)
        
        serializer = IssueResponseSerializer(issue)
        self.info(Messages.Get.retrieved_one("issue", pk))
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        operation_id="update_issue",
        summary="Update an issue",        
        description="Updates an existing issue with the provided data.",
        request=IssueRequestSerializer,
        responses={
            status.HTTP_200_OK: standardized_response(
                IssueResponseSerializer,
                name="IssueUpdated",
                description="The issue was updated successfully."
            ),
            status.HTTP_400_BAD_REQUEST: standardized_response(
                GenericResponseSerializer,
                name="IssueUpdateInvalidPayload",
                success=False,
                description="The request payload was invalid."
            ),
            status.HTTP_404_NOT_FOUND: standardized_response(
                GenericResponseSerializer,
                name="IssueUpdateNotFound",
                success=False,
                description="The issue with the specified ID was not found."
            ),
        }
    )
    def put(self, request: Request, pk: int, *args, **kwargs) -> Response:
        self.debug(Messages.Put.update_one("issue", pk, request.data))
        issue = self.__get_object(pk)
        if issue is None:
            message = Messages.Put.not_found("issue", pk)
            self.warning(message)
            return Response(
                data=GenericResponseSerializer(GenericResponse(message)).data, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = IssueRequestSerializer(issue, data=request.data)
        if not serializer.is_valid():
            self.warning(Messages.Put.validation_failed("issue", pk, serializer.errors))
            return Response(
                data=serializer.errors, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        instance = serializer.save()
        self.info(Messages.Put.updated_one("issue", instance.id))
        response_serializer = IssueResponseSerializer(instance)
        return Response(
            data=response_serializer.data, 
            status=status.HTTP_200_OK
        )

    @extend_schema(
        operation_id="delete_issue",
        summary="Delete an issue",        
        description="Deletes a specific issue by its unique ID.",
        responses={
            status.HTTP_200_OK: standardized_response(
                GenericResponseSerializer,
                name="IssueDeleted",
                description="The issue was deleted successfully."
            ),
            status.HTTP_404_NOT_FOUND: standardized_response(
                GenericResponseSerializer,
                name="IssueDeleteNotFound",
                success=False,
                description="The issue with the specified ID was not found."
            ),
        })
    def delete(self, request: Request, pk: int, *args, **kwargs) -> Response:
        self.debug(Messages.Delete.delete_one("issue", pk))
        issue = self.__get_object(pk)
        if issue is None:
            message = Messages.Delete.not_found("issue", pk)
            self.warning(message)
            return Response(
                data=GenericResponseSerializer(GenericResponse(message)).data, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        issue.delete()
        message = Messages.Delete.deleted_one("issue", pk)
        self.info(message)
        return Response(
            data=GenericResponseSerializer(GenericResponse(message)).data, 
            status=status.HTTP_200_OK
        )
        