import stat
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema

from common.api.messages import Messages
from common.api.serializers.generic_response import GenericResponseSerializer, GenericResponse
from common.log.logger import Logger
from common.core.schemas import standardized_response
from paper_types_api.models import PaperType
from paper_types_api.api.serializers.paper_type_response_serializer import PaperTypeResponseSerializer
from paper_types_api.api.serializers.paper_type_request_serializer import PaperTypeRequestSerializer


class PaperTypesView(Logger, APIView):
    """
    API view for handling collections of PaperType instances.

    This view provides GET (list) and POST (create) operations for paper types.
    """
    serializer_class = PaperTypeResponseSerializer
    
    @extend_schema(
        operation_id="list_paper_types",
        tags=['Database Management'],
        summary="List All Paper Types",
        description="Retrieves a list of all paper type entries currently stored in the database.",
        responses={
            status.HTTP_200_OK: standardized_response(
                PaperTypeResponseSerializer, 
                name="PaperTypesRetrieved",
                description="A list of paper types was successfully retrieved.",
                many=True
                ),
            status.HTTP_403_FORBIDDEN: standardized_response(
                PaperTypeResponseSerializer,
                name="PaperTypesRetrieveForbidden",
                success=False,
                description="Permission denied."
            )
        }
    )
    def get(self, request:Request, *args, **kwargs) -> Response:
        """
        Handles GET requests to retrieve a list of all paper types.

        Args:
            request: The incoming HTTP request.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            A Response object containing a list of all serialized paper types
            with a 200 OK status.
        """
        self.log.debug(Messages.Get.retrieve_all("paper types"))
        paper_types = PaperType.objects.all()
        self.log.debug(Messages.Get.retrieved_all("paper types", len(paper_types)))
        response = PaperTypeResponseSerializer(paper_types, many=True)
        
        return Response(
            data=response.data, 
            status=status.HTTP_200_OK
            )
    
    @extend_schema(
        operation_id="create_paper_type",
        tags=['Database Management'],
        summary="Create a New Paper Type",
        description="Adds a new paper type entry to the database. A successful creation returns the newly created paper type object with a 201 Created status code.",
        request=PaperTypeRequestSerializer,
        responses={
            status.HTTP_201_CREATED: standardized_response(
                PaperTypeResponseSerializer,
                name="PaperTypeCreated",
                description="The paper type was created successfully."
                ),
            status.HTTP_400_BAD_REQUEST: standardized_response(
                GenericResponseSerializer,
                name="PaperTypeCreateInvalidPayload",
                success=False,
                description="The request payload was invalid (e.g., missing a required field)."
                ),
            status.HTTP_403_FORBIDDEN: standardized_response(
                PaperTypeResponseSerializer,
                name="PaperTypeCreateForbidden",
                success=False,
                description="Permission denied."
            )
        }
    )
    def post(self, request:Request, *args, **kwargs) -> Response:
        """
        Handles POST requests to create a new paper type.

        Args:
            request: The incoming HTTP request containing the new paper type data.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            A Response object with the newly created paper type data and a 201 Created
            status if successful. Returns a 400 Bad Request if the provided
            data is invalid.
        """
        self.log.debug(Messages.Post.create_one("paper type", request.data))
        paper_type = PaperTypeRequestSerializer(data = request.data)
        
        if paper_type.is_valid():
            instance = paper_type.save()
            self.log.info(Messages.Post.created_one("paper type", instance.id))
            return Response(
                data=PaperTypeResponseSerializer(instance).data, 
                status=status.HTTP_201_CREATED
                )
        
        self.log.warning(Messages.Post.validation_failed("paper type", paper_type.errors))
        return Response(
            data=GenericResponseSerializer(GenericResponse(paper_type.errors)).data,
            status=status.HTTP_400_BAD_REQUEST
            )