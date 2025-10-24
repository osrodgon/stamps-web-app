from re import M
from common.api.messages import Messages
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema

from common.log.logger import Logger
from common.api.serializers.generic_response import GenericResponse, GenericResponseSerializer
from common.core.schemas import standardized_response
from colors_api.models import Color
from colors_api.api.serializers.color_response_serializer import ColorResponseSerializer
from colors_api.api.serializers.color_request_serializer import ColorRequestSerializer


class ColorsByIdView(Logger, APIView):
    serializer_class = ColorResponseSerializer
    def __get_color(self, pk: int) -> Color:
        try:
            self.debug(Messages.Database.querying("color", pk))
            return Color.objects.get(pk=pk)
        except Color.DoesNotExist:
            self.debug(Messages.Database.not_found("color", pk))
            return None
    
    @extend_schema(
        operation_id="retrieve_color",
        tags=['Database Management'],
        summary="Retrieve a Color by ID",
        description="Fetches the details of a specific color entry by its unique identifier.",
        responses={
            200: standardized_response(
                ColorResponseSerializer,
                name="ColorRetrieved",
                description="The requested color's data was retrieved successfully."
                ),
            404: standardized_response(
                GenericResponseSerializer,
                name="RetrieveColorNotFound",
                success=False,
                description="No color was found for the provided ID."
                ),
            403: standardized_response(
                ColorResponseSerializer,
                name="RetrieveColorForbidden",
                success=False,
                description="Permission denied."
                )   
        }
    )    
    def get(self, request: Request, pk: int, *args, **kwargs) -> Response:
        self.debug(Messages.Get.retrieve_one("color", pk))
        color = self.__get_color(pk)
        
        if color is None:
            message = Messages.Get.not_found("color", pk)
            self.warning(message)
            return Response(
                data=GenericResponseSerializer(GenericResponse(message)).data,
                status=status.HTTP_404_NOT_FOUND
                )
        
        response = ColorResponseSerializer(color)
        self.info(Messages.Get.retrieved_one("color", pk))
        return Response(
            data=response.data, 
            status=status.HTTP_200_OK
            )
    
    @extend_schema(
        operation_id="update_color",
        tags=['Database Management'],
        summary="Update a Color",
        description="Updates an existing color entry identified by its ID. A complete payload with all required fields is expected.",
        request=ColorRequestSerializer,
        responses={
            status.HTTP_200_OK: standardized_response(
                ColorResponseSerializer,
                name="ColorUpdated",
                description="The color was updated successfully."
                ),
            status.HTTP_400_BAD_REQUEST: standardized_response(
                GenericResponseSerializer,
                name="ColorUpdateInvalidPayload",
                success=False,
                description="The request payload was invalid."
                ),
            status.HTTP_403_FORBIDDEN: standardized_response(
                ColorResponseSerializer,
                name="ColorUpdateForbidden",
                success=False,
                description="Permission denied."
                ),    
            status.HTTP_404_NOT_FOUND: standardized_response(
                GenericResponseSerializer,
                name="ColorUpdateNotFound",
                success=False,
                description="The color with the specified ID was not found."
                )
        }
    )    
    def put(self, request: Request, pk: int, *args, **kwargs) -> Response:
        self.debug(Messages.Put.update_one("color", pk, request.data))
        color = self.__get_color(pk)
        if color is None:
            message = Messages.Put.not_found("color", pk)
            self.warning(message)
            return Response(
                data=GenericResponseSerializer(GenericResponse(message)).data,
                status=status.HTTP_404_NOT_FOUND
                )
        
        updated_color = ColorRequestSerializer(data=request.data, instance=color, partial=False)
        if updated_color.is_valid():
            instance = updated_color.save()
            self.info(Messages.Put.updated_one("color", instance.id))
            return Response(
                data=ColorResponseSerializer(instance).data,
                status=status.HTTP_200_OK
                )
        
        self.warning(Messages.Put.validation_failed("color", pk, updated_color.errors))
        return Response(
            data=GenericResponseSerializer(GenericResponse(updated_color.errors)).data,
            status=status.HTTP_400_BAD_REQUEST
            )
    
    @extend_schema(
        operation_id="delete_color",
        tags=['Database Management'],
        summary="Delete a Color",
        description="Deletes a color entry from the database using its ID.",
        responses={
            status.HTTP_200_OK: standardized_response(
                GenericResponseSerializer,
                name="ColorDeleted",
                success=True,
                description="The color was deleted successfully."
                ),
            status.HTTP_403_FORBIDDEN: standardized_response(
                ColorResponseSerializer,
                name="ColorDeleteForbidden",
                success=False,
                description="Permission denied."
                ),   
            status.HTTP_404_NOT_FOUND: standardized_response(
                GenericResponseSerializer,
                name="ColorDeleteNotFound",
                success=False,
                description="The color with the specified ID was not found."
                )
        }
    )    
    def delete(self, request: Request, pk: int, *args, **kwargs) -> Response:
        self.debug(Messages.Delete.delete_one("color", pk))
        color = self.__get_color(pk)
        if color is None:
            message = Messages.Delete.not_found("color", pk)
            self.warning(message)
            return Response(
                data=GenericResponseSerializer(GenericResponse(message)).data,
                status=status.HTTP_404_NOT_FOUND
                )
        
        color.delete()
        message = Messages.Delete.deleted_one("color", pk)
        self.info(message)
        return Response(
            data=GenericResponseSerializer(GenericResponse(message)).data,
            status=status.HTTP_200_OK
            )
