from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema

from common.api.messages import Messages
from common.api.serializers.generic_response import GenericResponseSerializer, GenericResponse
from common.log.logger import Logger
from common.core.schemas import standardized_response
from printers_api.models import Printer
from printers_api.api.serializers.printer_response_serializer import PrinterResponseSerializer
from printers_api.api.serializers.printer_request_serializer import PrinterRequestSerializer

class PrintersView(Logger, APIView):
    """Manages bulk API operations for Printer instances.

    This view handles the retrieval of all printers (GET) and the creation
    of a new printer (POST).
    """
    serializer_class = PrinterResponseSerializer
    
    @extend_schema(
        operation_id="list_printers",
        tags=['Database Management'],
        summary="List All Printers",
        description="Retrieves a list of all printer entries currently stored in the database.",
        responses={
            200: standardized_response(
                PrinterResponseSerializer, 
                name="PrintersRetrieved",
                description="A list of printers was successfully retrieved.",
                many=True
                ),
            403: standardized_response(
                PrinterResponseSerializer,
                name="PrintersForbidden",
                success=False,
                description="Permission denied."
                )   
        }
    )
    def get(self, request:Request, *args, **kwargs) -> Response:
        """Handles GET requests to retrieve all printers.

        Args:
            request (Request): The incoming HTTP request.

        Returns:
            Response:   A DRF Response object containing a list of all serialized
                        printer objects and a 200 OK status.
        """
        self.log.debug(Messages.Get.retrieve_all("printers"))
        printers = Printer.objects.all()
        self.log.debug(Messages.Get.retrieved_all("printers", printers.count()))
        response = PrinterResponseSerializer(printers, many=True)
        
        return Response(
            data=response.data, 
            status=status.HTTP_200_OK
            )
    
    @extend_schema(
        operation_id="create_printer",
        tags=['Database Management'],
        summary="Create a New Printer",
        description="Adds a new printer entry to the database. A successful creation returns the newly created printer object with a 201 Created status code.",
        request=PrinterRequestSerializer,
        responses={
            status.HTTP_201_CREATED: standardized_response(
                PrinterResponseSerializer,
                name="PrinterCreated",
                description="The printer was created successfully."
                ),
            status.HTTP_400_BAD_REQUEST: standardized_response(
                GenericResponseSerializer,
                name="PrinterCreateInvalidPayload",
                success=False,
                description="The request payload was invalid (e.g., missing a required field)."
                ),
            status.HTTP_403_FORBIDDEN: standardized_response(
                PrinterResponseSerializer,
                name="PrinterCreateForbidden",
                success=False,
                description="Permission denied."
                )   
        }
    )
    def post(self, request:Request, *args, **kwargs) -> Response:
        """Handles POST requests to create a new printer.

        Args:
            request (Request):  The incoming HTTP request containing the data for
                                the new printer.

        Returns:
            Response:   A DRF Response with the newly created printer's data and a
                        201 Created status, or a 400 Bad Request on validation error.
        """
        self.log.debug(Messages.Post.create_one("printer", request.data))
        printer = PrinterRequestSerializer(data = request.data)
        
        if printer.is_valid():
            instance = printer.save()
            self.log.info(Messages.Post.created_one("printer", instance.id))
            return Response(
                data=PrinterResponseSerializer(instance).data, 
                status=status.HTTP_201_CREATED
                )
        
        self.log.warning(Messages.Post.validation_failed("printer", printer.errors))
        return Response(
            data=GenericResponseSerializer(GenericResponse(printer.errors)).data,
            status=status.HTTP_400_BAD_REQUEST
            )

