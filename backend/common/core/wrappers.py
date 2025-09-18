from rest_framework.response import Response

def standard_response(success=True, message=None, data=None, errors=None, status=200):
    return Response(
        {
            "success": success,
            "message": message,
            "data": data,
            "errors": errors,
        },
        status=status,
    )
