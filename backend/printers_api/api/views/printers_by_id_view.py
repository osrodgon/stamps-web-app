from re import M
from common.api.messages import Messages
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema

from common.log.logger import Logger
from common.api.serializers.generic_response import GenericResponse, GenericResponseSerializer
from common.core.schemas import standardized_response
from printers_api.models import Printer
from printers_api.api.serializers.printer_response_serializer import PrinterResponseSerializer
from printers_api.api.serializers.printer_request_serializer import PrinterRequestSerializer


class PrintersByIdView(Logger, APIView):
    """Manages API operations for a single Printer instance.

    This view handles the retrieval (GET), update (PUT), and deletion (DELETE)
    of a specific `Printer` object, identified by its primary key (`pk`)
    provided in the URL.
    """
    serializer_class = PrinterResponseSerializer
    def __get_printer(self, pk: int) -> Printer:
        """Retrieves a Printer instance by its primary key.

        Args:
            pk (int): The primary key of the printer to retrieve.

        Returns:
            Printer: The found printer instance, or None if it does not exist.
        """
        try:
            self.log.debug(Messages.Database.querying("printer", pk))
            return Printer.objects.get(pk=pk)
        except Printer.DoesNotExist:
            self.log.warning(Messages.Database.not_found("printer", pk))
            return None
    
    @extend_schema(
        operation_id="retrieve_printer",
        tags=['Database Management'],
        summary="Retrieve a Printer by ID",
        description="Fetches the details of a specific printer entry by its unique identifier.",
        responses={
            200: standardized_response(
                PrinterResponseSerializer,
                name="PrinterRetrieved",
                description="The requested printer's data was retrieved successfully."
                ),
            404: standardized_response(
                GenericResponseSerializer,
                name="RetrievePrinterNotFound",
                success=False,
                description="No printer was found for the provided ID."
                ),
            403: standardized_response(
                PrinterResponseSerializer,
                name="RetrievePrinterForbidden",
                success=False,
                description="Permission denied."
                )   
        }
    )    
    def get(self, request: Request, pk: int, *args, **kwargs) -> Response:
        """Handles GET requests to retrieve a single printer.

        Args:
            request (Request): The incoming HTTP request.
            pk (int): The primary key of the printer to retrieve.

        Returns:
            Response:   A DRF Response object with the serialized printer
                        data and 200 OK status, or a 404 Not Found response.
        """
        self.log.debug(Messages.Get.retrieve_one("printer", pk))
        printer = self.__get_printer(pk)
        
        if printer is None:
            message = Messages.Get.not_found("printer", pk)
            self.log.warning(message)
            return Response(
                data=GenericResponseSerializer(GenericResponse(message)).data,
                status=status.HTTP_404_NOT_FOUND
                )
        
        response = PrinterResponseSerializer(printer)
        self.log.info(Messages.Get.retrieved_one("printer", pk))
        return Response(
            data=response.data, 
            status=status.HTTP_200_OK
            )
    
    @extend_schema(
        operation_id="update_printer",
        tags=['Database Management'],
        summary="Update a Printer",
        description="Updates an existing printer entry identified by its ID. A complete payload with all required fields is expected.",
        request=PrinterRequestSerializer,
        responses={
            status.HTTP_200_OK: standardized_response(
                PrinterResponseSerializer,
                name="PrinterUpdated",
                description="The printer was updated successfully."
                ),
            status.HTTP_400_BAD_REQUEST: standardized_response(
                GenericResponseSerializer,
                name="PrinterUpdateInvalidPayload",
                success=False,
                description="The request payload was invalid."
                ),
            status.HTTP_403_FORBIDDEN: standardized_response(
                PrinterResponseSerializer,
                name="PrinterUpdateForbidden",
                success=False,
                description="Permission denied."
                ),    
            status.HTTP_404_NOT_FOUND: standardized_response(
                GenericResponseSerializer,
                name="PrinterUpdateNotFound",
                success=False,
                description="The printer with the specified ID was not found."
                )
        }
    )    
    def put(self, request: Request, pk: int, *args, **kwargs) -> Response:
        """Handles PUT requests to update an existing printer.

        Args:
            request (Request): The incoming HTTP request containing update data.
            pk (int): The primary key of the printer to update.

        Returns:
            Response:   A DRF Response with updated data and 200 OK status,
                        a 404 if not found, or a 400 on validation error.
        """
        self.log.debug(Messages.Put.update_one("printer", pk, request.data))
        printer = self.__get_printer(pk)
        if printer is None:
            message = Messages.Put.not_found("printer", pk)
            self.log.warning(message)
            return Response(
                data=GenericResponseSerializer(GenericResponse(message)).data,
                status=status.HTTP_404_NOT_FOUND
                )
        
        updated_printer = PrinterRequestSerializer(data=request.data, instance=printer, partial=False)
        if updated_printer.is_valid():
            instance = updated_printer.save()
            self.log.info(Messages.Put.updated_one("printer", instance.id))
            return Response(
                data=PrinterResponseSerializer(instance).data,
                status=status.HTTP_200_OK
                )
        
        self.log.warning(Messages.Put.validation_failed("printer", pk, updated_printer.errors))
        return Response(
            data=GenericResponseSerializer(GenericResponse(updated_printer.errors)).data,
            status=status.HTTP_400_BAD_REQUEST
            )
    
    @extend_schema(
        operation_id="delete_printer",
        tags=['Database Management'],
        summary="Delete a Printer",
        description="Deletes a printer entry from the database using its ID.",
        responses={
            status.HTTP_200_OK: standardized_response(
                GenericResponseSerializer,
                name="PrinterDeleted",
                success=True,
                description="The printer was deleted successfully."
                ),
            status.HTTP_403_FORBIDDEN: standardized_response(
                PrinterResponseSerializer,
                name="PrinterDeleteForbidden",
                success=False,
                description="Permission denied."
                ),   
            status.HTTP_404_NOT_FOUND: standardized_response(
                GenericResponseSerializer,
                name="PrinterDeleteNotFound",
                success=False,
                description="The printer with the specified ID was not found."
                )
        }
    )    
    def delete(self, request: Request, pk: int, *args, **kwargs) -> Response:
        """Handles DELETE requests to remove a printer.

        Args:
            request (Request): The incoming HTTP request.
            pk (int): The primary key of the printer to delete.

        Returns:
            Response:   A DRF Response with a success message and 200 OK status,
                        or a 404 Not Found response if the item does not exist.
        """
        self.log.debug(Messages.Delete.delete_one("printer", pk))
        printer = self.__get_printer(pk)
        if printer is None:
            message = Messages.Delete.not_found("printer", pk)
            self.log.warning(message)
            return Response(
                data=GenericResponseSerializer(GenericResponse(message)).data,
                status=status.HTTP_404_NOT_FOUND
                )
        
        printer.delete()
        message = Messages.Delete.deleted_one("printer", pk)
        self.log.info(message)
        return Response(
            data=GenericResponseSerializer(GenericResponse(message)).data,
            status=status.HTTP_200_OK
            )
