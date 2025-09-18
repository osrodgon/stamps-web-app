from rest_framework.views import exception_handler
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
    return standard_response(
        success=False,
        message=Messages.server_error(),
        data=None,
        errors=exc,
        status=500,
    )
