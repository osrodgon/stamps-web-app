import stat
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from common.api.messages import Messages
from common.api.serializers.generic_response import GenericResponseSerializer, GenericResponse
from common.log.logger import Logger
from common.core.schemas import standardized_response
from stamps_api.models import Stamp
from stamps_api.api.serializers.stamp_response_serializer import StampResponseSerializer
from stamps_api.api.serializers.stamp_request_serializer import StampRequestSerializer


class StampsView(Logger, APIView):
    """
    API view for handling collections of Stamp instances.

    This view provides GET (list) and POST (create) operations for stamps.
    """
    serializer_class = StampResponseSerializer
    
    @extend_schema(
        operation_id="list_stamps",
        tags=['Database Management'],
        summary="List All Stamps",
        description="Retrieves a list of all stamp entries currently stored in the database.",
        parameters=[
        OpenApiParameter(
                name='issue_id', 
                type=OpenApiTypes.INT, 
                location=OpenApiParameter.QUERY, 
                description='Filter stamps by issue_id',
                required=False
        )
        ],
        responses={
            status.HTTP_200_OK: standardized_response(
                StampResponseSerializer, 
                name="StampsRetrieved",
                description="A list of stamps was successfully retrieved.",
                many=True
                ),
            status.HTTP_403_FORBIDDEN: standardized_response(
                StampResponseSerializer,
                name="StampsListPermissionDenied",
                success=False,
                description="Permission denied."
            )
        }
    )
    def get(self, request:Request, *args, **kwargs) -> Response:
        """
        Handles GET requests to retrieve a list of all stamps.

        Args:
            request: The incoming HTTP request.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            A Response object containing a list of all serialized stamps
            with a 200 OK status.
        """
        self.log.debug(Messages.Get.retrieve_all("stamps"))
        issue_id = request.query_params.get('issue_id', None)
        
        stamps = Stamp.objects.all().order_by('edifil_code')
        if issue_id:
            try:
                issue_id_int = int(issue_id)
                self.log.debug(F"Filtering stamps by issue id {issue_id_int}")
                stamps = stamps.filter(issue__id=issue_id_int)
            except ValueError:
                self.log.warning(f"Invalid value for 'issue_id' filter provided: {issue_id}")
                stamps = stamps.none()
        
        self.log.debug(Messages.Get.retrieved_all("stamps", len(stamps)))
        response = StampResponseSerializer(stamps, many=True)
        
        return Response(
            data=response.data, 
            status=status.HTTP_200_OK
            )
    
    @extend_schema(
        operation_id="create_stamp",
        tags=['Database Management'],
        summary="Create a New Stamp",
        description="Adds a new stamp entry to the database. A successful creation returns the newly created stamp object with a 201 Created status code.",
        request=StampRequestSerializer,
        responses={
            status.HTTP_201_CREATED: standardized_response(
                StampResponseSerializer,
                name="StampCreated",
                description="The stamp was created successfully."
                ),
            status.HTTP_400_BAD_REQUEST: standardized_response(
                GenericResponseSerializer,
                name="StampCreateInvalidPayload",
                success=False,
                description="The request payload was invalid (e.g., missing a required field)."
                ),
            status.HTTP_403_FORBIDDEN: standardized_response(
                StampResponseSerializer,
                name="StampCreatePermissionDenied",
                success=False,
                description="Permission denied."
            )
        }
    )
    def post(self, request:Request, *args, **kwargs) -> Response:
        """
        Handles POST requests to create a new stamp.

        Args:
            request: The incoming HTTP request containing the new stamp data.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            A Response object with the newly created stamp data and a 201 Created
            status if successful. Returns a 400 Bad Request if the provided
            data is invalid.
        """
        self.log.debug(Messages.Post.create_one("stamp", request.data))
        stamp = StampRequestSerializer(data = request.data)
        
        if stamp.is_valid():
            instance = stamp.save()
            self.log.info(Messages.Post.created_one("stamp", instance.id))
            return Response(
                data=StampResponseSerializer(instance).data, 
                status=status.HTTP_201_CREATED
                )
        
        self.log.warning(Messages.Post.validation_failed("stamp", stamp.errors))
        return Response(
            data=GenericResponseSerializer(GenericResponse(stamp.errors)).data,
            status=status.HTTP_400_BAD_REQUEST
            )