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
    serializer_class = StampResponseSerializer

    def __get_object(self, id):
        try:
            return Stamp.objects.get(pk=id)
        except Stamp.DoesNotExist:
            return None

    @extend_schema(
        operation_id="retrieve_stamp",
        tags=['Stamps'],
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
                description="Permission denied. You're likely missing X-API-Key or X-API-User headers."
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
        self.debug(Messages.Get.retrieve_one("stamp", id))
        stamp = self.__get_object(id)
        
        if stamp is None:
            message=Messages.Get.not_found("stamp", id)
            self.warning(message)
            return Response(
                data=GenericResponseSerializer(GenericResponse(message)).data,
                status=status.HTTP_404_NOT_FOUND
            )
        
        self.debug(Messages.Get.retrieved_one("stamp", id))
        serializer = StampResponseSerializer(stamp)
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        operation_id="update_stamp",
        tags=['Stamps'],
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
                description="Permission denied. You're likely missing X-API-Key or X-API-User headers."
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
        self.debug(Messages.Put.update_one("stamp", id, request.data))
        stamp = self.__get_object(id)
        if stamp is None:
            message = Messages.Put.not_found("stamp", id)
            self.warning(message)
            return Response(
                data=GenericResponseSerializer(GenericResponse(message)).data,
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = StampRequestSerializer(stamp, data=request.data, partial=True)
        if serializer.is_valid():
            instance = serializer.save()
            self.info(Messages.Put.updated_one("stamp", instance.id))
            return Response(
                data=StampResponseSerializer(instance).data,
                status=status.HTTP_200_OK
            )
        
        self.warning(Messages.Put.validation_failed("stamp", id, serializer.errors))
        return Response(
            data=GenericResponseSerializer(GenericResponse(serializer.errors)).data,
            status=status.HTTP_400_BAD_REQUEST
        )

    @extend_schema(
        operation_id="delete_stamp",
        tags=['Stamps'],
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
                description="Permission denied. You're likely missing X-API-Key or X-API-User headers."
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
        self.debug(Messages.Delete.delete_one("stamp", id))
        stamp = self.__get_object(id)
        if stamp is None:
            message = Messages.Delete.not_found("stamp", id)
            self.warning(message)
            return Response(
                data=GenericResponseSerializer(GenericResponse(message)).data,
                status=status.HTTP_404_NOT_FOUND
            )

        stamp.delete()
        message = Messages.Delete.deleted_one("stamp", id)
        self.info(message)
        return Response(
            data=GenericResponseSerializer(GenericResponse(message)).data,
            status=status.HTTP_200_OK
        )