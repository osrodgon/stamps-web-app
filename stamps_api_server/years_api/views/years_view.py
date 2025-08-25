from common.logger import Logger
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from years_api.models import Year
from years_api.serializers.year_response_serializer import YearResponseSerializer
from years_api.serializers.year_request_serializer import YearRequestSerializer


class YearsView(Logger, APIView):
    def get(self, request:Request, *args, **kwargs) -> Response:
        self.debug("Getting all years")
        years = Year.objects.all().values()
        response = YearResponseSerializer(years, many = True)
        return Response(response.data, status=status.HTTP_200_OK)
    
    def post(self, request:Request, *args, **kwargs) -> Response:
        self.debug(f"Create a new year: {request.data}")
        year = YearRequestSerializer(data = request.data)
        
        if year.is_valid():
            year.save()
            return Response(year.data, status=status.HTTP_201_CREATED)
        
        self.debug(f"Payload validaton error: {year.errors}")
        return Response(year.errors, status = status.HTTP_400_BAD_REQUEST)