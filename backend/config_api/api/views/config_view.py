from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiParameter

from common.api.messages import Messages
from common.api.serializers.generic_response import GenericResponse, GenericResponseSerializer
from common.core.schemas import standardized_response
from common.log.logger import Logger
from config_api.api.serializers.config_request_serializer import ConfigRequestSerializer
from config_api.api.serializers.config_response_serializer import ConfigResponseSerializer
from config_api.models import Config

class ConfigView(Logger, APIView):
    """Manages bulk API operations for Config instances.

    This view handles the retrieval of all configuration entries (GET) and the
    creation of a new configuration entry (POST).
    """
    serializer_class = ConfigResponseSerializer
    
    @extend_schema(
        operation_id="list_config_entries",
        tags=['Config Management'],
        summary="Retrieve Configuration Entries",
        description="Retrieves a list of configuration key-value pairs. Can be filtered by user ID to get user-specific settings. If no user ID is provided, it returns all settings.",
        parameters=[
            OpenApiParameter(
                name='user_id',
                type=int,
                location=OpenApiParameter.QUERY,
                description='Filter configuration entries by user ID. If not provided, all entries are returned.',
                required=False
            ),
        ],
        responses={
            200: standardized_response(
                ConfigResponseSerializer,
                name="GetConfigEntriesSuccess",
                many=True, 
                description="A list of configuration entries was successfully retrieved."
            ),
            403: standardized_response(
                ConfigResponseSerializer,
                name="GetConfigEntriesForbidden",
                success=False,
                description="Permission denied."
            )
        }
    )
    def get(self, request:Request, *args, **kwargs) -> Response:
        """Handles GET requests to retrieve configuration entries.

        Args:
            request (Request): The incoming HTTP request.

        Returns:
            Response:   A DRF Response object containing a list of all serialized
                        configuration entries (optionally filtered by user_id) 
                        and a 200 OK status.
        """
        self.log.debug(Messages.Get.retrieve_all("config entries"))
        
        user_id = request.query_params.get('user_id')
        if user_id:
            if user_id.isdigit():
                config = Config.objects.filter(user=user_id)
            else:
                # Return an empty queryset for non-numeric user_id to prevent ValueError
                config = Config.objects.none()
        else:
            config = Config.objects.all()

        self.log.debug(Messages.Get.retrieved_all("config entries", config.count()))
        response = ConfigResponseSerializer(config, many=True)
        
        return Response(
            data=response.data,
            status=status.HTTP_200_OK
            )
        
    @extend_schema(
        operation_id="create_config_entry",
        tags=['Config Management'],
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
            ),
            403: standardized_response(
                ConfigResponseSerializer,
                name="CreateConfigEntryForbidden",
                success=False,
                description="Permission denied."
            )
        }
    )
    def post(self, request:Request, *args, **kwargs) -> Response:
        """Handles POST requests to create a new configuration entry.

        Args:
            request (Request):  The incoming HTTP request containing the data for
                                the new configuration entry.

        Returns:
            Response:   A DRF Response with the newly created entry's data and a
                        201 Created status, or a 400 Bad Request on validation error.
        """
        self.log.debug(Messages.Post.create_one("config entry", request.data))
        config = ConfigRequestSerializer(data = request.data)
        
        if config.is_valid():
            instance = config.save()
            self.log.debug(Messages.Post.created_one("config entry", instance.id))
            return Response(
                data=ConfigResponseSerializer(instance).data,
                status=status.HTTP_201_CREATED
                )

        self.log.warning(Messages.Post.validation_failed("config entry", config.errors))
        return Response(
            data=GenericResponseSerializer(GenericResponse(config.errors)).data, 
            status=status.HTTP_400_BAD_REQUEST
        )
        