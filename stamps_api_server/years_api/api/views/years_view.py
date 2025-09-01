from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema

from common.api.serializers.generic_response import GenericResponseSerializer, GenericResponse
from common.log.logger import Logger
from common.core.schemas import standardized_response
from years_api.models import Year
from years_api.api.serializers.year_response_serializer import YearResponseSerializer
from years_api.api.serializers.year_request_serializer import YearRequestSerializer


class YearsView(Logger, APIView):
    @extend_schema(
        tags=['Years'],
        summary="List All Years",
        description="Retrieves a list of all year entries currently stored in the database. The response will contain an array of year objects.",
        responses={
            200: standardized_response(
                YearResponseSerializer, 
                name="YearsRetrieved",
                description="A list of years was successfully retrieved.",
                many=True
                )
        }
    )
    def get(self, request:Request, *args, **kwargs) -> Response:
        self.debug("Attempting to retrieve all years.")
        years = Year.objects.all()
        self.debug(f"Found {len(years)} year entries.")
        response = YearResponseSerializer(years, many=True)
        
        return Response(
            data=response.data, 
            status=status.HTTP_200_OK
            )
    
    @extend_schema(
        tags=['Years'],
        summary="Create a New Year",
        description="Adds a new year entry to the database. The request body must contain the year data. A successful creation returns the newly created year object with a 201 status code.",
        request=YearRequestSerializer,
        responses={
            201: standardized_response(
                YearResponseSerializer,
                name="YearCreated",
                description="The year was created successfully."
                ),
            400: standardized_response(
                GenericResponseSerializer,
                name="YearCreateInvalidPayload",
                success=False,
                description="The request payload was invalid."
                )
        }
    )
    def post(self, request:Request, *args, **kwargs) -> Response:
        self.debug(f"Attempting to create a new year with payload: {request.data}")
        year = YearRequestSerializer(data = request.data)
        
        if year.is_valid():
            instance = year.save()
            self.info(f"Successfully created year with id: {instance.id}")
            return Response(
                data=YearResponseSerializer(instance).data, 
                status=status.HTTP_201_CREATED
                )
        
        self.warning(f"Payload validation failed for new year entry: {year.errors}")
        return Response(
            data=GenericResponseSerializer(GenericResponse(year.errors)).data,
            status=status.HTTP_400_BAD_REQUEST
            )