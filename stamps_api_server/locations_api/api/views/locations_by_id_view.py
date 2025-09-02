from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema

from common.log.logger import Logger
from common.api.serializers.generic_response import GenericResponse, GenericResponseSerializer
from common.core.schemas import standardized_response
from locations_api.models import Location
from locations_api.api.serializers.location_response_serializer import LocationResponseSerializer
from locations_api.api.serializers.location_request_serializer import LocationRequestSerializer


class LocationsByIdView(Logger, APIView):
    def __get_location__(self, pk: int) -> Location:
        try:
            self.debug(f"Querying database for location with id: {pk}")
            return Location.objects.get(pk = pk)
        except Location.DoesNotExist:
            self.warning(f"Location with id {pk} does not exist in the database.")
            return None
        except Exception as e:
            self.error(f"An unexpected error occurred while fetching location with id {pk}: {str(e)}")
            return None
    
    @extend_schema(
        tags=['Locations'],
        summary="Retrieve a Location by ID",
        description="Fetches the details of a specific location entry by its unique identifier.",
        responses={
            200: standardized_response(
                LocationResponseSerializer,
                name="LocationRetrieved",
                description="The requested location's data was retrieved successfully."
                ),
            404: standardized_response(
                GenericResponseSerializer,
                name="RetrieveLocationNotFound",
                success=False,
                description="No location was found for the provided ID."
                ) 
        }
    )    
    def get(self, request: Request, pk: int, *args, **kwargs) -> Response:
        self.debug(f"Attempting to retrieve location for id: {pk}")
        location = self.__get_location__(pk)
        
        if location is None:
            message = f"Location with id: {pk} not found"
            self.warning(message)
            return Response(
                data=GenericResponse(message).data,
                status=status.HTTP_404_NOT_FOUND
                )
        
        response = LocationResponseSerializer(location)
        self.info(f"Successfully retrieved location with id: {pk}")
        return Response(
            data=response.data, 
            status=status.HTTP_200_OK
            )
    
    @extend_schema(
        tags=['Locations'],
        summary="Update a Location",
        description="Updates an existing location entry identified by its ID. A complete payload with all required fields is expected.",
        request=LocationRequestSerializer,
        responses={
            200: standardized_response(
                LocationResponseSerializer,
                name="LocationUpdated",
                description="The location was updated successfully."
                ),
            404: standardized_response(
                GenericResponseSerializer,
                name="LocationUpdateNotFound",
                success=False,
                description="The location with the specified ID was not found."
                ),
            400: standardized_response(
                GenericResponseSerializer,
                name="LocationUpdateInvalidPayload",
                success=False,
                description="The request payload was invalid."
                )   
        }
    )    
    def put(self, request: Request, pk: int, *args, **kwargs) -> Response:
        self.debug(f"Attempting to update location for id: {pk} with payload: {request.data}")
        location = self.__get_location__(pk)
        if location is None:
            message = f"Cannot update Location with id: {pk}. Not found in the database"
            self.warning(message)
            return Response(
                data=GenericResponse(message).data,
                status=status.HTTP_404_NOT_FOUND
                )
        
        updated_location = LocationRequestSerializer(data=request.data, instance=location, partial=False)
        if updated_location.is_valid():
            instance=updated_location.save()
            self.info(f"Successfully updated location with id: {instance.id}")
            return Response(
                data=LocationResponseSerializer(instance).data,
                status=status.HTTP_200_OK
                )
        
        self.warning(f"Payload validation failed for location update (id: {pk}): {updated_location.errors}")
        return Response(
            data=GenericResponse(updated_location.errors).data,
            status=status.HTTP_400_BAD_REQUEST
            )
    
    @extend_schema(
        tags=['Locations'],
        summary="Delete a Location",
        description="Deletes a location entry from the. database using its ID.",
        responses={
            200: standardized_response(
                GenericResponseSerializer,
                name="LocationDeleted",
                success=True,
                description="The location was deleted successfully."
                ),
            404: standardized_response(
                GenericResponseSerializer,
                name="LocationDeleteNotFound",
                success=False,
                description="The location with the specified ID was not found."
                )
        }
    )    
    def delete(self, request: Request, pk: int, *args, **kwargs) -> Response:
        self.debug(f"Attempting to delete location for id: {pk}")
        location = self.__get_location__(pk)
        if location is None:
            message=f"Cannot delete Location with id: {pk}. Not found in the database"
            self.warning(message)
            return Response(
                data=GenericResponse(message).data,
                status=status.HTTP_404_NOT_FOUND
                )
        
        location.delete()
        message = f"Successfully deleted Location with id: {pk}"
        self.info(message)
        return Response(
            data=GenericResponse(message).data,
            status=status.HTTP_200_OK
            )