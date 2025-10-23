from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework import status
from drf_spectacular.utils import extend_schema


from common.api.messages import Messages
from common.api.serializers.generic_response import GenericResponse, GenericResponseSerializer
from common.core.schemas import standardized_response
from common.log.logger import Logger
from config_api.api.serializers.config_request_serializer import ConfigRequestSerializer
from config_api.api.serializers.config_response_serializer import ConfigResponseSerializer
from config_api.models import Config


class ConfigByIdView(Logger, APIView):
    serializer_class = ConfigResponseSerializer
    
    def __get_config(self, pk: int) -> Config:
        try:
            Messages.Database.querying("config", pk)
            return Config.objects.get(pk=pk)
        except Config.DoesNotExist:
            Messages.Database.not_found("config", pk)
            return None
        
    @extend_schema(
        operation_id="retrieve_config_entry",
        tags=['Config Management'],
        summary="Retrieve a Configuration Entry by ID",
        description="Fetches a specific configuration entry using its unique ID. Returns the entry's details if found.",
        responses={
            status.HTTP_200_OK: standardized_response(
                ConfigResponseSerializer,
                name="GetConfigEntrySuccess",
                description="The configuration entry was retrieved successfully."
            ),
            status.HTTP_403_FORBIDDEN: standardized_response(
                ConfigResponseSerializer,
                name="GetConfigEntryForbidden",
                success=False,
                description="Permission denied. You're likely missing X-API-Key header."
            ),
            status.HTTP_404_NOT_FOUND: standardized_response(
                GenericResponseSerializer,
                name="GetConfigEntryNotFound",
                success=False,
                description="No configuration entry was found for the provided ID."
            )
        }
    )
    def get(self, request: Request, pk: int, *args, **kwargs) -> Response:
        self.debug(Messages.Get.retrieve_one("config entry", pk))
        config = self.__get_config(pk)
        if config is None:
            message = Messages.Get.not_found("config entry", pk)
            self.warning(message)
            return Response(
                data=GenericResponseSerializer(GenericResponse(message)).data, 
                status=status.HTTP_404_NOT_FOUND
                )
        
        response = ConfigResponseSerializer(config)
        self.info(Messages)
        return Response(
            data=response.data, 
            status=status.HTTP_200_OK
            )
    
    @extend_schema(
        operation_id="update_config_entry",
        tags=['Config Management'],
        summary="Update a Configuration Entry",
        description="Updates an existing configuration entry identified by its ID. The request body can contain a partial or full update of the entry's fields.",
        request=ConfigRequestSerializer,
        responses={
            status.HTTP_200_OK: standardized_response(
                ConfigResponseSerializer,
                name="UpdateConfigEntrySuccess",
                description="The configuration entry was updated successfully."
            ),
            status.HTTP_400_BAD_REQUEST: standardized_response(
                GenericResponseSerializer,
                name="UpdateConfigEntryBadRequest",
                success=False,
                description="The request payload was invalid."
            ),
            status.HTTP_403_FORBIDDEN: standardized_response(
                ConfigResponseSerializer,
                name="UpdateConfigEntryForbidden",
                success=False,
                description="Permission denied. You're likely missing X-API-Key header."
            ),
            status.HTTP_404_NOT_FOUND: standardized_response(
                GenericResponseSerializer,
                name="UpdateConfigEntryNotFound",
                success=False,
                description="The configuration entry with the specified ID was not found."
            )
        }
    )
    def put(self, request: Request, pk: int, *args, **kwargs) -> Response:
        self.debug(Messages.Put.update_one("config entry", pk, request.data))
        config = self.__get_config(pk)
        
        if config is None:
            message = Messages.Put.not_found("config entry", pk)
            self.warning(message)
            return Response(
                data=GenericResponseSerializer(GenericResponse(message)).data, 
                status=status.HTTP_404_NOT_FOUND
                )
            
        updated_config = ConfigRequestSerializer(data=request.data, instance=config, partial=True)
        if updated_config.is_valid():
            instance = updated_config.save()
            self.info(Messages.Put.updated_one("config entry", pk))
            return Response(
                data=ConfigResponseSerializer(instance).data,
                status=status.HTTP_200_OK
                )
        
        self.warning(Messages.Put.validation_failed("config entry", pk, updated_config.errors))
        return  Response(
            data=GenericResponseSerializer(GenericResponse(updated_config.errors)).data, 
            status=status.HTTP_400_BAD_REQUEST
        )

    @extend_schema(
        operation_id="delete_config_entry",
        tags=['Config Management'],
        summary="Delete a Configuration Entry",
        description="Permanently removes a configuration entry from the database using its ID.",
        responses={
            status.HTTP_200_OK: standardized_response(
                GenericResponseSerializer,
                name="DeleteConfigEntrySuccess", 
                description="The configuration entry was deleted successfully."
            ),
            status.HTTP_403_FORBIDDEN: standardized_response(
                ConfigResponseSerializer,
                name="DeleteConfigEntryForbidden",
                success=False,
                description="Permission denied. You're likely missing X-API-Key header."
            ),
            status.HTTP_404_NOT_FOUND: standardized_response(
                GenericResponseSerializer,
                name="DeleteConfigEntryNotFound",
                success=False,
                description="The configuration entry with the specified ID was not found."
            )
        }
    )
    def delete(self, request: Request, pk: int, *args, **kwargs) -> Response:
        self.debug(f"Attempting to delete config entry for id: {pk}")
        config = self.__get_config(pk)
        
        if config is None:
            message = Messages.Delete.not_found("config entry", pk)
            self.warning(message)
            return Response(
                data=GenericResponseSerializer(GenericResponse(message)).data, 
                status=status.HTTP_404_NOT_FOUND
                )
            
        config.delete()
        message = Messages.Delete.deleted_one("config entry", pk)
        self.info(message)
        return Response(
            data=GenericResponseSerializer(GenericResponse(message)).data,
            status=status.HTTP_200_OK
            )