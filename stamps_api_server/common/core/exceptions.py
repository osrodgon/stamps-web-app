from rest_framework.views import exception_handler
from common.core.wrappers import standard_response

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        return standard_response(
            success=False,
            message="Request failed",
            data=None,
            errors=response.data,
            status=response.status_code,
        )

    # For unhandled exceptions
    return standard_response(
        success=False,
        message="Internal server error",
        data=None,
        errors=exc,
        status=500,
    )
