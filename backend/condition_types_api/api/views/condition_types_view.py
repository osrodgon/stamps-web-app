from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema

from common.api.messages import Messages
from common.api.serializers.generic_response import GenericResponseSerializer, GenericResponse
from common.log.logger import Logger
from common.core.schemas import standardized_response
from condition_types_api.models import ConditionType
from condition_types_api.api.serializers.condition_type_response_serializer import ConditionTypeResponseSerializer
from condition_types_api.api.serializers.condition_type_request_serializer import ConditionTypeRequestSerializer

class ConditionTypesView(Logger, APIView):
    serializer_class = ConditionTypeResponseSerializer
    
    @extend_schema(
        operation_id="list_condition_types",
        tags=['Collection Management'],
        summary="List All Condition Types",
        description="Retrieves a list of all condition type entries currently stored in the database.",
        responses={
            200: standardized_response(
                ConditionTypeResponseSerializer, 
                name="ConditionTypesRetrieved",
                description="A list of condition types was successfully retrieved.",
                many=True
                ),
            403: standardized_response(
                ConditionTypeResponseSerializer,
                name="ConditionTypesForbidden",
                success=False,
                description="Permission denied."
                )   
        }
    )
    def get(self, request:Request, *args, **kwargs) -> Response:
        self.debug(Messages.Get.retrieve_all("condition types"))
        condition_types = ConditionType.objects.all()
        self.debug(Messages.Get.retrieved_all("condition types", condition_types.count()))
        response = ConditionTypeResponseSerializer(condition_types, many=True)
        
        return Response(
            data=response.data, 
            status=status.HTTP_200_OK
            )
    
    @extend_schema(
        operation_id="create_condition_type",
        tags=['Collection Management'],
        summary="Create a New Condition Type",
        description="Adds a new condition type entry to the database. A successful creation returns the newly created condition type object with a 201 Created status code.",
        request=ConditionTypeRequestSerializer,
        responses={
            status.HTTP_201_CREATED: standardized_response(
                ConditionTypeResponseSerializer,
                name="ConditionTypeCreated",
                description="The condition type was created successfully."
                ),
            status.HTTP_400_BAD_REQUEST: standardized_response(
                GenericResponseSerializer,
                name="ConditionTypeCreateInvalidPayload",
                success=False,
                description="The request payload was invalid (e.g., missing a required field)."
                ),
            status.HTTP_403_FORBIDDEN: standardized_response(
                ConditionTypeResponseSerializer,
                name="ConditionTypeCreateForbidden",
                success=False,
                description="Permission denied."
                )   
        }
    )
    def post(self, request:Request, *args, **kwargs) -> Response:
        self.debug(Messages.Post.create_one("condition type", request.data))
        condition_type = ConditionTypeRequestSerializer(data = request.data)
        
        if condition_type.is_valid():
            instance = condition_type.save()
            self.info(Messages.Post.created_one("condition type", instance.id))
            return Response(
                data=ConditionTypeResponseSerializer(instance).data, 
                status=status.HTTP_201_CREATED
                )
        
        self.warning(Messages.Post.validation_failed("condition type", condition_type.errors))
        return Response(
            data=GenericResponseSerializer(GenericResponse(condition_type.errors)).data,
            status=status.HTTP_400_BAD_REQUEST
            )