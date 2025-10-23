from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema
from django.contrib.auth.hashers import make_password

from common.api.messages import Messages
from common.api.serializers.generic_response import GenericResponseSerializer, GenericResponse
from common.log.logger import Logger
from common.core.schemas import standardized_response
from users_api.models import UserCollection
from users_api.api.serializers.user_response_serializer import UserResponseSerializer
from users_api.api.serializers.user_request_serializer import UserRequestSerializer

class UsersView(Logger, APIView):
    serializer_class = UserResponseSerializer
    
    @extend_schema(
        operation_id="list_users",
        tags=['Collection Users'],
        summary="List All Collection Users",
        description="Retrieves a list of all collection user entries currently stored in the database.",
        responses={
            200: standardized_response(
                UserResponseSerializer, 
                name="UsersRetrieved",
                description="A list of collection users was successfully retrieved.",
                many=True
                ),
            403: standardized_response(
                UserResponseSerializer,
                name="UsersForbidden",
                success=False,
                description="Permission denied. You're likely missing X-API-Key header."
                )   
        }
    )
    def get(self, request:Request, *args, **kwargs) -> Response:
        self.debug(Messages.Get.retrieve_all("collection users"))
        users = UserCollection.objects.all()
        self.debug(Messages.Get.retrieved_all("collection users", users.count()))
        response = UserResponseSerializer(users, many=True)
        
        return Response(
            data=response.data, 
            status=status.HTTP_200_OK
            )
    
    @extend_schema(
        operation_id="create_user",
        tags=['Collection Users'],
        summary="Create a New Collection User",
        description="Adds a new collection user entry to the database. A successful creation returns the newly created user object with a 201 Created status code.",
        request=UserRequestSerializer,
        responses={
            status.HTTP_201_CREATED: standardized_response(
                UserResponseSerializer,
                name="UserCreated",
                description="The collection user was created successfully."
                ),
            status.HTTP_400_BAD_REQUEST: standardized_response(
                GenericResponseSerializer,
                name="UserCreateInvalidPayload",
                success=False,
                description="The request payload was invalid (e.g., missing a required field)."
                ),
            status.HTTP_403_FORBIDDEN: standardized_response(
                UserResponseSerializer,
                name="UserCreateForbidden",
                success=False,
                description="Permission denied. You're likely missing X-API-Key header."
                )   
        }
    )
    def post(self, request:Request, *args, **kwargs) -> Response:
        self.debug(Messages.Post.create_one("collection user", request.data))
        serializer = UserRequestSerializer(data=request.data)
        if serializer.is_valid():
            validated_data = serializer.validated_data
            validated_data['password_hash'] = make_password(validated_data.pop('password'))
            instance = UserCollection.objects.create(**validated_data)
            self.info(Messages.Post.created_one("collection user", instance.id))
            return Response(data=UserResponseSerializer(instance).data, status=status.HTTP_201_CREATED)
        
        self.warning(Messages.Post.validation_failed("collection user", serializer.errors))
        return Response(data=GenericResponseSerializer(GenericResponse(serializer.errors)).data, status=status.HTTP_400_BAD_REQUEST)