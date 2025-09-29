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
    serializer_class = CountryResponseSerializer
    def __get_country(self, pk: int) -> Country:
        try:
            Messages.Database.querying("country", pk)
            return Country.objects.get(pk=pk)
        except Country.DoesNotExist:
            Messages.Database.not_found("country", pk)
            return None
    
    @extend_schema(
        operation_id="retrieve_country",
        tags=['Countries'],
        summary="Retrieve a Country by ID",
        description="Fetches the details of a specific country entry by its unique identifier.",
        responses={
            200: standardized_response(
                CountryResponseSerializer,
                name="CountryRetrieved",
                description="The requested country's data was retrieved successfully."
                ),
            404: standardized_response(
                GenericResponseSerializer,
                name="RetrieveCountryNotFound",
                success=False,
                description="No country was found for the provided ID."
                ) 
        }
    )    
    def get(self, request: Request, pk: int, *args, **kwargs) -> Response:
        self.debug(Messages.Get.retrieve_one("country", pk))
        country = self.__get_country(pk)
        
        if country is None:
            message = Messages.Get.not_found("country", pk) 
            self.warning(message)
            return Response(
                data=GenericResponseSerializer(GenericResponse(message)).data,
                status=status.HTTP_404_NOT_FOUND
                )
        
        response = CountryResponseSerializer(country)
        self.info(Messages.Get.retrieved_one("country", pk))
        return Response(
            data=response.data, 
            status=status.HTTP_200_OK
            )
    
    @extend_schema(
        operation_id="update_country",
        tags=['Countries'],
        summary="Update a Country",
        description="Updates an existing country entry identified by its ID. A complete payload with all required fields is expected.",
        request=CountryRequestSerializer,
        responses={
            200: standardized_response(
                CountryResponseSerializer,
                name="CountryUpdated",
                description="The country was updated successfully."
                ),
            404: standardized_response(
                GenericResponseSerializer,
                name="CountryUpdateNotFound",
                success=False,
                description="The country with the specified ID was not found."
                ),
            400: standardized_response(
                GenericResponseSerializer,
                name="CountryUpdateInvalidPayload",
                success=False,
                description="The request payload was invalid."
                )   
        }
    )    
    def put(self, request: Request, pk: int, *args, **kwargs) -> Response:
        self.debug(Messages.Put.update_one("country", pk, request.data))
        country = self.__get_country(pk)
        if country is None:
            message = Messages.Put.not_found("country", pk)
            self.warning(message)
            return Response(
                data=GenericResponseSerializer(GenericResponse(message)).data,
                status=status.HTTP_404_NOT_FOUND
                )
        
        updated_country = CountryRequestSerializer(data=request.data, instance=country, partial=False)
        if updated_country.is_valid():
            instance = updated_country.save()
            self.info(Messages.Put.updated_one("country", instance.id))
            return Response(
                data=CountryResponseSerializer(instance).data,
                status=status.HTTP_200_OK
                )
        
        self.warning(Messages.Put.validation_failed("country", pk, updated_country.errors))
        return Response(
            data=GenericResponseSerializer(GenericResponse(updated_country.errors)).data,
            status=status.HTTP_400_BAD_REQUEST
            )
    
    @extend_schema(
        operation_id="delete_country",
        tags=['Countries'],
        summary="Delete a Country",
        description="Deletes a country entry from the database using its ID.",
        responses={
            200: standardized_response(
                GenericResponseSerializer,
                name="CountryDeleted",
                success=True,
                description="The country was deleted successfully."
                ),
            404: standardized_response(
                GenericResponseSerializer,
                name="CountryDeleteNotFound",
                success=False,
                description="The country with the specified ID was not found."
                )
        }
    )    
    def delete(self, request: Request, pk: int, *args, **kwargs) -> Response:
        self.debug(Messages.Delete.delete_one("country", pk))
        country = self.__get_country(pk)
        if country is None:
            message = Messages.Delete.not_found("country", pk)
            self.warning(message)
            return Response(
                data=GenericResponseSerializer(GenericResponse(message)).data,
                status=status.HTTP_404_NOT_FOUND
                )
        
        country.delete()
        message = Messages.Delete.deleted_one("country", pk)
        self.info(message)
        return Response(
            data=GenericResponseSerializer(GenericResponse(message)).data,
            status=status.HTTP_200_OK
            )