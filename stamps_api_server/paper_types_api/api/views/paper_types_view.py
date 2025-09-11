from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema

from common.api.serializers.generic_response import GenericResponseSerializer, GenericResponse
from common.log.logger import Logger
from common.core.schemas import standardized_response
from paper_types_api.models import PaperType
from paper_types_api.api.serializers.paper_type_response_serializer import PaperTypeResponseSerializer
from paper_types_api.api.serializers.paper_type_request_serializer import PaperTypeRequestSerializer


class PaperTypesView(Logger, APIView):
    serializer_class = PaperTypeResponseSerializer
    
    @extend_schema(
        operation_id="list_paper_types",
        tags=['Paper Types'],
        summary="List All Paper Types",
        description="Retrieves a list of all paper type entries currently stored in the database.",
        responses={
            200: standardized_response(
                PaperTypeResponseSerializer, 
                name="PaperTypesRetrieved",
                description="A list of paper types was successfully retrieved.",
                many=True
                )
        }
    )
    def get(self, request:Request, *args, **kwargs) -> Response:
        self.debug("Attempting to retrieve all paper types.")
        paper_types = PaperType.objects.all()
        self.debug(f"Found {len(paper_types)} paper type entries.")
        response = PaperTypeResponseSerializer(paper_types, many=True)
        
        return Response(
            data=response.data, 
            status=status.HTTP_200_OK
            )
    
    @extend_schema(
        operation_id="create_paper_type",
        tags=['Paper Types'],
        summary="Create a New Paper Type",
        description="Adds a new paper type entry to the database. A successful creation returns the newly created paper type object with a 201 Created status code.",
        request=PaperTypeRequestSerializer,
        responses={
            201: standardized_response(
                PaperTypeResponseSerializer,
                name="PaperTypeCreated",
                description="The paper type was created successfully."
                ),
            400: standardized_response(
                GenericResponseSerializer,
                name="PaperTypeCreateInvalidPayload",
                success=False,
                description="The request payload was invalid (e.g., missing a required field)."
                )
        }
    )
    def post(self, request:Request, *args, **kwargs) -> Response:
        self.debug(f"Attempting to create a new paper type with payload: {request.data}")
        paper_type = PaperTypeRequestSerializer(data = request.data)
        
        if paper_type.is_valid():
            instance = paper_type.save()
            self.info(f"Successfully created paper type with id: {instance.id}")
            return Response(
                data=PaperTypeResponseSerializer(instance).data, 
                status=status.HTTP_201_CREATED
                )
        
        self.warning(f"Payload validation failed for new paper type entry: {paper_type.errors}")
        return Response(
            data=GenericResponseSerializer(GenericResponse(paper_type.errors)).data,
            status=status.HTTP_400_BAD_REQUEST
            )