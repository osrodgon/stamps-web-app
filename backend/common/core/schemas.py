# utils/schema.py
from email.policy import default
from rest_framework import serializers
from drf_spectacular.utils import inline_serializer, OpenApiResponse

class ItemList(serializers.Serializer):
    field = serializers.CharField()
    message = serializers.CharField()
    code = serializers.CharField()
    

def standardized_response(serializer_class, many=False, success = True, name=None, description=None):
    """
    Generates a standardized drf-spectacular response schema.

    This helper function creates an `OpenApiResponse` with a consistent
    wrapper around a given data serializer. The wrapper includes fields for
    success status, a message, the data payload, and potential errors.

    The structure of the 'data' and 'errors' fields adapts based on the
    'success' flag to correctly represent success and error responses.

    Args:
        serializer_class: The DRF serializer class for the main payload.
        many (bool): Set to True if the 'data' field should be an array
                     of serialized objects. Defaults to False.
        success (bool): Determines the schema type. True for success responses
                        (data is serialized), False for error responses
                        (errors are serialized). Defaults to True.
        name (str, optional): A custom name for the generated inline
                              serializer in the OpenAPI schema. If None, a
                              name is auto-generated. Defaults to None.
        description (str, optional): A description for the `OpenApiResponse`.
                                     Defaults to a generic message.

    Returns:
        OpenApiResponse: A drf-spectacular response object configured with
                         the standardized schema.
    """
    wrapper_name = name or f"{serializer_class.__name__}StandardResponse_{'List' if many else 'Single'}"
    if success:
        data_field = serializer_class(many=many)
        success_field = serializers.BooleanField(default=True)
        errors_field = serializers.CharField()
    else:
        data_field = serializers.CharField()
        success_field = serializers.BooleanField(default=False)
        errors_field = serializers.ListField(child=ItemList())
        

    response_serializer = inline_serializer(
        name=wrapper_name,
        fields={
            "success": success_field,
            "message": serializers.CharField(),
            "data": data_field,
            "errors": errors_field,
        },
    )

    return OpenApiResponse(
        response=response_serializer,
        description=description or "Standardized API response"
        )
