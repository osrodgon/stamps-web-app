from logging import warn
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema

from common.api.messages import Messages
from common.log.logger import Logger
from common.api.serializers.generic_response import GenericResponse, GenericResponseSerializer
from common.core.schemas import standardized_response
from paper_types_api.models import PaperType
from paper_types_api.api.serializers.paper_type_response_serializer import PaperTypeResponseSerializer
from paper_types_api.api.serializers.paper_type_request_serializer import PaperTypeRequestSerializer


class PaperTypesByIdView(Logger, APIView):
    """
    API view for handling individual PaperType instances.

    This view provides GET, PUT, and DELETE operations for a specific
    paper type identified by its primary key.
    """
    serializer_class = PaperTypeResponseSerializer
    
    def __get_paper_type(self, pk: int) -> PaperType:
        """
        Helper method to retrieve a PaperType object by its primary key.

        Args:
            pk: The primary key of the paper type to retrieve.

        Returns:
            The PaperType instance if found, otherwise None.
        """
        try:
            Messages.Database.querying("PaperType", pk)
            return PaperType.objects.get(pk=pk)
        except PaperType.DoesNotExist:
            Messages.Database.not_found("PaperType", pk)
            return None
    
    @extend_schema(
        operation_id="retrieve_paper_type",
        tags=['Database Management'],
        summary="Retrieve a Paper Type by ID",
        description="Fetches the details of a specific paper type entry by its unique identifier.",
        responses={
            status.HTTP_200_OK: standardized_response(
                PaperTypeResponseSerializer,
                name="PaperTypeRetrieved",
                description="The requested paper type's data was retrieved successfully."
            ),
            status.HTTP_403_FORBIDDEN: standardized_response(
                PaperTypeResponseSerializer,
                name="PaperTypeRetrieveForbidden",
                success=False,
                description="Permission denied."
            ),
            status.HTTP_404_NOT_FOUND: standardized_response(
                GenericResponseSerializer,
                name="RetrievePaperTypeNotFound",
                success=False,
                description="No paper type was found for the provided ID."
            ) 
        }
    )    
    def get(self, request: Request, pk: int, *args, **kwargs) -> Response:
        """
        Handles GET requests to retrieve a single paper type by its ID.

        Args:
            request: The incoming HTTP request.
            pk: The primary key of the paper type to retrieve.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            A Response object containing the serialized paper type data with a
            200 OK status, or a 404 Not Found if the paper type does not exist.
        """
        self.log.debug(Messages.Get.retrieve_one("paper type", pk))
        paper_type = self.__get_paper_type(pk)
        
        if paper_type is None:
            message = Messages.Get.not_found("paper type", pk)
            self.log.warning(message)
            return Response(
                data=GenericResponseSerializer(GenericResponse(message)).data,
                status=status.HTTP_404_NOT_FOUND
                )
        
        response = PaperTypeResponseSerializer(paper_type)
        self.log.info(Messages.Get.retrieved_one("paper type", pk))
        return Response(
            data=response.data, 
            status=status.HTTP_200_OK
            )
    
    @extend_schema(
        operation_id="update_paper_type",
        tags=['Database Management'],
        summary="Update a Paper Type",
        description="Updates an existing paper type entry identified by its ID. A complete payload with all required fields is expected.",
        request=PaperTypeRequestSerializer,
        responses={
            status.HTTP_200_OK: standardized_response(
                PaperTypeResponseSerializer,
                name="PaperTypeUpdated",
                description="The paper type was updated successfully."
                ),
            status.HTTP_403_FORBIDDEN: standardized_response(
                PaperTypeResponseSerializer,
                name="PaperTypeUpdateForbidden",
                success=False,
                description="Permission denied."
            ),
            status.HTTP_404_NOT_FOUND: standardized_response(
                GenericResponseSerializer,
                name="PaperTypeUpdateNotFound",
                success=False,
                description="The paper type with the specified ID was not found."
                ),
            status.HTTP_400_BAD_REQUEST: standardized_response(
                GenericResponseSerializer,
                name="PaperTypeUpdateInvalidPayload",
                success=False,
                description="The request payload was invalid."
                )   
        }
    )    
    def put(self, request: Request, pk: int, *args, **kwargs) -> Response:
        """
        Handles PUT requests to update an existing paper type.

        Args:
            request: The incoming HTTP request containing the update data.
            pk: The primary key of the paper type to update.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            A Response object with the updated paper type data and a 200 OK status
            if successful. Returns a 404 Not Found if the paper type does not exist,
            or a 400 Bad Request if the provided data is invalid.
        """
        self.log.debug(Messages.Put.update_one("paper type", pk, request.data))
        paper_type = self.__get_paper_type(pk)
        if paper_type is None:
            message = Messages.Put.not_found("paper type", pk)
            self.log.warning(message)
            return Response(
                data=GenericResponseSerializer(GenericResponse(message)).data,
                status=status.HTTP_404_NOT_FOUND
                )
        
        updated_paper_type = PaperTypeRequestSerializer(data=request.data, instance=paper_type, partial=False)
        if updated_paper_type.is_valid():
            instance = updated_paper_type.save()
            self.log.info(Messages.Put.updated_one("paper type", instance.id))
            return Response(
                data=PaperTypeResponseSerializer(instance).data,
                status=status.HTTP_200_OK
                )
        
        self.log.warning(Messages.Put.validation_failed("paper type", pk, updated_paper_type.errors))
        return Response(
            data=GenericResponseSerializer(GenericResponse(updated_paper_type.errors)).data,
            status=status.HTTP_400_BAD_REQUEST
            )
    
    @extend_schema(
        operation_id="delete_paper_type",
        tags=['Database Management'],
        summary="Delete a Paper Type",
        description="Deletes a paper type entry from the. database using its ID.",
        responses={
            status.HTTP_200_OK: standardized_response(
                GenericResponseSerializer,
                name="PaperTypeDeleted",
                success=True,
                description="The paper type was deleted successfully."
                ),
            status.HTTP_403_FORBIDDEN: standardized_response(
                PaperTypeResponseSerializer,
                name="PaperTypeDeleteForbidden",
                success=False,
                description="Permission denied."
            ),
            status.HTTP_404_NOT_FOUND: standardized_response(
                GenericResponseSerializer,
                name="PaperTypeDeleteNotFound",
                success=False,
                description="The paper type with the specified ID was not found."
                )
        }
    )    
    def delete(self, request: Request, pk: int, *args, **kwargs) -> Response:
        """
        Handles DELETE requests to remove a paper type.

        Args:
            request: The incoming HTTP request.
            pk: The primary key of the paper type to delete.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            A Response object with a success message and a 200 OK status if
            the deletion was successful, or a 404 Not Found if the paper type does not exist.
        """
        self.log.debug(Messages.Delete.delete_one("paper type", pk))
        paper_type = self.__get_paper_type(pk)
        if paper_type is None:
            message=Messages.Delete.not_found("paper type", pk)
            self.log.warning(message)
            return Response(
                data=GenericResponseSerializer(GenericResponse(message)).data,
                status=status.HTTP_404_NOT_FOUND
                )
        
        paper_type.delete()
        message = Messages.Delete.deleted_one("paper type", pk)
        self.log.info(message)
        return Response(
            data=GenericResponseSerializer(GenericResponse(message)).data,
            status=status.HTTP_200_OK
            )