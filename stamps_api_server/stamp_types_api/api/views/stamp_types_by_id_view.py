from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema

from common.log.logger import Logger
from common.api.serializers.generic_response import GenericResponse, GenericResponseSerializer
from common.core.schemas import standardized_response
from stamp_types_api.models import StampType
from stamp_types_api.api.serializers.stamp_type_response_serializer import StampTypeResponseSerializer
from stamp_types_api.api.serializers.stamp_type_request_serializer import StampTypeRequestSerializer


class StampTypesByIdView(Logger, APIView):
    def __get_stamp_type__(self, pk: int) -> StampType:
        try:
            self.debug(f"Querying database for stamp type with id: {pk}")
            return StampType.objects.get(pk = pk)
        except StampType.DoesNotExist:
            self.warning(f"StampType with id {pk} does not exist in the database.")
            return None
        except Exception as e:
            self.error(f"An unexpected error occurred while fetching stamp type with id {pk}: {str(e)}")
            return None
    
    @extend_schema(
        tags=['Stamp Types'],
        summary="Retrieve a Stamp Type by ID",
        description="Fetches the details of a specific stamp type entry by its unique identifier.",
        responses={
            200: standardized_response(
                StampTypeResponseSerializer,
                name="StampTypeRetrieved",
                description="The requested stamp type's data was retrieved successfully."
                ),
            404: standardized_response(
                GenericResponseSerializer,
                name="RetrieveStampTypeNotFound",
                success=False,
                description="No stamp type was found for the provided ID."
                ) 
        }
    )    
    def get(self, request: Request, pk: int, *args, **kwargs) -> Response:
        self.debug(f"Attempting to retrieve stamp type for id: {pk}")
        stamp_type = self.__get_stamp_type__(pk)
        
        if stamp_type is None:
            message = f"StampType with id: {pk} not found"
            self.warning(message)
            return Response(
                data=GenericResponseSerializer(GenericResponse(message)).data,
                status=status.HTTP_404_NOT_FOUND
                )
        
        response = StampTypeResponseSerializer(stamp_type)
        self.info(f"Successfully retrieved stamp type with id: {pk}")
        return Response(
            data=response.data, 
            status=status.HTTP_200_OK
            )
    
    @extend_schema(
        tags=['Stamp Types'],
        summary="Update a Stamp Type",
        description="Updates an existing stamp type entry identified by its ID. A complete payload with all required fields is expected.",
        request=StampTypeRequestSerializer,
        responses={
            200: standardized_response(
                StampTypeResponseSerializer,
                name="StampTypeUpdated",
                description="The stamp type was updated successfully."
                ),
            404: standardized_response(
                GenericResponseSerializer,
                name="StampTypeUpdateNotFound",
                success=False,
                description="The stamp type with the specified ID was not found."
                ),
            400: standardized_response(
                GenericResponseSerializer,
                name="StampTypeUpdateInvalidPayload",
                success=False,
                description="The request payload was invalid."
                )   
        }
    )    
    def put(self, request: Request, pk: int, *args, **kwargs) -> Response:
        self.debug(f"Attempting to update stamp type for id: {pk} with payload: {request.data}")
        stamp_type = self.__get_stamp_type__(pk)
        if stamp_type is None:
            message = f"Cannot update StampType with id: {pk}. Not found in the database"
            self.warning(message)
            return Response(
                data=GenericResponseSerializer(GenericResponse(message)).data,
                status=status.HTTP_404_NOT_FOUND
                )
        
        updated_stamp_type = StampTypeRequestSerializer(data=request.data, instance=stamp_type, partial=False)
        if updated_stamp_type.is_valid():
            instance=updated_stamp_type.save()
            self.info(f"Successfully updated stamp type with id: {instance.id}")
            return Response(
                data=StampTypeResponseSerializer(instance).data,
                status=status.HTTP_200_OK
                )
        
        self.warning(f"Payload validation failed for stamp type update (id: {pk}): {updated_stamp_type.errors}")
        return Response(
            data=GenericResponseSerializer(GenericResponse(updated_stamp_type.errors)).data,
            status=status.HTTP_400_BAD_REQUEST
            )
    
    @extend_schema(
        tags=['Stamp Types'],
        summary="Delete a Stamp Type",
        description="Deletes a stamp type entry from the database using its ID.",
        responses={
            200: standardized_response(
                GenericResponseSerializer,
                name="StampTypeDeleted",
                success=True,
                description="The stamp type was deleted successfully."
                ),
            404: standardized_response(
                GenericResponseSerializer,
                name="StampTypeDeleteNotFound",
                success=False,
                description="The stamp type with the specified ID was not found."
                )
        }
    )    
    def delete(self, request: Request, pk: int, *args, **kwargs) -> Response:
        self.debug(f"Attempting to delete stamp type for id: {pk}")
        stamp_type = self.__get_stamp_type__(pk)
        if stamp_type is None:
            message=f"Cannot delete StampType with id: {pk}. Not found in the database"
            self.warning(message)
            return Response(
                data=GenericResponseSerializer(GenericResponse(message)).data,
                status=status.HTTP_404_NOT_FOUND
                )
        
        stamp_type.delete()
        message = f"Successfully deleted StampType with id: {pk}"
        self.info(message)
        return Response(
            data=GenericResponseSerializer(GenericResponse(message)).data,
            status=status.HTTP_200_OK
            )