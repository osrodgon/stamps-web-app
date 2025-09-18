from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema

from common.api.serializers.generic_response import GenericResponseSerializer, GenericResponse
from common.log.logger import Logger
from common.core.schemas import standardized_response
from countries_api.models import Country
from countries_api.api.serializers.country_response_serializer import CountryResponseSerializer
from countries_api.api.serializers.country_request_serializer import CountryRequestSerializer


class CountriesView(Logger, APIView):
    serializer_class = CountryResponseSerializer
    
    @extend_schema(
        operation_id="list_countries",
        tags=['Countries'],
        summary="List All Countries",
        description="Retrieves a list of all country entries currently stored in the database.",
        responses={
            200: standardized_response(
                CountryResponseSerializer, 
                name="CountriesRetrieved",
                description="A list of countries was successfully retrieved.",
                many=True
                )
        }
    )
    def get(self, request:Request, *args, **kwargs) -> Response:
        self.debug("Attempting to retrieve all countries.")
        countries = Country.objects.all()
        self.debug(f"Found {len(countries)} country entries.")
        response = CountryResponseSerializer(countries, many=True)
        
        return Response(
            data=response.data, 
            status=status.HTTP_200_OK
            )
    
    @extend_schema(
        operation_id="create_country",
        tags=['Countries'],
        summary="Create a New Country",
        description="Adds a new country entry to the database. A successful creation returns the newly created country object with a 201 Created status code.",
        request=CountryRequestSerializer,
        responses={
            201: standardized_response(
                CountryResponseSerializer,
                name="CountryCreated",
                description="The country was created successfully."
                ),
            400: standardized_response(
                GenericResponseSerializer,
                name="CountryCreateInvalidPayload",
                success=False,
                description="The request payload was invalid (e.g., missing a required field)."
                )
        }
    )
    def post(self, request:Request, *args, **kwargs) -> Response:
        self.debug(f"Attempting to create a new country with payload: {request.data}")
        country = CountryRequestSerializer(data = request.data)
        
        if country.is_valid():
            instance = country.save()
            self.info(f"Successfully created country with id: {instance.id}")
            return Response(
                data=CountryResponseSerializer(instance).data, 
                status=status.HTTP_201_CREATED
                )
        
        self.warning(f"Payload validation failed for new country entry: {country.errors}")
        return Response(
            data=GenericResponseSerializer(GenericResponse(country.errors)).data,
            status=status.HTTP_400_BAD_REQUEST
            )