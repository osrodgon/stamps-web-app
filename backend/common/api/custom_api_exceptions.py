from rest_framework.exceptions import APIException
from rest_framework import status

from common.api.messages import Messages

class DatabaseConnectionLost(APIException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    _default_detail = Messages.Database.connection_lost()
    default_code = Messages.Code.connection_lost()