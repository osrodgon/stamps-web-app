from sqlite3 import OperationalError

from django.db import connection
from common.api.messages import Messages
from common.api.serializers.generic_response import GenericResponse, GenericResponseSerializer
from common.log.logger import Logger
from common.core.schemas import standardized_response
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema

from health_api.api.serializers.health_response_serializer import HealthResponseSerializer

class HealthView(Logger, APIView):
    """
    API view to check and report the health of the system.

    This view provides an endpoint to monitor the status of critical
    components of the application, such as the database connection.
    It is designed to be used by automated monitoring services.
    """
    authentication_classes = []
    permission_classes = []
    
    @extend_schema(
        operation_id="list_system_health",
        tags=['Config Management'],
        summary="Show system health",
        description="Show system health",
        responses={
            200: standardized_response(
                HealthResponseSerializer,
                name="GetSystemHealthSuccess",
                many=True, 
                description="System health was successfully retrieved."
            ),
            503: standardized_response(
                GenericResponseSerializer,
                name="GetSystemHealthDBFailure",
                success=False,
                description="System health retrieved with errors."
            )
        }
    )
    def get(self, request:Request, *args, **kwargs) -> Response:
        """
        Handles GET requests to perform a system health check.

        Checks the database connectivity by executing a simple query.
        Constructs a response detailing the status of the backend and
        the database.

        Args:
            request: The incoming HTTP request.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            A Response object containing the health status.
            -   Returns HTTP 200 OK with health details, even if the database
                check fails, to provide a detailed status report.
            -   Returns HTTP 503 Service Unavailable if the response payload
                itself cannot be serialized, indicating a deeper application issue.
        """
        self.log.debug("Attempting to retrieve system health")
        db_status = Messages.Health.ok()
        backend_status = Messages.Health.running()
        response_status = 200
    
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
        except OperationalError:
            db_status = Messages.Health.error()
            response_status = 503
        except Exception as e:
            db_status = Messages.Health.error()
            backend_status = Messages.Health.error_with_message(type(e).__name__)
            response_status = 503
        
        data = {
            "status": Messages.Health.ok() if response_status == 200 else Messages.Health.error(),
            "database": db_status,
            "backend": backend_status
        }
        
        response = HealthResponseSerializer(data=data)
        
        if response.is_valid():
            self.log.debug("System health was successfully retrieved.")
            return Response(
                data=response.data, 
                status=status.HTTP_200_OK
            )
        
        self.log.warning(f"System health could not be retrieved. Error: {response.errors}")
        return Response(
            data=GenericResponseSerializer(GenericResponse(response.errors)).data,
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
        
