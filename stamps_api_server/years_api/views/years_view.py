from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema

from common.log.logger import Logger
from common.serializers.generic_response import GenericResponse
from years_api.models import Year
from years_api.serializers.year_response_serializer import YearResponseSerializer
from years_api.serializers.year_request_serializer import YearRequestSerializer


class YearsView(Logger, APIView):
    """Implements REST methods for the year table (all records)

    Args:
        Logger: Abstract class for logging
        APIView: Abstract class
    """
    @swagger_auto_schema(
        tags=['Years'],
        operation_description="List all years",
        responses={
            200: YearResponseSerializer(many = True)
        }
    )    
    def get(self, request:Request, *args, **kwargs) -> Response:
        """Gets all records from the year table

        Args:
            request (Request): Request data

        Returns:
            Response:   200. List of records
        """
        self.debug("Getting all years")
        years = Year.objects.all()
        response = YearResponseSerializer(years, many=True)
        return Response(
            data=response.data, 
            status=status.HTTP_200_OK
            )
    
    @swagger_auto_schema(
        tags=['Years'],
        operation_description="Creates a year",
        request_body=YearRequestSerializer(many=False),
        responses={
            200: YearRequestSerializer(many=False),
            400: YearRequestSerializer(many=False)
        }
    )   
    def post(self, request:Request, *args, **kwargs) -> Response:
        """Creates an entry in the year table

        Args:
            request (Request): Request data (payload)

        Returns:
            Response:   201. Record created
                        404. Bad request
        """
        self.debug(f"Create a new year: {request.data}")
        year = YearRequestSerializer(data = request.data)
        
        if year.is_valid():
            year.save()
            return Response(
                data=year.data, 
                status=status.HTTP_201_CREATED
                )
        
        self.debug(f"Payload validaton error: {year.errors}")
        return Response(
            data=year.errors, 
            status=status.HTTP_400_BAD_REQUEST
            )