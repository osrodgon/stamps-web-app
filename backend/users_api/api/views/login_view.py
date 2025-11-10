import datetime
import token
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema
from django.contrib.auth.hashers import check_password

from common.api.messages import Messages
from common.api.serializers.generic_response import GenericResponse, GenericResponseSerializer
from common.core.schemas import standardized_response
from common.log.logger import Logger
from common.core.jwt_token import JwtToken
from users_api.api.serializers.login_request_serializer import LoginRequestSerializer
from users_api.api.serializers.login_response_serializer import LoginResponseSerializer
from users_api.models import UserCollection

class LoginView(Logger, APIView):
    """
    API view for handling user authentication and login.

    This view provides a public endpoint (`/login`) for users to authenticate
    by submitting their credentials (username and password). Upon successful
    authentication, it generates and returns a JWT (JSON Web Token).
    """
    authentication_classes = []
    permission_classes = []
    
    def __get_user(self, username: str, password: str) -> UserCollection:
        """
        Retrieves and validates a user from the database.

        Args:
            username: The username of the user to retrieve.
            password: The password to validate against the stored hash.

        Returns:
            The UserCollection instance if the user exists and the password is
            correct, otherwise None.
        """
        try: 
            self.debug("Querying database for user...")
            user = UserCollection.objects.get(username=username)
        except UserCollection.DoesNotExist: ## Check this
            self.debug("User not found")
            return None
        
        if check_password(password, user.password_hash): ## Check this
            self.debug("User found and validated.")
            return user
        
        self.debug("User validation failed")
        return None
    
    @extend_schema(
        operation_id="login_users",
        tags=['User Management'],
        summary="Logs a user into the system",
        description="Returns token information to be used in future requests.",
        request=LoginRequestSerializer,
        responses={
            200: standardized_response(
                LoginResponseSerializer, 
                name="LoginSuccessful",
                description="The user was logged in successfully.",
                many=True
                ),
            400: standardized_response(
                LoginResponseSerializer,
                name="LoginForbiddenBadRequest",
                success=False,
                description="The payload is not valid."
                ),
            401: standardized_response(
                LoginResponseSerializer,
                name="LoginForbidden",
                success=False,
                description="The user was not logged in."
                ),
            500: standardized_response(
                LoginResponseSerializer,
                name="LoginFailed",
                success=False,
                description="The user was not logged in. An error occurred while logging in."
                )
        }
    )
    def post(self, request:Request, *args, **kwargs) -> Response:
        """
        Handles POST requests to authenticate a user and provide a JWT.

        Args:
            request: The incoming HTTP request containing 'username' and 'password'.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            A Response object with a JWT and a 200 OK status on successful login.
            Returns a 401 Unauthorized status if credentials are invalid.
            Returns a 500 Internal Server Error if token creation fails.
        """
        self.debug("Logging in...")
        
        serializer = LoginRequestSerializer(data=request.data)
        if serializer.is_valid():
            user = self.__get_user(request.data['username'], request.data['password'])
        
            if user is None:
                self.debug("User not found")
                message = Messages.Post.login_failed()
                self.warning(message)
                return Response(
                    data=GenericResponseSerializer(GenericResponse(message)).data,
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            token_data = JwtToken().create(user)
            if token_data is None:
                self.debug("JWT token creation failed")
                message = Messages.Post.login_failed()
                return Response(
                    status=status.HTTP_401_UNAUTHORIZED,
                    data=GenericResponseSerializer(GenericResponse(message)).data
                )
            
            self.debug("User logged in.")
            return Response(
                status=status.HTTP_200_OK, 
                data=token_data
            )
        else:
            self.debug("Invalid payload")
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data = GenericResponseSerializer(GenericResponse(serializer.errors)).data
            )