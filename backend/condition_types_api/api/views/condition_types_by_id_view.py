from common.api.messages import Messages
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema

from common.log.logger import Logger
from common.api.serializers.generic_response import GenericResponse, GenericResponseSerializer
from common.core.schemas import standardized_response
from condition_types_api.models import ConditionType
from condition_types_api.api.serializers.condition_type_response_serializer import ConditionTypeResponseSerializer
from condition_types_api.api.serializers.condition_type_request_serializer import ConditionTypeRequestSerializer


class ConditionTypesByIdView(Logger, APIView):
    serializer_class = ConditionTypeResponseSerializer
    def __get_condition_type(self, pk: int) -> ConditionType:
        try:
            self.debug(Messages.Database.querying("condition type", pk))
            return ConditionType.objects.get(pk=pk)
        except ConditionType.DoesNotExist:
            self.debug(Messages.Database.not_found("condition type", pk))
            return None
    
    @extend_schema(
        operation_id="retrieve_condition_type",
        tags=['Condition Types'],
        summary="Retrieve a Condition Type by ID",
        description="Fetches the details of a specific condition type entry by its unique identifier.",
        responses={
            200: standardized_response(
                ConditionTypeResponseSerializer,
                name="ConditionTypeRetrieved",
                description="The requested condition type's data was retrieved successfully."
                ),
            404: standardized_response(
                GenericResponseSerializer,
                name="RetrieveConditionTypeNotFound",
                success=False,
                description="No condition type was found for the provided ID."
                ),
            403: standardized_response(
                ConditionTypeResponseSerializer,
                name="RetrieveConditionTypeForbidden",
                success=False,
                description="Permission denied. You're likely missing X-API-Key header."
                )   
        }
    )    
    def get(self, request: Request, pk: int, *args, **kwargs) -> Response:
        self.debug(Messages.Get.retrieve_one("condition type", pk))
        condition_type = self.__get_condition_type(pk)
        
        if condition_type is None:
            message = Messages.Get.not_found("condition type", pk)
            self.warning(message)
            return Response(
                data=GenericResponseSerializer(GenericResponse(message)).data,
                status=status.HTTP_404_NOT_FOUND
                )
        
        response = ConditionTypeResponseSerializer(condition_type)
        self.info(Messages.Get.retrieved_one("condition type", pk))
        return Response(
            data=response.data, 
            status=status.HTTP_200_OK
            )
    
    @extend_schema(
        operation_id="update_condition_type",
        tags=['Condition Types'],
        summary="Update a Condition Type",
        description="Updates an existing condition type entry identified by its ID. A complete payload with all required fields is expected.",
        request=ConditionTypeRequestSerializer,
        responses={
            status.HTTP_200_OK: standardized_response(
                ConditionTypeResponseSerializer,
                name="ConditionTypeUpdated",
                description="The condition type was updated successfully."
                ),
            status.HTTP_400_BAD_REQUEST: standardized_response(
                GenericResponseSerializer,
                name="ConditionTypeUpdateInvalidPayload",
                success=False,
                description="The request payload was invalid."
                ),
            status.HTTP_403_FORBIDDEN: standardized_response(
                ConditionTypeResponseSerializer,
                name="ConditionTypeUpdateForbidden",
                success=False,
                description="Permission denied. You're likely missing X-API-Key header."
                ),    
            status.HTTP_404_NOT_FOUND: standardized_response(
                GenericResponseSerializer,
                name="ConditionTypeUpdateNotFound",
                success=False,
                description="The condition type with the specified ID was not found."
                )
        }
    )    
    def put(self, request: Request, pk: int, *args, **kwargs) -> Response:
        self.debug(Messages.Put.update_one("condition type", pk, request.data))
        condition_type = self.__get_condition_type(pk)
        if condition_type is None:
            message = Messages.Put.not_found("condition type", pk)
            self.warning(message)
            return Response(
                data=GenericResponseSerializer(GenericResponse(message)).data,
                status=status.HTTP_404_NOT_FOUND
                )
        
        updated_condition_type = ConditionTypeRequestSerializer(data=request.data, instance=condition_type, partial=False)
        if updated_condition_type.is_valid():
            instance = updated_condition_type.save()
            self.info(Messages.Put.updated_one("condition type", instance.id))
            return Response(
                data=ConditionTypeResponseSerializer(instance).data,
                status=status.HTTP_200_OK
                )
        
        self.warning(Messages.Put.validation_failed("condition type", pk, updated_condition_type.errors))
        return Response(
            data=GenericResponseSerializer(GenericResponse(updated_condition_type.errors)).data,
            status=status.HTTP_400_BAD_REQUEST
            )
    
    @extend_schema(
        operation_id="delete_condition_type",
        tags=['Condition Types'],
        summary="Delete a Condition Type",
        description="Deletes a condition type entry from the database using its ID.",
        responses={
            status.HTTP_200_OK: standardized_response(
                GenericResponseSerializer,
                name="ConditionTypeDeleted",
                success=True,
                description="The condition type was deleted successfully."
                ),
            status.HTTP_403_FORBIDDEN: standardized_response(
                ConditionTypeResponseSerializer,
                name="ConditionTypeDeleteForbidden",
                success=False,
                description="Permission denied. You're likely missing X-API-Key header."
                ),   
            status.HTTP_404_NOT_FOUND: standardized_response(
                GenericResponseSerializer,
                name="ConditionTypeDeleteNotFound",
                success=False,
                description="The condition type with the specified ID was not found."
                )
        }
    )    
    def delete(self, request: Request, pk: int, *args, **kwargs) -> Response:
        self.debug(Messages.Delete.delete_one("condition type", pk))
        condition_type = self.__get_condition_type(pk)
        if condition_type is None:
            message = Messages.Delete.not_found("condition type", pk)
            self.warning(message)
            return Response(
                data=GenericResponseSerializer(GenericResponse(message)).data,
                status=status.HTTP_404_NOT_FOUND
                )
        
        condition_type.delete()
        message = Messages.Delete.deleted_one("condition type", pk)
        self.info(message)
        return Response(
            data=GenericResponseSerializer(GenericResponse(message)).data,
            status=status.HTTP_200_OK
            )