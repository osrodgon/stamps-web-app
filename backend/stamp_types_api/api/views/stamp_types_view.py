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
from stamp_types_api.models import StampType
from stamp_types_api.api.serializers.stamp_type_response_serializer import StampTypeResponseSerializer
from stamp_types_api.api.serializers.stamp_type_request_serializer import StampTypeRequestSerializer


class StampTypesView(Logger, APIView):
    serializer_class = StampTypeResponseSerializer
    
    @extend_schema(
        operation_id="list_stamp_types",
        tags=['Stamp Types'],
        summary="List All Stamp Types",
        description="Retrieves a list of all stamp type entries currently stored in the database.",
        responses={
            status.HTTP_200_OK: standardized_response(
                StampTypeResponseSerializer, 
                name="StampTypesRetrieved",
                description="A list of stamp types was successfully retrieved.",
                many=True
                ),
            status.HTTP_403_FORBIDDEN: standardized_response(
                StampTypeResponseSerializer,
                name="StampTypesRetrieveForbidden",
                success=False,
                description="Permission denied. You're likely missing X-API-Key header."
            )
        }
    )
    def get(self, request:Request, *args, **kwargs) -> Response:
        self.debug(Messages.Get.retrieve_all("StampType"))
        stamp_types = StampType.objects.all()
        self.debug(Messages.Get.retrieved_all("StampType", len(stamp_types)))
        response = StampTypeResponseSerializer(stamp_types, many=True)
        
        return Response(
            data=response.data, 
            status=status.HTTP_200_OK
            )
    
    @extend_schema(
        operation_id="create_stamp_type",
        tags=['Stamp Types'],
        summary="Create a New Stamp Type",
        description="Adds a new stamp type entry to the database. A successful creation returns the newly created stamp type object with a 201 Created status code.",
        request=StampTypeRequestSerializer,
        responses={
            status.HTTP_201_CREATED: standardized_response(
                StampTypeResponseSerializer,
                name="StampTypeCreated",
                description="The stamp type was created successfully."
                ),
            status.HTTP_400_BAD_REQUEST: standardized_response(
                GenericResponseSerializer,
                name="StampTypeCreateInvalidPayload",
                success=False,
                description="The request payload was invalid (e.g., missing a required field)."
                ),
            status.HTTP_403_FORBIDDEN: standardized_response(
                StampTypeResponseSerializer,
                name="StampTypeCreateForbidden",
                success=False,
                description="Permission denied. You're likely missing X-API-Key header."
            )
        }
    )
    def post(self, request:Request, *args, **kwargs) -> Response:
        self.debug(Messages.Post.create_one("StampType", request.data))
        stamp_type = StampTypeRequestSerializer(data = request.data)
        
        if stamp_type.is_valid():
            instance = stamp_type.save()
            self.info(Messages.Post.created_one("StampType", instance.id))
            return Response(
                data=StampTypeResponseSerializer(instance).data, 
                status=status.HTTP_201_CREATED
                )
        
        self.warning(Messages.Post.validation_failed("StampType", stamp_type.errors))
        return Response(
            data=GenericResponseSerializer(GenericResponse(stamp_type.errors)).data,
            status=status.HTTP_400_BAD_REQUEST
            )