import datetime
from math import e
import re
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema
from django.contrib.auth.hashers import make_password, check_password
from datetime import datetime, timedelta, timezone
import jwt

from _backend.settings import JWT_ALGORITHM, JWT_SECRET
from common.api.messages import Messages
from common.api.serializers.generic_response import GenericResponse, GenericResponseSerializer
from common.log.logger import Logger
from users_api.models import UserCollection


class LoginView(Logger, APIView):
    authentication_classes = []
    permission_classes = []
    
    def __get_user(self, username: str, password: str) -> UserCollection:
        self.debug("Getting user...")
        try:
            self.debug("Querying database for user...")
            user = UserCollection.objects.get(username=username)
        except UserCollection.DoesNotExist:
            self.debug("User not found")
            return None
        
        if check_password(password, user.password_hash):
            self.debug("User found and validated.")
            return user
        
        self.debug("User validation failed")
        return None
    
    def post(self, request:Request, *args, **kwargs) -> Response:
        self.debug("Logging in...")
        user = self.__get_user(request.data['username'], request.data['password'])
        
        if user is None:
            self.debug("User not found")
            message = Messages.Post.login_failed()
            self.warning(message)
            return Response(
                data=GenericResponseSerializer(GenericResponse(message)).data,
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        current_time_utc = datetime.now(timezone.utc)
        
        jtw_payload = {
            'user_id': user.id,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'exp': current_time_utc + timedelta(days=1),
            'iat': current_time_utc
        }
        
        token = jwt.encode(
            jtw_payload,
            JWT_SECRET,
            algorithm=JWT_ALGORITHM
        )
        
        data = {
            'token': token,
            'payload': jtw_payload,
        }
        
        
        return Response(status=status.HTTP_200_OK, data=data)