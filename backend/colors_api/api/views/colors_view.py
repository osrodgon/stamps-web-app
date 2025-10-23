import stat
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema

from common.api.messages import Messages
from common.api.serializers.generic_response import GenericResponseSerializer, GenericResponse
from common.log.logger import Logger
from common.core.schemas import standardized_response
from colors_api.models import Color
from colors_api.api.serializers.color_response_serializer import ColorResponseSerializer
from colors_api.api.serializers.color_request_serializer import ColorRequestSerializer

class ColorsView(Logger, APIView):
    serializer_class = ColorResponseSerializer
    
    @extend_schema(
        operation_id="list_colors",
        tags=['Database Management'],
        summary="List All Colors",
        description="Retrieves a list of all color entries currently stored in the database.",
        responses={
            200: standardized_response(
                ColorResponseSerializer, 
                name="ColorsRetrieved",
                description="A list of colors was successfully retrieved.",
                many=True
                ),
            403: standardized_response(
                ColorResponseSerializer,
                name="ColorsForbidden",
                success=False,
                description="Permission denied. You're likely missing X-API-Key header."
                )   
        }
    )
    def get(self, request:Request, *args, **kwargs) -> Response:
        self.debug(Messages.Get.retrieve_all("colors"))
        colors = Color.objects.all()
        self.debug(Messages.Get.retrieved_all("colors", colors.count()))
        response = ColorResponseSerializer(colors, many=True)
        
        return Response(
            data=response.data, 
            status=status.HTTP_200_OK
            )
    
    @extend_schema(
        operation_id="create_color",
        tags=['Database Management'],
        summary="Create a New Color",
        description="Adds a new color entry to the database. A successful creation returns the newly created color object with a 201 Created status code.",
        request=ColorRequestSerializer,
        responses={
            status.HTTP_201_CREATED: standardized_response(
                ColorResponseSerializer,
                name="ColorCreated",
                description="The color was created successfully."
                ),
            status.HTTP_400_BAD_REQUEST: standardized_response(
                GenericResponseSerializer,
                name="ColorCreateInvalidPayload",
                success=False,
                description="The request payload was invalid (e.g., missing a required field)."
                ),
            status.HTTP_403_FORBIDDEN: standardized_response(
                ColorResponseSerializer,
                name="ColorCreateForbidden",
                success=False,
                description="Permission denied. You're likely missing X-API-Key header."
                )   
        }
    )
    def post(self, request:Request, *args, **kwargs) -> Response:
        self.debug(Messages.Post.create_one("color", request.data))
        color = ColorRequestSerializer(data = request.data)
        
        if color.is_valid():
            instance = color.save()
            self.info(Messages.Post.created_one("color", instance.id))
            return Response(
                data=ColorResponseSerializer(instance).data, 
                status=status.HTTP_201_CREATED
                )
        
        self.warning(Messages.Post.validation_failed("color", color.errors))
        return Response(
            data=GenericResponseSerializer(GenericResponse(color.errors)).data,
            status=status.HTTP_400_BAD_REQUEST
            )
