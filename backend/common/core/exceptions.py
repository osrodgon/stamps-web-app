from math import e
from rest_framework.views import exception_handler
from rest_framework import status
from common.core.wrappers import standard_response
from common.api.messages import Messages

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        return standard_response(
            success=False,
            message=Messages.failed(),
            data=None,
            errors=response.data,
            status=response.status_code,
        )

    # For unhandled exceptions
    if exc.args[0] == status.HTTP_400_BAD_REQUEST:
        return standard_response(
            success=False,
            message=exc.args[1],
            data=None,
            errors=None,
            status=status.HTTP_400_BAD_REQUEST
            
        )
        
    return standard_response(
        success=False,
        message=Messages.server_error(),
        data=None,
        errors=exc,
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
