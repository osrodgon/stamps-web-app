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
            self.debug(f"Querying database for year with id: {pk}")
            return Year.objects.get(pk = pk)
        except Year.DoesNotExist:
            self.warning(f"Year with id {pk} does not exist in the database.")
            return None
        except Exception as e:
            self.error(f"An unexpected error occurred while fetching year with id {pk}: {str(e)}")
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
        summary="Retrieve a Year by ID",
        description="Fetches the details of a specific year entry by its unique identifier. If the year exists, its data is returned. Otherwise, a 404 Not Found error is returned.",
        responses={
            200: standardized_response(
                YearResponseSerializer,
                description="The requested year's data was retrieved successfully."
                ),
            404: standardized_response(
                GenericResponseSerializer,
                success=False,
                description="No year was found for the provided ID."
                ) 
        }
    )    
    def get(self, request: Request, pk: int, *args, **kwargs) -> Response:
        self.debug(f"Attempting to retrieve year for id: {pk}")
        year = self.__get_year__(pk)
        
        if year is None:
            message = f"Year with id: {pk} not found"
            self.warning(message)
            return Response(
                data=GenericResponseSerializer(GenericResponse(message)).data,
                status=status.HTTP_404_NOT_FOUND
                )
        
        response = YearResponseSerializer(year)
        self.info(f"Successfully retrieved year with id: {pk}")
        return Response(
            data=response.data, 
            status=status.HTTP_200_OK
            )
    
    @extend_schema(
        tags=['Years'],
        summary="Update a Year",
        description="Updates an existing year entry identified by its ID. A complete payload with all required fields is expected. If the update is successful, the updated year data is returned. Returns a 404 error if the year does not exist or a 400 error for an invalid payload.",
        request=YearRequestSerializer,
        responses={
            200: standardized_response(
                YearResponseSerializer,
                description="The year was updated successfully."
                ),
            404: standardized_response(
                GenericResponseSerializer, 
                success=False,
                description="The year with the specified ID was not found."
                ),
            400: standardized_response(
                GenericResponseSerializer,
                success=False,
                description="The request payload was invalid."
                )   
        }
    )    
    def put(self, request: Request, pk: int, *args, **kwargs) -> Response:
        self.debug(f"Attempting to update year for id: {pk} with payload: {request.data}")
        year = self.__get_year__(pk)
        if year is None:
            message = f"Cannot update year with id: {pk}. Not found in the database"
            self.warning(message)
            return Response(
                data=GenericResponseSerializer(GenericResponse(message)).data,
                status=status.HTTP_404_NOT_FOUND
                )
        
        updated_year = YearRequestSerializer(data=request.data, instance=year, partial=False)
        if updated_year.is_valid():
            instance=updated_year.save()
            self.info(f"Successfully updated year with id: {instance.id}")
            return Response(
                data=YearResponseSerializer(instance).data,
                status=status.HTTP_200_OK
                )
        
        self.warning(f"Payload validation failed for year update (id: {pk}): {updated_year.errors}")
        return Response(
            data=GenericResponseSerializer(GenericResponse(updated_year.errors)).data,
            status=status.HTTP_400_BAD_REQUEST
            )
    
    @extend_schema(
        tags=['Years'],
        summary="Delete a Year",
        description="Deletes a year entry from the database using its ID. If the deletion is successful, a confirmation message is returned. A 404 error is returned if the year with the specified ID does not exist.",
        responses={
            200: standardized_response(
                GenericResponseSerializer,
                description="The year was deleted successfully."
                ),
            404: standardized_response(
                GenericResponseSerializer,
                success=False,
                description="The year with the specified ID was not found."
                )
        }
    )    
    def delete(self, request: Request, pk: int, *args, **kwargs) -> Response:
        self.debug(f"Attempting to delete year for id: {pk}")
        year = self.__get_year__(pk)
        if year is None:
            message=f"Cannot delete year with id: {pk}. Not found in the database"
            self.warning(message)
            return Response(
                data=GenericResponseSerializer(GenericResponse(message)).data,
                status=status.HTTP_404_NOT_FOUND
                )
        
        year.delete()
        message = f"Successfully deleted year with id: {pk}"
        self.info(message)
        return Response(
            data=GenericResponseSerializer(GenericResponse(message)).data,
            status=status.HTTP_200_OK
            )