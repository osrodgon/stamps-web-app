from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema

from common.api.serializers.generic_response import GenericResponseSerializer, GenericResponse
from common.log.logger import Logger
from common.core.schemas import standardized_response
from locations_api.models import Location
from locations_api.api.serializers.location_response_serializer import LocationResponseSerializer
from locations_api.api.serializers.location_request_serializer import LocationRequestSerializer


class LocationsView(Logger, APIView):
    @extend_schema(
        tags=['Locations'],
        summary="List All Locations",
        description="Retrieves a list of all location entries currently stored in the database.",
        responses={
            200: standardized_response(
                LocationResponseSerializer, 
                name="LocationsRetrieved",
                description="A list of locations was successfully retrieved.",
                many=True
                )
        }
    )
    def get(self, request:Request, *args, **kwargs) -> Response:
        self.debug("Attempting to retrieve all locations.")
        locations = Location.objects.all()
        self.debug(f"Found {len(locations)} location entries.")
        response = LocationResponseSerializer(locations, many=True)
        
        return Response(
            data=response.data, 
            status=status.HTTP_200_OK
            )
    
    @extend_schema(
        tags=['Locations'],
        summary="Create a New Location",
        description="Adds a new location entry to the database. A successful creation returns the newly created location object with a 201 Created status code.",
        request=LocationRequestSerializer,
        responses={
            201: standardized_response(
                LocationResponseSerializer,
                name="LocationCreated",
                description="The location was created successfully."
                ),
            400: standardized_response(
                GenericResponseSerializer,
                name="LocationCreateInvalidPayload",
                success=False,
                description="The request payload was invalid (e.g., missing a required field)."
                )
        }
    )
    def post(self, request:Request, *args, **kwargs) -> Response:
        self.debug(f"Attempting to create a new location with payload: {request.data}")
        location = LocationRequestSerializer(data = request.data)
        
        if location.is_valid():
            instance = location.save()
            self.info(f"Successfully created location with id: {instance.id}")
            return Response(
                data=LocationResponseSerializer(instance).data, 
                status=status.HTTP_201_CREATED
                )
        
        self.warning(f"Payload validation failed for new location entry: {location.errors}")
        return Response(
            data=GenericResponseSerializer(GenericResponse(location.errors)).data,
            status=status.HTTP_400_BAD_REQUEST
            )