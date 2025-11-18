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
    """
    API view for handling collections of UserCollection instances.

    This view provides GET (list) and POST (create) operations for users.
    """
    serializer_class = UserResponseSerializer
    
    @extend_schema(
        operation_id="list_users",
        tags=['User Management'],
        summary="List All Users",
        description="Retrieves a list of all user entries currently stored in the database.",
        responses={
            200: standardized_response(
                UserResponseSerializer, 
                name="UsersRetrieved",
                description="A list of users was successfully retrieved.",
                many=True
                ),
            403: standardized_response(
                UserResponseSerializer,
                name="UsersForbidden",
                success=False,
                description="Permission denied."
                )   
        }
    )
    def get(self, request:Request, *args, **kwargs) -> Response:
        """
        Handles GET requests to retrieve a list of all users.

        Args:
            request: The incoming HTTP request.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            A Response object containing a list of all serialized users
            with a 200 OK status.
        """
        self.log.debug(Messages.Get.retrieve_all("collection users"))
        users = UserCollection.objects.all()
        self.log.debug(Messages.Get.retrieved_all("collection users", users.count()))
        response = UserResponseSerializer(users, many=True)
        
        return Response(
            data=response.data, 
            status=status.HTTP_200_OK
            )
    
    @extend_schema(
        operation_id="create_user",
        tags=['User Management'],
        summary="Create a New User",
        description="Adds a new user entry to the database. A successful creation returns the newly created user object with a 201 Created status code.",
        request=UserRequestSerializer,
        responses={
            status.HTTP_201_CREATED: standardized_response(
                UserResponseSerializer,
                name="UserCreated",
                description="The user was created successfully."
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
                description="Permission denied."
                )   
        }
    )
    def post(self, request:Request, *args, **kwargs) -> Response:
        """
        Handles POST requests to create a new user.

        The user's password is automatically hashed before saving.

        Args:
            request: The incoming HTTP request containing the new user data.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            A Response object with the newly created user data and a 201 Created
            status if successful. Returns a 400 Bad Request if the provided data is invalid.
        """
        self.log.debug(Messages.Post.create_one("collection user", request.data))
        serializer = UserRequestSerializer(data=request.data)
        if serializer.is_valid():
            validated_data = serializer.validated_data
            validated_data['password_hash'] = make_password(validated_data.pop('password'))
            instance = UserCollection.objects.create(**validated_data)
            self.log.info(Messages.Post.created_one("collection user", instance.id))
            return Response(
                data=UserResponseSerializer(instance).data, 
                status=status.HTTP_201_CREATED
            )
        
        self.log.warning(Messages.Post.validation_failed("collection user", serializer.errors))
        return Response(
            data=GenericResponseSerializer(GenericResponse(serializer.errors)).data, 
            status=status.HTTP_400_BAD_REQUEST
        )