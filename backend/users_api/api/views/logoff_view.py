from email import message
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema

from common.api.messages import Messages
from common.api.serializers.generic_response import GenericResponse, GenericResponseSerializer
from common.core.jwt_token import JwtToken
from common.core.schemas import standardized_response
from common.log.logger import Logger
from users_api.api.serializers.logoff_request_serializer import LogoffRequestSerializer
from users_api.api.serializers.logoff_response_serializer import LogoffResponseSerializer
from users_api.models import UserToken


class LogoffView(Logger, APIView):
    """
    API view for handling user logoff.

    This view provides an endpoint for users to log off from the system.
    Logging off invalidates the user's current JSON Web Token (JWT) by
    deleting the associated token record from the database, preventing
    its further use for authentication.
    """
    authentication_classes = []
    permission_classes = []
    
    @extend_schema(
        operation_id="logoff_users",
        tags=['User Management'],
        summary="Logoff a user from the system",
        description="Logoff a user from the system. A valid Authoriztion header must be provided.",
        request=LogoffRequestSerializer,
        responses={
            200: standardized_response(
                LogoffResponseSerializer, 
                name="LogoffSuccessful",
                description="The user was logged off successfully.",
                many=True
                ),
            400: standardized_response(
                LogoffResponseSerializer,
                name="LogoffBadRequest",
                success=False,
                description="The user was not logged off. Header missing or invalid format."
                ),
            401: standardized_response(
                LogoffResponseSerializer,
                name="LogoffUnauthorized",
                success=False,
                description="The user was not logged off. Token is invalid or already invalidated or user does not exist."
                ),
            500: standardized_response(
                LogoffResponseSerializer,
                name="LogoffInternalServerError",
                success=False,
                description="The user was not logged off. An error occurred while logging off."
                )
        }
    )
    def post(self, request:Request, *args, **kwargs) -> Response:
        """
        Handles POST requests to log a user off.

        This method extracts the JWT from the Authorization header, validates it,
        and then deletes the corresponding UserToken from the database to
        invalidate the session.

        Args:
            request:    The incoming HTTP request, which should contain the
                        Authorization header with a jwt Token.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            A Response object with a success message and a 200 OK status if
            the logoff was successful. Returns a 401 Unauthorized status if
            the token is invalid or already invalidated.
        """
        self.log.debug("Logging off...")
        
        header = request.headers.get('Authorization')
        if header is None:
            message = Messages.Auth.header_missing()
            self.log.debug(message)
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data=GenericResponseSerializer(GenericResponse(message)).data
            )
        
        try: 
            jwt, token = header.split(' ')
            if jwt.lower() != "jwt":
                message = Messages.Auth.not_supported()
                self.log.debug(message)
                return Response(
                    status=status.HTTP_400_BAD_REQUEST,
                    data=GenericResponseSerializer(GenericResponse(message)).data
                )
        except Exception as e:
            message = Messages.Auth.invalid_format()
            self.log.debug(message)
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data=GenericResponseSerializer(GenericResponse(message)).data
            )
        
        token_data = JwtToken().validate(token)
        
        if token_data is None:
            message = Messages.Auth.invalid_jwt()
            self.log.debug(message)
            return Response(
                status=status.HTTP_401_UNAUTHORIZED, 
                data=GenericResponseSerializer(GenericResponse(message)).data
            )
        
        try:
            user_token = UserToken.objects.get(user=token_data['user_id'], jti=token_data['jti'])
            user_token.delete()
            self.log.debug("User logged off.")
            return Response(
                status=status.HTTP_200_OK, 
                data=Messages.Post.logoff()
            )
        
        except UserToken.DoesNotExist:
            message = Messages.Auth.user_not_found()
            self.log.debug(message)
            return Response(
                status=status.HTTP_401_UNAUTHORIZED, 
                data=GenericResponseSerializer(GenericResponse(message)).data
            )
        