from email import message
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework import status


from common.api.serializers.generic_response import GenericResponse
from common.log.logger import Logger
from config_api.api.serializers.config_request_serializer import ConfigRequestSerializer
from config_api.api.serializers.config_response_serializer import ConfigResponseSerializer
from config_api.models import Config


class ConfigByPropertyView(Logger, APIView):
    def __get_config__(self, property: str) -> Config:
        try:
            return Config.objects.get(property=property)
        except Config.DoesNotExist:
            return None
        except Exception as e:
            self.warning(f"An unknown error has occurred: {str(e)}")
            return None
        
    def __validate_payload__(self, payload: dict):
        self.debug(f"Validating payload: {payload}")
        
        message = None
        if payload.get("property") is not None:
            message = "Field 'property' is not allowed."
            self.debug(message)
            return message
        
        if payload.get("value") is None:
            message = "Field 'value' is required."
            self.debug(message)
            return message
        
        return message

    def get(self, request: Request, property: str, *args, **kwargs) -> Response:
        self.debug(f"Getting config entry for property: {property})")
        config = self.__get_config__(property)
        if config is None:
            message = f"Config entry for property: {property} not found"
            self.debug(message)
            return Response(
                data=GenericResponse(message).data, 
                status=status.HTTP_404_NOT_FOUND
                )
        
        response = ConfigResponseSerializer(config)
        self.debug(f"Config entry found: {response.data}")
        return Response(
            data=response.data, 
            status=status.HTTP_200_OK
            )
    
    def put(self, request: Request, property: str, *args, **kwargs) -> Response:
        self.debug(f"Updating config entry for property: {property})")
        
        message = self.__validate_payload__(request.data)
        if message is not None:
            return Response(
                data=GenericResponse(message).data,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        config = self.__get_config__(property)
        
        if config is None:
            message = "Config entry not found"
            self.debug(message)
            return Response(
                data=GenericResponse(message).data, 
                status=status.HTTP_404_NOT_FOUND
                )
            
        updated_config = ConfigRequestSerializer(data=request.data, instance=config, partial=True)
        if updated_config.is_valid():
            updated_config.save()
            return Response(
                data=updated_config.data, 
                status=status.HTTP_200_OK
                )
            
        return  Response(
            data=updated_config.errors, 
            status=status.HTTP_400_BAD_REQUEST
        )
        
    def delete(self, request: Request, property: str, *args, **kwargs) -> Response:
        self.debug(f"Deleting config entry for property: {property})")
        config = self.__get_config__(property)
        
        if config is None:
            message = "Config entry not found"
            self.debug(message)
            return Response(
                data=GenericResponse(message).data, 
                status=status.HTTP_404_NOT_FOUND
                )
            
        config.delete()
        return Response(
            data=GenericResponse("Config entry deleted").data, 
            status=status.HTTP_200_OK
            )