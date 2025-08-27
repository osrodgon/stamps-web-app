from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema

from common.log.logger import Logger
from common.api.serializers.generic_response import GenericResponse
from years_api.models import Year
from years_api.api.serializers.year_response_serializer import YearResponseSerializer
from years_api.api.serializers.year_request_serializer import YearRequestSerializer


class YearsByIdView(Logger, APIView):
    """Handles REST operation for single entries in the Year table

    Args:
        Logger: Abstract class for logging
        APIView: Abstract class
    """
    
    def __get_year__(self, pk: int) -> Year:
        """Gets a single record from the year table or None if it does not exist

        Args:
            pk (int): Id of the year to retrieve from the table

        Returns:
            Year: A record from the table
        """
        try:
            self.debug(f"Getting a year from database with id: {pk}")
            return Year.objects.get(pk = pk)
        except Year.DoesNotExist:
            self.warning(f"Year with id {pk} does not exist.")
            return None
        except Exception as e:
            self.warning(f"A unknown error has occured: {e.message}")
            return None
    
    @swagger_auto_schema(
        tags=['Years'],
        operation_description="Gets a single year",
        responses={
            200: YearResponseSerializer(many=False),
            204: GenericResponse().serializer
        }
    )       
    def get(self, request: Request, pk: int, *args, **kwargs) -> Response:
        """GET opration for a single entry

        Args:
            request (Request): Request data
            pk (int): Id of the year to be retrieved

        Returns:
            Response:   200. The year
                        204. Year not found
        """
        self.debug(f"GET year with id: {pk}")
        year = self.__get_year__(pk)
        
        if year is None:
            message = f"Year with id: {pk} not found"
            self.debug(message)
            return Response(
                data=GenericResponse(message).data, 
                status=status.HTTP_204_NO_CONTENT
                )
        
        response = YearResponseSerializer(year)
        self.debug(f"Year found: {response.data}")
        return Response(
            data=response.data, 
            status=status.HTTP_200_OK
            )
    
    @swagger_auto_schema(
        tags=['Years'],
        operation_description="Updates a single year",
        responses={
            200: YearResponseSerializer(many=False),
            204: GenericResponse().serializer,
            404: YearRequestSerializer(many=False)
        }
    )  
    def put(self, request: Request, pk: int, *args, **kwargs) -> Response:
        """PUT operation (update) for a single entry

        Args:
            request (Request): Request payload
            pk (int): Id of the year to be updated

        Returns:
            Response:   200. Year updated
                        204. Year not found
                        404. Bad request (i.e: wrong payload)
        """
        year = self.__get_year__(pk)
        if year is None:
            message = f"Cannot update year with id: {pk}. Not found in the database"
            self.debug(message)
            return Response(
                data=GenericResponse(message).data,
                status=status.HTTP_204_NO_CONTENT
                )
        
        updated_year = YearRequestSerializer(data=request.data, instance=year, partial=False)
        if updated_year.is_valid():
            updated_year.save()
            return Response(
                data=updated_year.data, 
                status=status.HTTP_200_OK
                )
        
        return Response(
            data=updated_year.errors, 
            status=status.HTTP_400_BAD_REQUEST
            )
    
    @swagger_auto_schema(
        tags=['Years'],
        operation_description="Deletes a single year",
        responses={
            200: GenericResponse().serializer,
            204: GenericResponse().serializer
        }
    )  
    def delete(self, request: Request, pk: int, *args, **kwargs) -> Response:
        """DELETE year from database

        Args:
            request (Request): Request data
            pk (int): Id of the year to be deleted

        Returns:
            Response:   200. Year deleted
                        204. Year not found
        """
        year = self.__get_year__(pk)
        if year is None:
            message=f"Cannot delete year with id: {pk}. Not found in the database"
            self.debug(message)
            return Response(
                GenericResponse(message).data, 
                status=status.HTTP_204_NO_CONTENT
                )
        
        year.delete()
        return Response(
            GenericResponse(f"Year with id: {pk} deleted").data, 
            status=status.HTTP_200_OK
            )