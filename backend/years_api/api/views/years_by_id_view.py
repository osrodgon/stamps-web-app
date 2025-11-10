from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema

from common.api.messages import Messages
from common.log.logger import Logger
from common.api.serializers.generic_response import GenericResponse, GenericResponseSerializer
from common.core.schemas import standardized_response
from years_api.models import Year
from years_api.api.serializers.year_response_serializer import YearResponseSerializer
from years_api.api.serializers.year_request_serializer import YearRequestSerializer


class YearsByIdView(Logger, APIView):
    """
    API view for handling individual Year instances.

    This view provides GET, PUT, and DELETE operations for a specific
    year identified by its primary key.
    """
    serializer_class = YearResponseSerializer
    
    def __get_year__(self, pk: int) -> Year:
        """
        Helper method to retrieve a Year object by its primary key.

        Args:
            pk: The primary key of the year to retrieve.

        Returns:
            The Year instance if found, otherwise None.
        """
        try:
            Messages.Database.querying("year", pk)
            return Year.objects.get(pk=pk)
        except Year.DoesNotExist:
            Messages.Database.not_found("year", pk)
            return None
    
    @extend_schema(
        operation_id="retrieve_year",
        tags=['Database Management'],
        summary="Retrieve a Year by ID",
        description="Fetches the details of a specific year entry by its unique identifier. If the year exists, its data is returned. Otherwise, a 404 Not Found error is returned.",
        responses={
            status.HTTP_200_OK: standardized_response(
                YearResponseSerializer,
                name="YearRetrieved",
                description="The requested year's data was retrieved successfully."
                ),
            status.HTTP_403_FORBIDDEN: standardized_response(
                YearResponseSerializer,
                name="YearRetrieveForbidden",
                success=False,
                description="Permission denied."
            ),
            status.HTTP_404_NOT_FOUND: standardized_response(
                GenericResponseSerializer,
                name="RetrieveYearNotFound",
                success=False,
                description="No year was found for the provided ID."
                ) 
        }
    )    
    def get(self, request: Request, pk: int, *args, **kwargs) -> Response:
        """
        Handles GET requests to retrieve a single year by its ID.

        Args:
            request: The incoming HTTP request.
            pk: The primary key of the year to retrieve.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            A Response object containing the serialized year data with a
            200 OK status, or a 404 Not Found if the year does not exist.
        """
        self.debug(Messages.Get.retrieve_one("year", pk))
        year = self.__get_year__(pk)
        
        if year is None:
            message = Messages.Get.not_found("year", pk)
            self.warning(message)
            return Response(
                data=GenericResponseSerializer(GenericResponse(message)).data,
                status=status.HTTP_404_NOT_FOUND
                )
        
        response = YearResponseSerializer(year)
        self.info(Messages.Get.retrieved_one("year", pk))
        return Response(
            data=response.data, 
            status=status.HTTP_200_OK
            )
    
    @extend_schema(
        operation_id="update_year",
        tags=['Database Management'],
        summary="Update a Year",
        description="Updates an existing year entry identified by its ID. A complete payload with all required fields is expected. If the update is successful, the updated year data is returned. Returns a 404 error if the year does not exist or a 400 error for an invalid payload.",
        request=YearRequestSerializer,
        responses={
            status.HTTP_200_OK: standardized_response(
                YearResponseSerializer,
                name="YearUpdated",
                description="The year was updated successfully."
                ),
            status.HTTP_403_FORBIDDEN: standardized_response(
                YearResponseSerializer,
                name="YearUpdateForbidden",
                success=False,
                description="Permission denied."
            ),
            status.HTTP_404_NOT_FOUND: standardized_response(
                GenericResponseSerializer,
                name="YearUpdateNotFound",
                success=False,
                description="The year with the specified ID was not found."
                ),
            status.HTTP_400_BAD_REQUEST: standardized_response(
                GenericResponseSerializer,
                name="YearUpdateInvalidPayload",
                success=False,
                description="The request payload was invalid."
                )   
        }
    )    
    def put(self, request: Request, pk: int, *args, **kwargs) -> Response:
        """
        Handles PUT requests to update an existing year.

        Args:
            request: The incoming HTTP request containing the update data.
            pk: The primary key of the year to update.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            A Response object with the updated year data and a 200 OK status
            if successful. Returns a 404 Not Found if the year does not exist,
            or a 400 Bad Request if the provided data is invalid.
        """
        self.debug(Messages.Put.update_one("year", pk, request.data))
        year = self.__get_year__(pk)
        if year is None:
            message = Messages.Put.not_found("year", pk)
            self.warning(message)
            return Response(
                data=GenericResponseSerializer(GenericResponse(message)).data,
                status=status.HTTP_404_NOT_FOUND
                )
        
        updated_year = YearRequestSerializer(data=request.data, instance=year, partial=False)
        if updated_year.is_valid():
            instance=updated_year.save()
            self.info(Messages.Put.updated_one("year", instance.id))
            return Response(
                data=YearResponseSerializer(instance).data,
                status=status.HTTP_200_OK
                )
        
        self.warning(f"Payload validation failed for year update (id: {pk}): {updated_year.errors}")
        return Response(
            data=GenericResponseSerializer(GenericResponse(updated_year.errors)).data,
            status=status.HTTP_400_BAD_REQUEST
            )
    
    @extend_schema(
        operation_id="delete_year",
        tags=['Database Management'],
        summary="Delete a Year",
        description="Deletes a year entry from the database using its ID. If the deletion is successful, a confirmation message is returned. A 404 error is returned if the year with the specified ID does not exist.",
        responses={
            status.HTTP_200_OK: standardized_response(
                GenericResponseSerializer,
                name="YearDeleted",
                success=True,
                description="The year was deleted successfully."
                ),
            status.HTTP_403_FORBIDDEN: standardized_response(
                YearResponseSerializer,
                name="YearDeleteForbidden",
                success=False,
                description="Permission denied."
            ),
            status.HTTP_404_NOT_FOUND: standardized_response(
                GenericResponseSerializer,
                name="YearDeleteNotFound",
                success=False,
                description="The year with the specified ID was not found."
                )
        }
    )    
    def delete(self, request: Request, pk: int, *args, **kwargs) -> Response:
        """
        Handles DELETE requests to remove a year.

        Args:
            request: The incoming HTTP request.
            pk: The primary key of the year to delete.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            A Response object with a success message and a 200 OK status if
            the deletion was successful, or a 404 Not Found if the year does not exist.
        """
        self.debug(Messages.Delete.delete_one("year", pk))
        year = self.__get_year__(pk)
        if year is None:
            message=Messages.Delete.not_found("year", pk)
            self.warning(message)
            return Response(
                data=GenericResponseSerializer(GenericResponse(message)).data,
                status=status.HTTP_404_NOT_FOUND
                )
        
        year.delete()
        message = Messages.Delete.deleted_one("year", pk)
        self.info(message)
        return Response(
            data=GenericResponseSerializer(GenericResponse(message)).data,
            status=status.HTTP_200_OK
            )