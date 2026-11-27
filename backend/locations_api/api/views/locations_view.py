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
    """
    API view for handling collections of Location instances.

    This view provides GET (list) and POST (create) operations for locations.
    """
    serializer_class = LocationResponseSerializer
    
    @extend_schema(
        operation_id="list_locations",
        tags=['Collection Management'],
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
                description="Permission denied."
            )
        }
    )
    def get(self, request:Request, *args, **kwargs) -> Response:
        """
        Handles GET requests to retrieve a list of all locations.

        Args:
            request: The incoming HTTP request.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            A Response object containing a list of all serialized locations
            with a 200 OK status.
        """
        self.log.debug(Messages.Get.retrieve_all("locations"))
        locations = Location.objects.all()
        self.log.debug(Messages.Get.retrieved_all("locations", len(locations)))
        response = LocationResponseSerializer(locations, many=True)
        
        return Response(
            data=response.data, 
            status=status.HTTP_200_OK
            )
    
    @extend_schema(
        operation_id="create_location",
        tags=['Collection Management'],
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
                description="Permission denied."
            )
        }
    )
    def post(self, request:Request, *args, **kwargs) -> Response:
        """
        Handles POST requests to create a new location.

        Args:
            request: The incoming HTTP request containing the new location data.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            A Response object with the newly created location data and a 201 Created
            status if successful. Returns a 400 Bad Request if the provided
            data is invalid.
        """
        self.log.debug(Messages.Post.create_one("location", request.data))
        location = LocationRequestSerializer(data = request.data)
        
        if location.is_valid():
            instance = location.save()
            self.log.info(Messages.Post.created_one("location", instance.id))
            return Response(
                data=LocationResponseSerializer(instance).data, 
                status=status.HTTP_201_CREATED
                )
        
        self.log.warning(Messages.Post.validation_failed("location", location.errors))
        return Response(
            data=GenericResponseSerializer(GenericResponse(location.errors)).data,
            status=status.HTTP_400_BAD_REQUEST
            )