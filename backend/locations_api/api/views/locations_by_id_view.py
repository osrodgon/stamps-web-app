from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema

from common.api.messages import Messages
from common.log.logger import Logger
from common.api.serializers.generic_response import GenericResponse, GenericResponseSerializer
from common.core.schemas import standardized_response
from locations_api.models import Location
from locations_api.api.serializers.location_response_serializer import LocationResponseSerializer
from locations_api.api.serializers.location_request_serializer import LocationRequestSerializer


class LocationsByIdView(Logger, APIView):
    """
    API view for handling individual Location instances.

    This view provides GET, PUT, and DELETE operations for a specific
    location identified by its primary key.
    """
    serializer_class = LocationResponseSerializer
    
    def __get_location(self, pk: int) -> Location:
        """
        Helper method to retrieve a Location object by its primary key.

        Args:
            pk: The primary key of the location to retrieve.

        Returns:
            The Location instance if found, otherwise None.
        """
        try:
            Messages.Database.querying("location", pk)
            return Location.objects.get(pk=pk)
        except Location.DoesNotExist:
            Messages.Database.not_found("location", pk)
            return None
    
    @extend_schema(
        operation_id="retrieve_location",
        tags=['Collection Management'],
        summary="Retrieve a Location by ID",
        description="Fetches the details of a specific location entry by its unique identifier.",
        responses={
            status.HTTP_200_OK: standardized_response(
                LocationResponseSerializer,
                name="LocationRetrieved",
                description="The requested location's data was retrieved successfully."
                ),
            status.HTTP_403_FORBIDDEN: standardized_response(
                LocationResponseSerializer,
                name="LocationRetrieveForbidden",
                success=False,
                description="Permission denied."
            ),
            status.HTTP_404_NOT_FOUND: standardized_response(
                GenericResponseSerializer,
                name="RetrieveLocationNotFound",
                success=False,
                description="No location was found for the provided ID."
                ) 
        }
    )    
    def get(self, request: Request, pk: int, *args, **kwargs) -> Response:
        """
        Handles GET requests to retrieve a single location by its ID.

        Args:
            request: The incoming HTTP request.
            pk: The primary key of the location to retrieve.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            A Response object containing the serialized location data with a
            200 OK status, or a 404 Not Found if the location does not exist.
        """
        self.debug(Messages.Get.retrieve_one("location", pk))
        location = self.__get_location(pk)
        
        if location is None:
            message = Messages.Get.not_found("location", pk)
            self.warning(message)
            return Response(
                data=GenericResponseSerializer(GenericResponse(message)).data,
                status=status.HTTP_404_NOT_FOUND
                )
        
        response = LocationResponseSerializer(location)
        self.info(Messages.Get.retrieved_one("location", pk))
        return Response(
            data=response.data, 
            status=status.HTTP_200_OK
            )
    
    @extend_schema(
        operation_id="update_location",
        tags=['Collection Management'],
        summary="Update a Location",
        description="Updates an existing location entry identified by its ID. A complete payload with all required fields is expected.",
        request=LocationRequestSerializer,
        responses={
            status.HTTP_200_OK: standardized_response(
                LocationResponseSerializer,
                name="LocationUpdated",
                description="The location was updated successfully."
                ),
            status.HTTP_400_BAD_REQUEST: standardized_response(
                GenericResponseSerializer,
                name="LocationUpdateInvalidPayload",
                success=False,
                description="The request payload was invalid."
            ),
            status.HTTP_403_FORBIDDEN: standardized_response(
                LocationResponseSerializer,
                name="LocationUpdateForbidden",
                success=False,
                description="Permission denied."
            ),
            status.HTTP_404_NOT_FOUND: standardized_response(
                GenericResponseSerializer,
                name="LocationUpdateNotFound",
                success=False,
                description="The location with the specified ID was not found."
            )   
        }
    )    
    def put(self, request: Request, pk: int, *args, **kwargs) -> Response:
        """
        Handles PUT requests to update an existing location.

        Args:
            request: The incoming HTTP request containing the update data.
            pk: The primary key of the location to update.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            A Response object with the updated location data and a 200 OK status
            if successful. Returns a 404 Not Found if the location does not exist,
            or a 400 Bad Request if the provided data is invalid.
        """
        self.debug(Messages.Put.update_one("location", pk, request.data))
        location = self.__get_location(pk)
        if location is None:
            message = Messages.Put.not_found("location", pk)
            self.warning(message)
            return Response(
                data=GenericResponseSerializer(GenericResponse(message)).data,
                status=status.HTTP_404_NOT_FOUND
                )
        
        updated_location = LocationRequestSerializer(data=request.data, instance=location, partial=False)
        if updated_location.is_valid():
            instance = updated_location.save()
            self.info(Messages.Put.updated_one("location", instance.id))
            return Response(
                data=LocationResponseSerializer(instance).data,
                status=status.HTTP_200_OK
                )
        
        self.warning(Messages.Put.validation_failed("location", pk, updated_location.errors))
        return Response(
            data=GenericResponseSerializer(GenericResponse(updated_location.errors)).data,
            status=status.HTTP_400_BAD_REQUEST
            )
    
    @extend_schema(
        operation_id="delete_location",
        tags=['Collection Management'],
        summary="Delete a Location",
        description="Deletes a location entry from the. database using its ID.",
        responses={
            status.HTTP_200_OK: standardized_response(
                GenericResponseSerializer,
                name="LocationDeleted",
                success=True,
                description="The location was deleted successfully."
                ),
            status.HTTP_403_FORBIDDEN: standardized_response(
                LocationResponseSerializer,
                name="LocationDeleteForbidden",
                success=False,
                description="Permission denied."
            ),
            status.HTTP_404_NOT_FOUND: standardized_response(
                GenericResponseSerializer,
                name="LocationDeleteNotFound",
                success=False,
                description="The location with the specified ID was not found."
                )
        }
    )    
    def delete(self, request: Request, pk: int, *args, **kwargs) -> Response:
        """
        Handles DELETE requests to remove a location.

        Args:
            request: The incoming HTTP request.
            pk: The primary key of the location to delete.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            A Response object with a success message and a 200 OK status if
            the deletion was successful, or a 404 Not Found if the location does not exist.
        """
        self.debug(Messages.Delete.delete_one("location", pk))
        location = self.__get_location(pk)
        if location is None:
            message=Messages.Delete.not_found("location", pk)
            self.warning(message)
            return Response(
                data=GenericResponseSerializer(GenericResponse(message)).data,
                status=status.HTTP_404_NOT_FOUND
                )
        
        location.delete()
        message = Messages.Delete.deleted_one("location", pk)
        self.info(message)
        return Response(
            data=GenericResponseSerializer(GenericResponse(message)).data,
            status=status.HTTP_200_OK
            )