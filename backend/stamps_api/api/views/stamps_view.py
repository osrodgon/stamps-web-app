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
from stamps_api.models import Stamp
from stamps_api.api.serializers.stamp_response_serializer import StampResponseSerializer
from stamps_api.api.serializers.stamp_request_serializer import StampRequestSerializer


class StampsView(Logger, APIView):
    serializer_class = StampResponseSerializer
    
    @extend_schema(
        operation_id="list_stamps",
        tags=['Stamps'],
        summary="List All Stamps",
        description="Retrieves a list of all stamp entries currently stored in the database.",
        responses={
            status.HTTP_200_OK: standardized_response(
                StampResponseSerializer, 
                name="StampsRetrieved",
                description="A list of stamps was successfully retrieved.",
                many=True
                ),
            status.HTTP_403_FORBIDDEN: standardized_response(
                StampResponseSerializer,
                name="StampsListPermissionDenied",
                success=False,
                description="Permission denied. You're likely missing X-API-Key header."
            )
        }
    )
    def get(self, request:Request, *args, **kwargs) -> Response:
        self.debug(Messages.Get.retrieve_all("stamps"))
        stamps = Stamp.objects.all()
        self.debug(Messages.Get.retrieved_all("stamps", len(stamps)))
        response = StampResponseSerializer(stamps, many=True)
        
        return Response(
            data=response.data, 
            status=status.HTTP_200_OK
            )
    
    @extend_schema(
        operation_id="create_stamp",
        tags=['Stamps'],
        summary="Create a New Stamp",
        description="Adds a new stamp entry to the database. A successful creation returns the newly created stamp object with a 201 Created status code.",
        request=StampRequestSerializer,
        responses={
            status.HTTP_201_CREATED: standardized_response(
                StampResponseSerializer,
                name="StampCreated",
                description="The stamp was created successfully."
                ),
            status.HTTP_400_BAD_REQUEST: standardized_response(
                GenericResponseSerializer,
                name="StampCreateInvalidPayload",
                success=False,
                description="The request payload was invalid (e.g., missing a required field)."
                ),
            status.HTTP_403_FORBIDDEN: standardized_response(
                StampResponseSerializer,
                name="StampCreatePermissionDenied",
                success=False,
                description="Permission denied. You're likely missing X-API-Key header."
            )
        }
    )
    def post(self, request:Request, *args, **kwargs) -> Response:
        self.debug(Messages.Post.create_one("stamp", request.data))
        stamp = StampRequestSerializer(data = request.data)
        
        if stamp.is_valid():
            instance = stamp.save()
            self.info(Messages.Post.created_one("stamp", instance.id))
            return Response(
                data=StampResponseSerializer(instance).data, 
                status=status.HTTP_201_CREATED
                )
        
        self.warning(Messages.Post.validation_failed("stamp", stamp.errors))
        return Response(
            data=GenericResponseSerializer(GenericResponse(stamp.errors)).data,
            status=status.HTTP_400_BAD_REQUEST
            )