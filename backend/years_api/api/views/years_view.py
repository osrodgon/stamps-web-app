import stat
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema

from common.api.messages import Messages
from common.api.serializers.generic_response import GenericResponseSerializer, GenericResponse
from common.log.logger import Logger
from common.core.schemas import standardized_response
from years_api.models import Year
from years_api.api.serializers.year_response_serializer import YearResponseSerializer
from years_api.api.serializers.year_request_serializer import YearRequestSerializer


class YearsView(Logger, APIView):
    serializer_class = YearResponseSerializer
    
    @extend_schema(
        operation_id="list_years",
        tags=['Database Management'],
        summary="List All Years",
        description="Retrieves a list of all year entries currently stored in the database. The response will contain an array of year objects.",
        responses={
            status.HTTP_200_OK: standardized_response(
                YearResponseSerializer, 
                name="YearsRetrieved",
                description="A list of years was successfully retrieved.",
                many=True
                ),
            status.HTTP_403_FORBIDDEN: standardized_response(
                YearResponseSerializer,
                name="YearsRetrieveForbidden",
                success=False,
                description="Permission denied. You're likely missing X-API-Key header."
            )
        }
    )
    def get(self, request:Request, *args, **kwargs) -> Response:
        self.debug(Messages.Get.retrieve_all("years"))
        years = Year.objects.all()
        self.debug(Messages.Get.retrieved_all("years", len(years)))
        response = YearResponseSerializer(years, many=True)
        
        return Response(
            data=response.data, 
            status=status.HTTP_200_OK
            )
    
    @extend_schema(
        operation_id="create_year",
        tags=['Database Management'],
        summary="Create a New Year",
        description="Adds a new year entry to the database. The request body must contain the year data. A successful creation returns the newly created year object with a 201 status code.",
        request=YearRequestSerializer,
        responses={
            status.HTTP_201_CREATED: standardized_response(
                YearResponseSerializer,
                name="YearCreated",
                description="The year was created successfully."
                ),
            status.HTTP_400_BAD_REQUEST: standardized_response(
                GenericResponseSerializer,
                name="YearCreateInvalidPayload",
                success=False,
                description="The request payload was invalid.",
                ),
            status.HTTP_403_FORBIDDEN: standardized_response(
                YearResponseSerializer,
                name="YearCreateForbidden",
                success=False,
                description="Permission denied. You're likely missing X-API-Key header."
            )
        }
    )
    def post(self, request:Request, *args, **kwargs) -> Response:
        self.debug(Messages.Post.create_one("year", request.data))
        year = YearRequestSerializer(data = request.data)
        
        if year.is_valid():
            instance = year.save()
            self.info(Messages.Post.created_one("year", instance.id))
            return Response(
                data=YearResponseSerializer(instance).data, 
                status=status.HTTP_201_CREATED
                )
        
        self.warning(Messages.Post.validation_failed("year", year.errors))
        return Response(
            data=GenericResponseSerializer(GenericResponse(year.errors)).data,
            status=status.HTTP_400_BAD_REQUEST
            )