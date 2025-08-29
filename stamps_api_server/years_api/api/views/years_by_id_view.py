from ast import Str
from turtle import st
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema

from common.log.logger import Logger
from common.api.serializers.generic_response import GenericResponse, GenericResponseSerializer
from common.core.schemas import standardized_response
from years_api.models import Year
from years_api.api.serializers.year_response_serializer import YearResponseSerializer
from years_api.api.serializers.year_request_serializer import YearRequestSerializer


class YearsByIdView(Logger, APIView):
    def __get_year__(self, pk: int) -> Year:
        try:
            self.debug(f"Getting a year from database with id: {pk}")
            return Year.objects.get(pk = pk)
        except Year.DoesNotExist:
            self.warning(f"Year with id {pk} does not exist.")
            return None
        except Exception as e:
            self.warning(f"An unknown error has occurred: {str(e)}")
            return None
    
    # @swagger_auto_schema(
    #     tags=['Years'],
    #     operation_description="Gets a single year",
    #     responses={
    #         200: YearResponseSerializer(many=False),
    #         404: GenericResponse().serializer
    #     }
    # )
    @extend_schema(
        tags=['Years'],
        summary="Gets a single year",
        description="Returns a single year from the database",
        responses={
            200: standardized_response(
                YearResponseSerializer,
                description="Year information retrieved successfully from the database"
                ),
            404: standardized_response(
                None, 
                description="Year not found in the database"
                ) 
        }
    )    
    def get(self, request: Request, pk: int, *args, **kwargs) -> Response:
        self.debug(f"GET year with id: {pk}")
        year = self.__get_year__(pk)
        
        if year is None:
            message = f"Year with id: {pk} not found"
            self.debug(message)
            return Response(
                data=GenericResponse(message).data, 
                status=status.HTTP_404_NOT_FOUND
                )
        
        response = YearResponseSerializer(year)
        self.debug(f"Year found: {response.data}")
        return Response(
            data=response.data, 
            status=status.HTTP_200_OK
            )
    
    @extend_schema(
        tags=['Years'],
        summary="Updates a single year",
        description="Updates a single year in the database",
        responses={
            200: standardized_response(
                YearResponseSerializer,
                description="Year successfully updated in the database"
                ),
            404: standardized_response(
                None, 
                description="Year not found in the database"
                ),
            400: standardized_response(
                None, 
                description="Payload validation error"
                )   
        }
    )    
    def put(self, request: Request, pk: int, *args, **kwargs) -> Response:
        year = self.__get_year__(pk)
        if year is None:
            message = f"Cannot update year with id: {pk}. Not found in the database"
            self.debug(message)
            return Response(
                data=GenericResponse(message).data,
                status=status.HTTP_404_NOT_FOUND
                )
        
        updated_year = YearRequestSerializer(data=request.data, instance=year, partial=False)
        if updated_year.is_valid():
            instace=updated_year.save()
            return Response(
                data=YearResponseSerializer(instace).data, 
                status=status.HTTP_200_OK
                )
        
        return Response(
            data=updated_year.errors, 
            status=status.HTTP_400_BAD_REQUEST
            )
    
    @extend_schema(
        tags=['Years'],
        summary="Deletes a single year",
        description="Deletes a single year in the database",
        responses={
            200: standardized_response(
                GenericResponseSerializer,
                description="Year successfully deleted from the database"
                ),
            404: standardized_response(
                None,
                description="Year not found in the database"
                )
        }
    )    
    def delete(self, request: Request, pk: int, *args, **kwargs) -> Response:
        year = self.__get_year__(pk)
        if year is None:
            message=f"Cannot delete year with id: {pk}. Not found in the database"
            self.debug(message)
            return Response(
                GenericResponse(message).data, 
                status=status.HTTP_404_NOT_FOUND
                )
        
        year.delete()
        return Response(
            GenericResponse(f"Year with id: {pk} deleted").data, 
            status=status.HTTP_200_OK
            )