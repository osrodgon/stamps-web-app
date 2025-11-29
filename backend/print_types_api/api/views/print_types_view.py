from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema

from common.api.messages import Messages
from common.api.serializers.generic_response import GenericResponseSerializer, GenericResponse
from common.log.logger import Logger
from common.core.schemas import standardized_response
from print_types_api.models import PrintType
from print_types_api.api.serializers.print_type_response_serializer import PrintTypeResponseSerializer
from print_types_api.api.serializers.print_type_request_serializer import PrintTypeRequestSerializer


class PrintTypesView(Logger, APIView):
    """
    API view for handling collections of PrintType instances.

    This view provides GET (list) and POST (create) operations for print types.
    """
    serializer_class = PrintTypeResponseSerializer
    
    @extend_schema(
        operation_id="list_print_types",
        tags=['Database Management'],
        summary="List All Print Types",
        description="Retrieves a list of all print type entries currently stored in the database.",
        responses={
            status.HTTP_200_OK: standardized_response(
                PrintTypeResponseSerializer, 
                name="PrintTypesRetrieved",
                description="A list of print types was successfully retrieved.",
                many=True
                ),
            status.HTTP_403_FORBIDDEN: standardized_response(
                PrintTypeResponseSerializer,
                name="PrintTypesRetrieveForbidden",
                success=False,
                description="Permission denied."
            )
        }
    )
    def get(self, request:Request, *args, **kwargs) -> Response:
        """
        Handles GET requests to retrieve a list of all print types.

        Args:
            request: The incoming HTTP request.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            A Response object containing a list of all serialized print types
            with a 200 OK status.
        """
        self.log.debug(Messages.Get.retrieve_all("print types"))
        print_types = PrintType.objects.all()
        self.log.debug(Messages.Get.retrieved_all("print types", len(print_types)))
        response = PrintTypeResponseSerializer(print_types, many=True)
        
        return Response(
            data=response.data, 
            status=status.HTTP_200_OK
            )
    
    @extend_schema(
        operation_id="create_print_type",
        tags=['Database Management'],
        summary="Create a New Print Type",
        description="Adds a new print type entry to the database. A successful creation returns the newly created print type object with a 201 Created status code.",
        request=PrintTypeRequestSerializer,
        responses={
            status.HTTP_201_CREATED: standardized_response(
                PrintTypeResponseSerializer,
                name="PrintTypeCreated",
                description="The print type was created successfully."
                ),
            status.HTTP_400_BAD_REQUEST: standardized_response(
                GenericResponseSerializer,
                name="PrintTypeCreateInvalidPayload",
                success=False,
                description="The request payload was invalid (e.g., missing a required field)."
                ),
            status.HTTP_403_FORBIDDEN: standardized_response(
                PrintTypeResponseSerializer,
                name="PrintTypeCreateForbidden",
                success=False,
                description="Permission denied."
            )
        }
    )
    def post(self, request:Request, *args, **kwargs) -> Response:
        """
        Handles POST requests to create a new print type.

        Args:
            request: The incoming HTTP request containing the new print type data.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            A Response object with the newly created print type data and a 201 Created
            status if successful. Returns a 400 Bad Request if the provided
            data is invalid.
        """
        self.log.debug(Messages.Post.create_one("print type", request.data))
        print_type = PrintTypeRequestSerializer(data = request.data)
        
        if print_type.is_valid():
            instance = print_type.save()
            self.log.info(Messages.Post.created_one("print type", instance.id))
            return Response(
                data=PrintTypeResponseSerializer(instance).data, 
                status=status.HTTP_201_CREATED
                )
        
        self.log.warning(Messages.Post.validation_failed("print type", print_type.errors))
        return Response(
            data=GenericResponseSerializer(GenericResponse(print_type.errors)).data,
            status=status.HTTP_400_BAD_REQUEST
            )