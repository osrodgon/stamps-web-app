from rest_framework import serializers

class LogoffRequestSerializer(serializers.Serializer):
    """
    Serializer for handling user logoff requests.

    This serializer is typically empty as logoff usually only requires
    an authentication token in the header, but can be extended if
    the logoff process requires additional data in the request body.
    """
    # No fields are typically required for a logoff request in the body.
    pass