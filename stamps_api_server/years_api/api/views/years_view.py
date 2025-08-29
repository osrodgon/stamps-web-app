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
        summary="List all years",
        description="Returns a list of all years in the database",
        responses={
            200: standardized_response(
                YearResponseSerializer, 
                description="Years retrieved successfully from the database",
                many=True
                )
        }
    )
    def get(self, request:Request, *args, **kwargs) -> Response:
        self.debug("Getting all years")
        years = Year.objects.all()
        response = YearResponseSerializer(years, many=True)
        
        return Response(
            data=response.data, 
            status=status.HTTP_200_OK
            )
    
    @extend_schema(
        tags=['Years'],
        summary="Creates a year",
        description="Creates a year in the database",
        responses={
            201: standardized_response(
                YearResponseSerializer,
                description="Year created successfully"
                ),
            400: standardized_response(
                GenericResponseSerializer,
                success=False,
                description="Payload validation error"
                )
        }
    )
    def post(self, request:Request, *args, **kwargs) -> Response:
        self.debug(f"Create a new year: {request.data}")
        year = YearRequestSerializer(data = request.data)
        
        if year.is_valid():
            instance = year.save()
            return Response(
                data=YearResponseSerializer(instance).data, 
                status=status.HTTP_201_CREATED
                )
        
        self.debug(f"Payload validaton error: {year.errors}")
        return Response(
            data=GenericResponseSerializer(GenericResponse(year.errors)).data,
            status=status.HTTP_400_BAD_REQUEST
            )