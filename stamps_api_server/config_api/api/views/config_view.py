from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView

from common.log.logger import Logger
from config_api.api.serializers.config_request_serializer import ConfigRequestSerializer
from config_api.api.serializers.config_response_serializer import ConfigResponseSerializer
from config_api.models import Config

class ConfigView(Logger, APIView):
    def get(self, request:Request, *args, **kwargs) -> Response:
        self.debug("Getting all config entries")
        config = Config.objects.all()
        response = ConfigResponseSerializer(config, many=True)
        
        return Response(
            data=response.data, 
            status=status.HTTP_200_OK
            )
        
    def post(self, request:Request, *args, **kwargs) -> Response:
        self.debug(f"Create a new config entry: {request.data}")
        config = ConfigRequestSerializer(data = request.data)
        
        if config.is_valid():
            config.save()
            return Response(
                data=config.data, 
                status=status.HTTP_201_CREATED
                )

        self.debug(f"Payload validaton error: {config.errors}")
        return Response(
            data=config.errors, 
            status=status.HTTP_400_BAD_REQUEST
        )