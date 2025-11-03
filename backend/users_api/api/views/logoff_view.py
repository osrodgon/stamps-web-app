from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema

from common.log.logger import Logger


class LogoffView(Logger, APIView):
    authentication_classes = []
    permission_classes = []
    
    def post(self, request:Request, *args, **kwargs) -> Response:
        return Response(status=status.HTTP_200_OK)