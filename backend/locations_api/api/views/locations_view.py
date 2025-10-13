from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema

from common.api.messages import Messages
from common.api.serializers.generic_response import GenericResponseSerializer, GenericResponse
from common.log.logger import Logger
from common.core.schemas import standardized_response
from locations_api.models import Location
from locations_api.api.serializers.location_response_serializer import LocationResponseSerializer
from locations_api.api.serializers.location_request_serializer import LocationRequestSerializer


class LocationsView(Logger, APIView):
    serializer_class = LocationResponseSerializer
    
    @extend_schema(
        operation_id="list_locations",
        tags=['Locations'],
        summary="List All Locations",
        description="Retrieves a list of all location entries currently stored in the database.",
        responses={
            status.HTTP_200_OK: standardized_response(
                LocationResponseSerializer, 
                name="LocationsRetrieved",
                description="A list of locations was successfully retrieved.",
                many=True
            ),
            status.HTTP_403_FORBIDDEN: standardized_response(
                LocationResponseSerializer,
                name="LocationsListForbidden",
                success=False,
                description="Permission denied. You're likely missing X-API-Key or X-API-User headers."
            )
        }
    )
    def get(self, request:Request, *args, **kwargs) -> Response:
        self.debug(Messages.Get.retrieve_all("locations"))
        locations = Location.objects.all()
        self.debug(Messages.Get.retrieved_all("locations", len(locations)))
        response = LocationResponseSerializer(locations, many=True)
        
        return Response(
            data=response.data, 
            status=status.HTTP_200_OK
            )
    
    @extend_schema(
        operation_id="create_location",
        tags=['Locations'],
        summary="Create a New Location",
        description="Adds a new location entry to the database. A successful creation returns the newly created location object with a 201 Created status code.",
        request=LocationRequestSerializer,
        responses={
            status.HTTP_201_CREATED: standardized_response(
                LocationResponseSerializer,
                name="LocationCreated",
                description="The location was created successfully."
            ),
            status.HTTP_400_BAD_REQUEST: standardized_response(
                GenericResponseSerializer,
                name="LocationCreateInvalidPayload",
                success=False,
                description="The request payload was invalid (e.g., missing a required field)."
            ),
            status.HTTP_403_FORBIDDEN: standardized_response(
                LocationResponseSerializer,
                name="LocationCreateForbidden",
                success=False,
                description="Permission denied. You're likely missing X-API-Key or X-API-User headers."
            )
        }
    )
    def post(self, request:Request, *args, **kwargs) -> Response:
        self.debug(Messages.Post.create_one("location", request.data))
        location = LocationRequestSerializer(data = request.data)
        
        if location.is_valid():
            instance = location.save()
            self.info(Messages.Post.created_one("location", instance.id))
            return Response(
                data=LocationResponseSerializer(instance).data, 
                status=status.HTTP_201_CREATED
                )
        
        self.warning(Messages.Post.validation_failed("location", location.errors))
        return Response(
            data=GenericResponseSerializer(GenericResponse(location.errors)).data,
            status=status.HTTP_400_BAD_REQUEST
            )