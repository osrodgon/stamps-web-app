import stat
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema

from common.api.messages import Messages
from common.log.logger import Logger
from common.api.serializers.generic_response import GenericResponse, GenericResponseSerializer
from common.core.schemas import standardized_response
from countries_api.models import Country
from countries_api.api.serializers.country_response_serializer import CountryResponseSerializer
from countries_api.api.serializers.country_request_serializer import CountryRequestSerializer


class CountriesByIdView(Logger, APIView):
    """Manages API operations for a single Country instance.

    This view handles the retrieval (GET), update (PUT), and deletion (DELETE)
    of a specific `Country` object, identified by its primary key (`pk`)
    provided in the URL.
    """
    serializer_class = CountryResponseSerializer
    def __get_country(self, pk: int) -> Country:
        """Retrieves a Country instance by its primary key.

        Args:
            pk (int): The primary key of the country to retrieve.

        Returns:
            Country: The found country instance, or None if it does not exist.
        """
        try:
            Messages.Database.querying("country", pk)
            return Country.objects.get(pk=pk)
        except Country.DoesNotExist:
            Messages.Database.not_found("country", pk)
            return None
    
    @extend_schema(
        operation_id="retrieve_country",
        tags=['Database Management'],
        summary="Retrieve a Country by ID",
        description="Fetches the details of a specific country entry by its unique identifier.",
        responses={
            status.HTTP_200_OK: standardized_response(
                CountryResponseSerializer,
                name="CountryRetrieved",
                description="The requested country's data was retrieved successfully."
                ),
            status.HTTP_403_FORBIDDEN: standardized_response(
                CountryResponseSerializer,
                name="CountryRetrieveForbidden",
                success=False,
                description="Permission denied."
            ),
            status.HTTP_404_NOT_FOUND: standardized_response(
                GenericResponseSerializer,
                name="RetrieveCountryNotFound",
                success=False,
                description="No country was found for the provided ID."
                ) 
        }
    )    
    def get(self, request: Request, pk: int, *args, **kwargs) -> Response:
        """Handles GET requests to retrieve a single country.

        Args:
            request (Request): The incoming HTTP request.
            pk (int): The primary key of the country to retrieve.

        Returns:
            Response:   A DRF Response object with the serialized country
                        data and 200 OK status, or a 404 Not Found response.
        """
        self.log.debug(Messages.Get.retrieve_one("country", pk))
        country = self.__get_country(pk)
        
        if country is None:
            message = Messages.Get.not_found("country", pk) 
            self.log.warning(message)
            return Response(
                data=GenericResponseSerializer(GenericResponse(message)).data,
                status=status.HTTP_404_NOT_FOUND
                )
        
        response = CountryResponseSerializer(country)
        self.log.info(Messages.Get.retrieved_one("country", pk))
        return Response(
            data=response.data, 
            status=status.HTTP_200_OK
            )
    
    @extend_schema(
        operation_id="update_country",
        tags=['Database Management'],
        summary="Update a Country",
        description="Updates an existing country entry identified by its ID. A complete payload with all required fields is expected.",
        request=CountryRequestSerializer,
        responses={
            status.HTTP_200_OK: standardized_response(
                CountryResponseSerializer,
                name="CountryUpdated",
                description="The country was updated successfully."
                ),
            status.HTTP_400_BAD_REQUEST: standardized_response(
                GenericResponseSerializer,
                name="CountryUpdateInvalidPayload",
                success=False,
                description="The request payload was invalid."
            ),
            status.HTTP_403_FORBIDDEN: standardized_response(
                CountryResponseSerializer,
                name="CountryUpdateForbidden",
                success=False,
                description="Permission denied."
            ),
            status.HTTP_404_NOT_FOUND: standardized_response(
                GenericResponseSerializer,
                name="CountryUpdateNotFound",
                success=False,
                description="The country with the specified ID was not found."
                )
        }
    )    
    def put(self, request: Request, pk: int, *args, **kwargs) -> Response:
        """Handles PUT requests to update an existing country.

        Args:
            request (Request): The incoming HTTP request containing update data.
            pk (int): The primary key of the country to update.

        Returns:
            Response:   A DRF Response with updated data and 200 OK status,
                        a 404 if not found, or a 400 on validation error.
        """
        self.log.debug(Messages.Put.update_one("country", pk, request.data))
        country = self.__get_country(pk)
        if country is None:
            message = Messages.Put.not_found("country", pk)
            self.log.warning(message)
            return Response(
                data=GenericResponseSerializer(GenericResponse(message)).data,
                status=status.HTTP_404_NOT_FOUND
                )
        
        updated_country = CountryRequestSerializer(data=request.data, instance=country, partial=False)
        if updated_country.is_valid():
            instance = updated_country.save()
            self.log.info(Messages.Put.updated_one("country", instance.id))
            return Response(
                data=CountryResponseSerializer(instance).data,
                status=status.HTTP_200_OK
                )
        
        self.log.warning(Messages.Put.validation_failed("country", pk, updated_country.errors))
        return Response(
            data=GenericResponseSerializer(GenericResponse(updated_country.errors)).data,
            status=status.HTTP_400_BAD_REQUEST
            )
    
    @extend_schema(
        operation_id="delete_country",
        tags=['Database Management'],
        summary="Delete a Country",
        description="Deletes a country entry from the database using its ID.",
        responses={
            status.HTTP_200_OK: standardized_response(
                GenericResponseSerializer,
                name="CountryDeleted",
                success=True,
                description="The country was deleted successfully."
                ),
            status.HTTP_403_FORBIDDEN: standardized_response(
                CountryResponseSerializer,
                name="CountryDeleteForbidden",
                success=False,
                description="Permission denied."
            ),
            status.HTTP_404_NOT_FOUND: standardized_response(
                GenericResponseSerializer,
                name="CountryDeleteNotFound",
                success=False,
                description="The country with the specified ID was not found."
                )
        }
    )    
    def delete(self, request: Request, pk: int, *args, **kwargs) -> Response:
        """Handles DELETE requests to remove a country.

        Args:
            request (Request): The incoming HTTP request.
            pk (int): The primary key of the country to delete.

        Returns:
            Response:   A DRF Response with a success message and 200 OK status,
                        or a 404 Not Found response if the item does not exist.
        """
        self.log.debug(Messages.Delete.delete_one("country", pk))
        country = self.__get_country(pk)
        if country is None:
            message = Messages.Delete.not_found("country", pk)
            self.log.warning(message)
            return Response(
                data=GenericResponseSerializer(GenericResponse(message)).data,
                status=status.HTTP_404_NOT_FOUND
                )
        
        country.delete()
        message = Messages.Delete.deleted_one("country", pk)
        self.log.info(message)
        return Response(
            data=GenericResponseSerializer(GenericResponse(message)).data,
            status=status.HTTP_200_OK
            )