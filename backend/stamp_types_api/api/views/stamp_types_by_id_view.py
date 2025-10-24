import stat
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema

from common.api.messages import Messages
from common.log.logger import Logger
from common.api.serializers.generic_response import GenericResponse, GenericResponseSerializer
from common.core.schemas import standardized_response
from stamp_types_api.models import StampType
from stamp_types_api.api.serializers.stamp_type_response_serializer import StampTypeResponseSerializer
from stamp_types_api.api.serializers.stamp_type_request_serializer import StampTypeRequestSerializer


class StampTypesByIdView(Logger, APIView):
    serializer_class = StampTypeResponseSerializer
    
    def __get_stamp_type(self, pk: int) -> StampType:
        try:
            Messages.Database.querying("StampType", pk)
            return StampType.objects.get(pk=pk)
        except StampType.DoesNotExist:
            Messages.Database.not_found("StampType", pk)
            return None
    
    @extend_schema(
        operation_id="retrieve_stamp_type",
        tags=['Database Management'],
        summary="Retrieve a Stamp Type by ID",
        description="Fetches the details of a specific stamp type entry by its unique identifier.",
        responses={
            status.HTTP_200_OK: standardized_response(
                StampTypeResponseSerializer,
                name="StampTypeRetrieved",
                description="The requested stamp type's data was retrieved successfully."
                ),
            status.HTTP_403_FORBIDDEN: standardized_response(
                StampTypeResponseSerializer,
                name="StampTypeRetrieveForbidden",
                success=False,
                description="Permission denied."
            ),
            status.HTTP_404_NOT_FOUND: standardized_response(
                GenericResponseSerializer,
                name="RetrieveStampTypeNotFound",
                success=False,
                description="No stamp type was found for the provided ID."
                ) 
        }
    )    
    def get(self, request: Request, pk: int, *args, **kwargs) -> Response:
        self.debug(Messages.Get.retrieve_one("StampType", pk))
        stamp_type = self.__get_stamp_type(pk)
        
        if stamp_type is None:
            message = Messages.Get.not_found("StampType", pk)
            self.warning(message)
            return Response(
                data=GenericResponseSerializer(GenericResponse(message)).data,
                status=status.HTTP_404_NOT_FOUND
                )
        
        response = StampTypeResponseSerializer(stamp_type)
        self.info(Messages.Get.retrieved_one("StampType", pk))
        return Response(
            data=response.data, 
            status=status.HTTP_200_OK
            )
    
    @extend_schema(
        operation_id="update_stamp_type",
        tags=['Database Management'],
        summary="Update a Stamp Type",
        description="Updates an existing stamp type entry identified by its ID. A complete payload with all required fields is expected.",
        request=StampTypeRequestSerializer,
        responses={
            status.HTTP_200_OK: standardized_response(
                StampTypeResponseSerializer,
                name="StampTypeUpdated",
                description="The stamp type was updated successfully."
                ),
            status.HTTP_403_FORBIDDEN: standardized_response(
                StampTypeResponseSerializer,
                name="StampTypeUpdateForbidden",
                success=False,
                description="Permission denied."
            ),
            status.HTTP_404_NOT_FOUND: standardized_response(
                GenericResponseSerializer,
                name="StampTypeUpdateNotFound",
                success=False,
                description="The stamp type with the specified ID was not found."
                ),
            status.HTTP_400_BAD_REQUEST: standardized_response(
                GenericResponseSerializer,
                name="StampTypeUpdateInvalidPayload",
                success=False,
                description="The request payload was invalid."
                )   
        }
    )    
    def put(self, request: Request, pk: int, *args, **kwargs) -> Response:
        self.debug(Messages.Put.update_one("StampType", pk, request.data))
        stamp_type = self.__get_stamp_type(pk)
        if stamp_type is None:
            message = Messages.Put.not_found("StampType", pk)
            self.warning(message)
            return Response(
                data=GenericResponseSerializer(GenericResponse(message)).data,
                status=status.HTTP_404_NOT_FOUND
                )
        
        updated_stamp_type = StampTypeRequestSerializer(data=request.data, instance=stamp_type, partial=False)
        if updated_stamp_type.is_valid():
            instance=updated_stamp_type.save()
            self.info(Messages.Put.updated_one("StampType", instance.id))
            return Response(
                data=StampTypeResponseSerializer(instance).data,
                status=status.HTTP_200_OK
                )
        
        self.warning(Messages.Put.validation_failed("StampType", pk, updated_stamp_type.errors))
        return Response(
            data=GenericResponseSerializer(GenericResponse(updated_stamp_type.errors)).data,
            status=status.HTTP_400_BAD_REQUEST
            )
    
    @extend_schema(
        operation_id="delete_stamp_type",
        tags=['Database Management'],
        summary="Delete a Stamp Type",
        description="Deletes a stamp type entry from the database using its ID.",
        responses={
            status.HTTP_200_OK: standardized_response(
                GenericResponseSerializer,
                name="StampTypeDeleted",
                success=True,
                description="The stamp type was deleted successfully."
                ),
            status.HTTP_403_FORBIDDEN: standardized_response(
                StampTypeResponseSerializer,
                name="StampTypeDeleteForbidden",
                success=False,
                description="Permission denied."
            ),
            status.HTTP_404_NOT_FOUND: standardized_response(
                GenericResponseSerializer,
                name="StampTypeDeleteNotFound",
                success=False,
                description="The stamp type with the specified ID was not found."
                )
        }
    )    
    def delete(self, request: Request, pk: int, *args, **kwargs) -> Response:
        self.debug(Messages.Delete.delete_one("StampType", pk))
        stamp_type = self.__get_stamp_type(pk)
        if stamp_type is None:
            message=Messages.Delete.not_found("StampType", pk)
            self.warning(message)
            return Response(
                data=GenericResponseSerializer(GenericResponse(message)).data,
                status=status.HTTP_404_NOT_FOUND
                )
        
        stamp_type.delete()
        message = Messages.Delete.deleted_one("StampType", pk)
        self.info(message)
        return Response(
            data=GenericResponseSerializer(GenericResponse(message)).data,
            status=status.HTTP_200_OK
            )