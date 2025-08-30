from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

from common.api.serializers.generic_response import GenericResponse, GenericResponseSerializer
from common.core.schemas import standardized_response
from common.log.logger import Logger
from config_api.api.serializers.config_request_serializer import ConfigRequestSerializer
from config_api.api.serializers.config_response_serializer import ConfigResponseSerializer
from config_api.models import Config

class ConfigView(Logger, APIView):
    @extend_schema(
        tags=['Config'],
        summary="List All Configuration Entries",
        description="Retrieves a comprehensive list of all configuration key-value pairs stored in the system. This is useful for a complete overview of all settings.",
        responses={
            200: standardized_response(
                ConfigResponseSerializer,
                name="GetAllConfigEntriesSuccess",
                many=True, 
                description="A list of all configuration entries was successfully retrieved."
            )
        }
    )
    def get(self, request:Request, *args, **kwargs) -> Response:
        self.debug("Attempting to retrieve all config entries.")
        config = Config.objects.all()
        self.debug(f"Found {len(config)} config entries.")
        response = ConfigResponseSerializer(config, many=True)
        
        return Response(
            data=response.data,
            status=status.HTTP_200_OK
            )
        
    @extend_schema(
        tags=['Config'],
        summary="Create a Configuration Entry",
        description="Adds a new configuration key-value pair to the database. The request body must contain the 'property' and 'value' for the new setting.",
        request=ConfigRequestSerializer,
        responses={
            201: standardized_response(
                ConfigResponseSerializer,
                name="CreateConfigEntrySuccess",
                description="The configuration entry was created successfully."
            ),
            400: standardized_response(
                GenericResponseSerializer,
                name="CreateConfigEntryBadRequest",
                success=False,
                description="The request payload was invalid or missing required fields."
            )
        }
    )
    def post(self, request:Request, *args, **kwargs) -> Response:
        self.debug(f"Attempting to create a new config entry with payload: {request.data}")
        config = ConfigRequestSerializer(data = request.data)
        
        if config.is_valid():
            instance = config.save()
            self.debug(f"Successfully created config entry with id: {instance.id}")
            return Response(
                data=ConfigResponseSerializer(instance).data,
                status=status.HTTP_201_CREATED
                )

        self.warning(f"Payload validation failed for new config entry: {config.errors}")
        return Response(
            data=GenericResponseSerializer(GenericResponse(config.errors)).data, 
            status=status.HTTP_400_BAD_REQUEST
        )