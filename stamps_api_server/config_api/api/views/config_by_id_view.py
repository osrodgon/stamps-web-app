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


class ConfigByIdView(Logger, APIView):
    def __get_config__(self, pk: int) -> Config:
        try:
            return Config.objects.get(pk=pk)
        except Config.DoesNotExist:
            return None
        except Exception as e:
            self.warning(f"An unknown error has occurred: {str(e)}")
            return None
        

    def get(self, request: Request, pk: int, *args, **kwargs) -> Response:
        self.debug(f"Getting config entry for id: {pk})")
        config = self.__get_config__(pk)
        if config is None:
            message = f"Config entry for id: {pk} not found"
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
    
    def put(self, request: Request, pk: int, *args, **kwargs) -> Response:
        self.debug(f"Updating config entry for id: {pk})")
    
        config = self.__get_config__(pk)
        
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