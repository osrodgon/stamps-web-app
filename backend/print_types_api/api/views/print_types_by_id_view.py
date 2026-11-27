from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema

from common.api.messages import Messages
from common.log.logger import Logger
from common.api.serializers.generic_response import GenericResponse, GenericResponseSerializer
from common.core.schemas import standardized_response
from print_types_api.models import PrintType
from print_types_api.api.serializers.print_type_response_serializer import PrintTypeResponseSerializer
from print_types_api.api.serializers.print_type_request_serializer import PrintTypeRequestSerializer


class PrintTypesByIdView(Logger, APIView):
    """
    API view for handling individual PrintType instances.

    This view provides GET, PUT, and DELETE operations for a specific
    print type identified by its primary key.
    """
    serializer_class = PrintTypeResponseSerializer
    
    def __get_print_type(self, pk: int) -> PrintType:
        """
        Helper method to retrieve a PrintType object by its primary key.

        Args:
            pk: The primary key of the print type to retrieve.

        Returns:
            The PrintType instance if found, otherwise None.
        """
        try:
            Messages.Database.querying("PrintType", pk)
            return PrintType.objects.get(pk=pk)
        except PrintType.DoesNotExist:
            Messages.Database.not_found("PrintType", pk)
            return None
    
    @extend_schema(
        operation_id="retrieve_print_type",
        tags=['Database Management'],
        summary="Retrieve a Print Type by ID",
        description="Fetches the details of a specific print type entry by its unique identifier.",
        responses={
            status.HTTP_200_OK: standardized_response(
                PrintTypeResponseSerializer,
                name="PrintTypeRetrieved",
                description="The requested print type's data was retrieved successfully."
            ),
            status.HTTP_403_FORBIDDEN: standardized_response(
                PrintTypeResponseSerializer,
                name="PrintTypeRetrieveForbidden",
                success=False,
                description="Permission denied."
            ),
            status.HTTP_404_NOT_FOUND: standardized_response(
                GenericResponseSerializer,
                name="RetrievePrintTypeNotFound",
                success=False,
                description="No print type was found for the provided ID."
            ) 
        }
    )    
    def get(self, request: Request, pk: int, *args, **kwargs) -> Response:
        """
        Handles GET requests to retrieve a single print type by its ID.

        Args:
            request: The incoming HTTP request.
            pk: The primary key of the print type to retrieve.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            A Response object containing the serialized print type data with a
            200 OK status, or a 404 Not Found if the print type does not exist.
        """
        self.log.debug(Messages.Get.retrieve_one("print type", pk))
        print_type = self.__get_print_type(pk)
        
        if print_type is None:
            message = Messages.Get.not_found("print type", pk)
            self.log.warning(message)
            return Response(
                data=GenericResponseSerializer(GenericResponse(message)).data,
                status=status.HTTP_404_NOT_FOUND
                )
        
        response = PrintTypeResponseSerializer(print_type)
        self.log.info(Messages.Get.retrieved_one("print type", pk))
        return Response(
            data=response.data, 
            status=status.HTTP_200_OK
            )
    
    @extend_schema(
        operation_id="update_print_type",
        tags=['Database Management'],
        summary="Update a Print Type",
        description="Updates an existing print type entry identified by its ID. A complete payload with all required fields is expected.",
        request=PrintTypeRequestSerializer,
        responses={
            status.HTTP_200_OK: standardized_response(
                PrintTypeResponseSerializer,
                name="PrintTypeUpdated",
                description="The print type was updated successfully."
                ),
            status.HTTP_403_FORBIDDEN: standardized_response(
                PrintTypeResponseSerializer,
                name="PrintTypeUpdateForbidden",
                success=False,
                description="Permission denied."
            ),
            status.HTTP_404_NOT_FOUND: standardized_response(
                GenericResponseSerializer,
                name="PrintTypeUpdateNotFound",
                success=False,
                description="The print type with the specified ID was not found."
                ),
            status.HTTP_400_BAD_REQUEST: standardized_response(
                GenericResponseSerializer,
                name="PrintTypeUpdateInvalidPayload",
                success=False,
                description="The request payload was invalid."
                )   
        }
    )    
    def put(self, request: Request, pk: int, *args, **kwargs) -> Response:
        """
        Handles PUT requests to update an existing print type.

        Args:
            request: The incoming HTTP request containing the update data.
            pk: The primary key of the print type to update.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            A Response object with the updated print type data and a 200 OK status
            if successful. Returns a 404 Not Found if the print type does not exist,
            or a 400 Bad Request if the provided data is invalid.
        """
        self.log.debug(Messages.Put.update_one("print type", pk, request.data))
        print_type = self.__get_print_type(pk)
        if print_type is None:
            message = Messages.Put.not_found("print type", pk)
            self.log.warning(message)
            return Response(
                data=GenericResponseSerializer(GenericResponse(message)).data,
                status=status.HTTP_404_NOT_FOUND
                )
        
        updated_print_type = PrintTypeRequestSerializer(data=request.data, instance=print_type, partial=False)
        if updated_print_type.is_valid():
            instance = updated_print_type.save()
            self.log.info(Messages.Put.updated_one("print type", instance.id))
            return Response(
                data=PrintTypeResponseSerializer(instance).data,
                status=status.HTTP_200_OK
                )
        
        self.log.warning(Messages.Put.validation_failed("print type", pk, updated_print_type.errors))
        return Response(
            data=GenericResponseSerializer(GenericResponse(updated_print_type.errors)).data,
            status=status.HTTP_400_BAD_REQUEST
            )
    
    @extend_schema(
        operation_id="delete_print_type",
        tags=['Database Management'],
        summary="Delete a Print Type",
        description="Deletes a print type entry from the. database using its ID.",
        responses={
            status.HTTP_200_OK: standardized_response(
                GenericResponseSerializer,
                name="PrintTypeDeleted",
                success=True,
                description="The print type was deleted successfully."
                ),
            status.HTTP_403_FORBIDDEN: standardized_response(
                PrintTypeResponseSerializer,
                name="PrintTypeDeleteForbidden",
                success=False,
                description="Permission denied."
            ),
            status.HTTP_404_NOT_FOUND: standardized_response(
                GenericResponseSerializer,
                name="PrintTypeDeleteNotFound",
                success=False,
                description="The print type with the specified ID was not found."
                )
        }
    )    
    def delete(self, request: Request, pk: int, *args, **kwargs) -> Response:
        """
        Handles DELETE requests to remove a print type.

        Args:
            request: The incoming HTTP request.
            pk: The primary key of the print type to delete.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            A Response object with a success message and a 200 OK status if
            the deletion was successful, or a 404 Not Found if the print type does not exist.
        """
        self.log.debug(Messages.Delete.delete_one("print type", pk))
        print_type = self.__get_print_type(pk)
        if print_type is None:
            message=Messages.Delete.not_found("print type", pk)
            self.log.warning(message)
            return Response(
                data=GenericResponseSerializer(GenericResponse(message)).data,
                status=status.HTTP_404_NOT_FOUND
                )
        
        print_type.delete()
        message = Messages.Delete.deleted_one("print type", pk)
        self.log.info(message)
        return Response(
            data=GenericResponseSerializer(GenericResponse(message)).data,
            status=status.HTTP_200_OK
            )