from functools import partial
import stat
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema

from common.api.messages import Messages
from common.api.serializers.generic_response import GenericResponse, GenericResponseSerializer
from common.log.logger import Logger
from common.core.schemas import standardized_response
from stamps_api.models import Stamp
from stamps_api.api.serializers.stamp_response_serializer import StampResponseSerializer
from stamps_api.api.serializers.stamp_request_serializer import StampRequestSerializer

class StampsByIdView(Logger, APIView):
    """
    API view for handling individual Stamp instances.

    This view provides GET, PUT, and DELETE operations for a specific
    stamp identified by its primary key.
    """
    serializer_class = StampResponseSerializer

    def __get_object(self, id):
        """
        Helper method to retrieve a Stamp object by its primary key.

        Args:
            id: The primary key of the stamp to retrieve.

        Returns:
            The Stamp instance if found, otherwise None.
        """
        try:
            return Stamp.objects.get(pk=id)
        except Stamp.DoesNotExist:
            return None

    @extend_schema(
        operation_id="retrieve_stamp",
        tags=['Database Management'],
        summary="Retrieve a Stamp by ID",
        description="Retrieves a single stamp entry by its unique ID.",
        responses={
            status.HTTP_200_OK: standardized_response(
                StampResponseSerializer,
                name="StampRetrieved",
                description="The stamp was retrieved successfully."
            ),
            status.HTTP_403_FORBIDDEN: standardized_response(
                StampResponseSerializer,
                name="StampRetrievePermissionDenied",
                success=False,
                description="Permission denied."
            ),
            status.HTTP_404_NOT_FOUND: standardized_response(
                GenericResponseSerializer,
                name="StampNotFound",
                success=False,
                description="The stamp with the specified ID was not found."
            )
        }
    )
    def get(self, request: Request, id: int, *args, **kwargs) -> Response:
        """
        Handles GET requests to retrieve a single stamp by its ID.

        Args:
            request: The incoming HTTP request.
            id: The primary key of the stamp to retrieve.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            A Response object containing the serialized stamp data with a
            200 OK status, or a 404 Not Found if the stamp does not exist.
        """
        self.log.debug(Messages.Get.retrieve_one("stamp", id))
        stamp = self.__get_object(id)
        
        if stamp is None:
            message=Messages.Get.not_found("stamp", id)
            self.log.warning(message)
            return Response(
                data=GenericResponseSerializer(GenericResponse(message)).data,
                status=status.HTTP_404_NOT_FOUND
            )
        
        self.log.debug(Messages.Get.retrieved_one("stamp", id))
        serializer = StampResponseSerializer(stamp)
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        operation_id="update_stamp",
        tags=['Database Management'],
        summary="Update a Stamp",
        description="Updates an existing stamp entry by its ID. The request body should contain the fields to be updated.",
        request=StampRequestSerializer,
        responses={
            status.HTTP_200_OK: standardized_response(
                StampResponseSerializer,
                name="StampUpdated",
                description="The stamp was updated successfully."
            ),
            status.HTTP_400_BAD_REQUEST: standardized_response(
                GenericResponseSerializer,
                name="StampUpdateInvalidPayload",
                success=False,
                description="The request payload was invalid."
            ),
            status.HTTP_403_FORBIDDEN: standardized_response(
                StampResponseSerializer,
                name="StampUpdatePermissionDenied",
                success=False,
                description="Permission denied."
            ),
            status.HTTP_404_NOT_FOUND: standardized_response(
                GenericResponseSerializer,
                name="StampUpdateNotFound",
                success=False,
                description="The stamp with the specified ID was not found."
            )
        }
    )
    def put(self, request: Request, id: int, *args, **kwargs) -> Response:
        """
        Handles PUT requests to update an existing stamp.

        Args:
            request: The incoming HTTP request containing the update data.
            id: The primary key of the stamp to update.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            A Response object with the updated stamp data and a 200 OK status
            if successful. Returns a 404 Not Found if the stamp does not exist,
            or a 400 Bad Request if the provided data is invalid.
        """
        self.log.debug(Messages.Put.update_one("stamp", id, request.data))
        stamp = self.__get_object(id)
        if stamp is None:
            message = Messages.Put.not_found("stamp", id)
            self.log.warning(message)
            return Response(
                data=GenericResponseSerializer(GenericResponse(message)).data,
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = StampRequestSerializer(stamp, data=request.data, partial=True)
        if serializer.is_valid():
            instance = serializer.save()
            self.log.info(Messages.Put.updated_one("stamp", instance.id))
            return Response(
                data=StampResponseSerializer(instance).data,
                status=status.HTTP_200_OK
            )
        
        self.log.warning(Messages.Put.validation_failed("stamp", id, serializer.errors))
        return Response(
            data=GenericResponseSerializer(GenericResponse(serializer.errors)).data,
            status=status.HTTP_400_BAD_REQUEST
        )

    @extend_schema(
        operation_id="delete_stamp",
        tags=['Database Management'],
        summary="Delete a Stamp",
        description="Deletes a stamp entry by its ID.",
        responses={
            status.HTTP_200_OK: standardized_response(
                GenericResponseSerializer,
                name="StampDeleted",
                description="The stamp was deleted successfully."
            ),
            status.HTTP_403_FORBIDDEN: standardized_response(
                StampResponseSerializer,
                name="StampDeletePermissionDenied",
                success=False,
                description="Permission denied."
            ),
            status.HTTP_404_NOT_FOUND: standardized_response(
                GenericResponseSerializer,
                name="StampDeleteNotFound",
                success=False,
                description="The stamp with the specified ID was not found."
            )
        }
    )
    def delete(self, request: Request, id: int, *args, **kwargs) -> Response:
        """
        Handles DELETE requests to remove a stamp.

        Args:
            request: The incoming HTTP request.
            id: The primary key of the stamp to delete.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            A Response object with a success message and a 200 OK status if
            the deletion was successful, or a 404 Not Found if the stamp does not exist.
        """
        self.log.debug(Messages.Delete.delete_one("stamp", id))
        stamp = self.__get_object(id)
        if stamp is None:
            message = Messages.Delete.not_found("stamp", id)
            self.log.warning(message)
            return Response(
                data=GenericResponseSerializer(GenericResponse(message)).data,
                status=status.HTTP_404_NOT_FOUND
            )

        stamp.delete()
        message = Messages.Delete.deleted_one("stamp", id)
        self.log.info(message)
        return Response(
            data=GenericResponseSerializer(GenericResponse(message)).data,
            status=status.HTTP_200_OK
        )