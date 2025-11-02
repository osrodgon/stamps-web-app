from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema

from common.api.messages import Messages
from common.api.serializers.generic_response import GenericResponseSerializer, GenericResponse
from common.log.logger import Logger
from common.core.schemas import standardized_response
from countries_api.models import Country
from countries_api.api.serializers.country_response_serializer import CountryResponseSerializer
from countries_api.api.serializers.country_request_serializer import CountryRequestSerializer


class CountriesView(Logger, APIView):
    """Manages bulk API operations for Country instances.

    This view handles the retrieval of all countries (GET) and the
    creation of a new country (POST).
    """
    serializer_class = CountryResponseSerializer
    
    @extend_schema(
        operation_id="list_countries",
        tags=['Database Management'],
        summary="List All Countries",
        description="Retrieves a list of all country entries currently stored in the database.",
        responses={
            status.HTTP_200_OK: standardized_response(
                CountryResponseSerializer, 
                name="CountriesRetrieved",
                description="A list of countries was successfully retrieved.",
                many=True
                ),
            status.HTTP_403_FORBIDDEN: standardized_response(
                CountryResponseSerializer,
                name="CountriesRetrieveForbidden",
                success=False,
                description="Permission denied."
            )
        }
    )
    def get(self, request:Request, *args, **kwargs) -> Response:
        """Handles GET requests to retrieve all countries.

        Args:
            request (Request): The incoming HTTP request.

        Returns:
            Response:   A DRF Response object containing a list of all serialized
                        country objects and a 200 OK status.
        """
        self.debug(Messages.Get.retrieve_all("countries"))
        countries = Country.objects.all()
        self.debug(Messages.Get.retrieved_all("countries", len(countries)))
        response = CountryResponseSerializer(countries, many=True)
        
        return Response(
            data=response.data, 
            status=status.HTTP_200_OK
            )
    
    @extend_schema(
        operation_id="create_country",
        tags=['Database Management'],
        summary="Create a New Country",
        description="Adds a new country entry to the database. A successful creation returns the newly created country object with a 201 Created status code.",
        request=CountryRequestSerializer,
        responses={
            status.HTTP_201_CREATED: standardized_response(
                CountryResponseSerializer,
                name="CountryCreated",
                description="The country was created successfully."
                ),
            status.HTTP_400_BAD_REQUEST: standardized_response(
                GenericResponseSerializer,
                name="CountryCreateInvalidPayload",
                success=False,
                description="The request payload was invalid (e.g., missing a required field)."
                ),
            status.HTTP_403_FORBIDDEN: standardized_response(
                CountryResponseSerializer,
                name="CountryCreateForbidden",
                success=False,
                description="Permission denied."
            )
        }
    )
    def post(self, request:Request, *args, **kwargs) -> Response:
        """Handles POST requests to create a new country.

        Args:
            request (Request):  The incoming HTTP request containing the data for
                                the new country.

        Returns:
            Response:   A DRF Response with the newly created country's data and a
                        201 Created status, or a 400 Bad Request on validation error.
        """
        self.debug(Messages.Post.create_one("country", request.data))
        country = CountryRequestSerializer(data = request.data)
        
        if country.is_valid():
            instance = country.save()
            self.info(Messages.Post.created_one("country", instance.id))
            return Response(
                data=CountryResponseSerializer(instance).data, 
                status=status.HTTP_201_CREATED
                )
        
        self.warning(Messages.Post.validation_failed("country", country.errors))
        return Response(
            data=GenericResponseSerializer(GenericResponse(country.errors)).data,
            status=status.HTTP_400_BAD_REQUEST
            )