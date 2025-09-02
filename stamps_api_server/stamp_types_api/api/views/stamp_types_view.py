from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema

from common.api.serializers.generic_response import GenericResponseSerializer, GenericResponse
from common.log.logger import Logger
from common.core.schemas import standardized_response
from stamp_types_api.api.serializers.stamp_types_request_serializer import StampTypesResponseSerializer
from stamp_types_api.api.serializers.stamp_types_response_serializer import StampTypesResponseSerializer

class StampTypesView(Logger, APIView):
    pass