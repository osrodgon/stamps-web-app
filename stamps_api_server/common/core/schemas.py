# utils/schema.py
from email.policy import default
from rest_framework import serializers
from drf_spectacular.utils import inline_serializer, OpenApiResponse

def standardized_response(serializer_class, many=False, name=None, description=None):
    if serializer_class:
        wrapper_name = name or f"{serializer_class.__name__}StandardResponse_{'List' if many else 'Single'}"
        data_field = serializer_class(many=many)
        success = serializers.BooleanField()
    else:
        wrapper_name = name or "StandardResponse_NoData"
        data_field = serializers.JSONField(required=False, allow_null=True)
        success = serializers.BooleanField(default=False)
        

    response_serializer = inline_serializer(
        name=wrapper_name,
        fields={
            "success": success,
            "message": serializers.CharField(),
            "data": data_field,
            "errors": serializers.JSONField(required=False, allow_null=True),
        },
    )

    return OpenApiResponse(
        response=response_serializer,
        description=description or "Standardized API response"
        )
