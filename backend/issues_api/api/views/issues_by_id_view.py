from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema

from issues_api.api.serializers.issue_response_serializer import IssueResponseSerializer
from common.log.logger import Logger
from issues_api.models import Issue
from issues_api.api.serializers.issue_request_serializer import IssueRequestSerializer
from common.api.messages import Messages
from common.core.schemas import standardized_response
from common.api.serializers.generic_response import GenericResponse, GenericResponseSerializer


@extend_schema(tags=['Database Management'])
class IssuesByIdView(Logger, APIView):
    """
    API view for handling individual Issue instances.

    This view provides GET, PUT, and DELETE operations for a specific
    issue identified by its primary key.
    """
    def __get_object(self, pk):
        """
        Helper method to retrieve an Issue object by its primary key.

        Args:
            pk: The primary key of the issue to retrieve.

        Returns:
            The Issue instance if found, otherwise None.
        """
        try:
            Messages.Database.querying("issue", pk) 
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
            status.HTTP_403_FORBIDDEN: standardized_response(
                IssueResponseSerializer,
                name="IssueRetrieveForbidden",
                success=False,
                description="Permission denied."
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
        """
        Handles GET requests to retrieve a single issue by its ID.

        Args:
            request: The incoming HTTP request.
            pk: The primary key of the issue to retrieve.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            A Response object containing the serialized issue data with a
            200 OK status, or a 404 Not Found if the issue does not exist.
        """
        self.log.debug(Messages.Get.retrieve_one("issue", pk))
        issue = self.__get_object(pk)
        if issue is None:
            message = Messages.Get.not_found("issue", pk)
            self.log.warning(message)
            return Response(data=GenericResponseSerializer(GenericResponse(message)).data, status=status.HTTP_404_NOT_FOUND)
        
        serializer = IssueResponseSerializer(issue)
        self.log.info(Messages.Get.retrieved_one("issue", pk))
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
            status.HTTP_403_FORBIDDEN: standardized_response(
                IssueResponseSerializer,
                name="IssueUpdateForbidden",
                success=False,
                description="Permission denied."
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
        """
        Handles PUT requests to update an existing issue.

        Args:
            request: The incoming HTTP request containing the update data.
            pk: The primary key of the issue to update.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            A Response object with the updated issue data and a 200 OK status
            if successful. Returns a 404 Not Found if the issue does not exist,
            or a 400 Bad Request if the provided data is invalid.
        """
        self.log.debug(Messages.Put.update_one("issue", pk, request.data))
        issue = self.__get_object(pk)
        if issue is None:
            message = Messages.Put.not_found("issue", pk)
            self.log.warning(message)
            return Response(
                data=GenericResponseSerializer(GenericResponse(message)).data, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = IssueRequestSerializer(issue, data=request.data, partial=True)
        if not serializer.is_valid():
            self.log.warning(Messages.Put.validation_failed("issue", pk, serializer.errors))
            return Response(
                data=GenericResponseSerializer(GenericResponse(serializer.errors)).data,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        instance = serializer.save()
        self.log.info(Messages.Put.updated_one("issue", instance.id))
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
            status.HTTP_403_FORBIDDEN: standardized_response(
                IssueResponseSerializer,
                name="IssueDeleteForbidden",
                success=False,
                description="Permission denied."
            ),
            status.HTTP_404_NOT_FOUND: standardized_response(
                GenericResponseSerializer,
                name="IssueDeleteNotFound",
                success=False,
                description="The issue with the specified ID was not found."
            ),
        })
    def delete(self, request: Request, pk: int, *args, **kwargs) -> Response:
        """
        Handles DELETE requests to remove an issue.

        Args:
            request: The incoming HTTP request.
            pk: The primary key of the issue to delete.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            A Response object with a success message and a 200 OK status if
            the deletion was successful, or a 404 Not Found if the issue does not exist.
        """
        self.log.debug(Messages.Delete.delete_one("issue", pk))
        issue = self.__get_object(pk)
        if issue is None:
            message = Messages.Delete.not_found("issue", pk)
            self.log.warning(message)
            return Response(
                data=GenericResponseSerializer(GenericResponse(message)).data, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        issue.delete()
        message = Messages.Delete.deleted_one("issue", pk)
        self.log.info(message)
        return Response(
            data=GenericResponseSerializer(GenericResponse(message)).data, 
            status=status.HTTP_200_OK
        )
        