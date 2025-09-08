from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema

from common.log.logger import Logger
from common.api.serializers.generic_response import GenericResponse, GenericResponseSerializer
from common.core.schemas import standardized_response
from paper_types_api.models import PaperType
from paper_types_api.api.serializers.paper_type_response_serializer import PaperTypeResponseSerializer
from paper_types_api.api.serializers.paper_type_request_serializer import PaperTypeRequestSerializer


class PaperTypesByIdView(Logger, APIView):
    def __get_paper_type__(self, pk: int) -> PaperType:
        try:
            self.debug(f"Querying database for paper type with id: {pk}")
            return PaperType.objects.get(pk = pk)
        except PaperType.DoesNotExist:
            self.warning(f"Paper type with id {pk} does not exist in the database.")
            return None
        except Exception as e:
            self.error(f"An unexpected error occurred while fetching paper type with id {pk}: {str(e)}")
            return None
    
    @extend_schema(
        tags=['Paper Types'],
        summary="Retrieve a Paper Type by ID",
        description="Fetches the details of a specific paper type entry by its unique identifier.",
        responses={
            200: standardized_response(
                PaperTypeResponseSerializer,
                name="PaperTypeRetrieved",
                description="The requested paper type's data was retrieved successfully."
                ),
            404: standardized_response(
                GenericResponseSerializer,
                name="RetrievePaperTypeNotFound",
                success=False,
                description="No paper type was found for the provided ID."
                ) 
        }
    )    
    def get(self, request: Request, pk: int, *args, **kwargs) -> Response:
        self.debug(f"Attempting to retrieve paper type for id: {pk}")
        paper_type = self.__get_paper_type__(pk)
        
        if paper_type is None:
            message = f"Paper type with id: {pk} not found"
            self.warning(message)
            return Response(
                data=GenericResponseSerializer(GenericResponse(message)).data,
                status=status.HTTP_404_NOT_FOUND
                )
        
        response = PaperTypeResponseSerializer(paper_type)
        self.info(f"Successfully retrieved paper type with id: {pk}")
        return Response(
            data=response.data, 
            status=status.HTTP_200_OK
            )
    
    @extend_schema(
        tags=['Paper Types'],
        summary="Update a Paper Type",
        description="Updates an existing paper type entry identified by its ID. A complete payload with all required fields is expected.",
        request=PaperTypeRequestSerializer,
        responses={
            200: standardized_response(
                PaperTypeResponseSerializer,
                name="PaperTypeUpdated",
                description="The paper type was updated successfully."
                ),
            404: standardized_response(
                GenericResponseSerializer,
                name="PaperTypeUpdateNotFound",
                success=False,
                description="The paper type with the specified ID was not found."
                ),
            400: standardized_response(
                GenericResponseSerializer,
                name="PaperTypeUpdateInvalidPayload",
                success=False,
                description="The request payload was invalid."
                )   
        }
    )    
    def put(self, request: Request, pk: int, *args, **kwargs) -> Response:
        self.debug(f"Attempting to update paper type for id: {pk} with payload: {request.data}")
        paper_type = self.__get_paper_type__(pk)
        if paper_type is None:
            message = f"Cannot update Paper Type with id: {pk}. Not found in the database"
            self.warning(message)
            return Response(
                data=GenericResponseSerializer(GenericResponse(message)).data,
                status=status.HTTP_404_NOT_FOUND
                )
        
        updated_paper_type = PaperTypeRequestSerializer(data=request.data, instance=paper_type, partial=False)
        if updated_paper_type.is_valid():
            instance = updated_paper_type.save()
            self.info(f"Successfully updated paper type with id: {instance.id}")
            return Response(
                data=PaperTypeResponseSerializer(instance).data,
                status=status.HTTP_200_OK
                )
        
        self.warning(f"Payload validation failed for paper type update (id: {pk}): {updated_paper_type.errors}")
        return Response(
            data=GenericResponseSerializer(GenericResponse(updated_paper_type.errors)).data,
            status=status.HTTP_400_BAD_REQUEST
            )
    
    @extend_schema(
        tags=['Paper Types'],
        summary="Delete a Paper Type",
        description="Deletes a paper type entry from the. database using its ID.",
        responses={
            200: standardized_response(
                GenericResponseSerializer,
                name="PaperTypeDeleted",
                success=True,
                description="The paper type was deleted successfully."
                ),
            404: standardized_response(
                GenericResponseSerializer,
                name="PaperTypeDeleteNotFound",
                success=False,
                description="The paper type with the specified ID was not found."
                )
        }
    )    
    def delete(self, request: Request, pk: int, *args, **kwargs) -> Response:
        self.debug(f"Attempting to delete paper type for id: {pk}")
        paper_type = self.__get_paper_type__(pk)
        if paper_type is None:
            message=f"Cannot delete Paper Type with id: {pk}. Not found in the database"
            self.warning(message)
            return Response(
                data=GenericResponseSerializer(GenericResponse(message)).data,
                status=status.HTTP_404_NOT_FOUND
                )
        
        paper_type.delete()
        message = f"Successfully deleted Paper Type with id: {pk}"
        self.info(message)
        return Response(
            data=GenericResponseSerializer(GenericResponse(message)).data,
            status=status.HTTP_200_OK
            )