from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema

from common.api.messages import Messages
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
    @extend_schema(
        operation_id="logoff_users",
        tags=['User Management'],
        summary="Logoff a user from the system",
        description="Logoff a user from the system.",
        request=LogoffRequestSerializer,
        responses={
            200: standardized_response(
                LogoffResponseSerializer, 
                name="LogoffSuccessful",
                description="The user was logged off successfully.",
                many=True
                ),
            401: standardized_response(
                LogoffResponseSerializer,
                name="LogoffUnauthorized",
                success=False,
                description="The user was not logged off. Token is invalid or already invalidated."
                ),
            403: standardized_response(
                LogoffResponseSerializer,
                name="LogoffForbidden",
                success=False,
                description="The user was not logged off. Permission denied."
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
                        Authorization header with a bearer JWT.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            A Response object with a success message and a 200 OK status if
            the logoff was successful. Returns a 401 Unauthorized status if
            the token is invalid or already invalidated.
        """
        token = request.headers.get('Authorization').split(' ')[1]
        token_data = JwtToken().validate(token)
        
        try:
            UserToken.objects.get(user=token_data['user_id'], jti=token_data['jti']).delete()
            return Response(status=status.HTTP_200_OK, data=Messages.Post.logoff())
        
        except UserToken.DoesNotExist:
            return Response(status=status.HTTP_401_UNAUTHORIZED, data=Messages.Auth.invalid_jwt())
        