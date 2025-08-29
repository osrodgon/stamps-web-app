# utils/schema.py
from email.policy import default
from math import e
from rest_framework import serializers
from drf_spectacular.utils import inline_serializer, OpenApiResponse

def standardized_response(serializer_class, many=False, success = True, name=None, description=None):
    wrapper_name = name or f"{serializer_class.__name__}StandardResponse_{'List' if many else 'Single'}"
    if success:
        data_field = serializer_class(many=many)
        success_field = serializers.BooleanField(default=True)
        errors_field = serializers.JSONField(required=False, allow_null=True)
    else:
        data_field = serializers.JSONField(required=False, allow_null=True)
        success_field = serializers.BooleanField(default=False)
        errors_field = serializer_class()
        

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
