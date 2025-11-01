import pytest
from rest_framework import status
from sqlite3 import OperationalError

from _backend.settings import HEALTH_ENDPOINT, SERVER_URL_V1
from common.api.messages import Messages
from common.test.api_client import api_client
from common.test.abstract_api_unit_test import AbstractApiUnitTest
from health_api.api.serializers.health_response_serializer import HealthResponseSerializer

@pytest.mark.django_db
class TestHealthAPI(AbstractApiUnitTest):

    def test_get_health_returns_200_ok(self, api_client):
        response = api_client.get(self.__get_url())

        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.retrieved_successfully()
        assert response.json()['errors'] == None
        assert response.json()['data']['status'] == Messages.Health.ok()
        assert response.json()['data']['database'] == Messages.Health.ok()
        assert response.json()['data']['backend'] == Messages.Health.running()
        assert response.status_code == status.HTTP_200_OK


    def test_get_health_returns_200_ok_database_operational_error(self, api_client):
        self.cursor_error(OperationalError)
        response = api_client.get(self.__get_url())

        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.retrieved_successfully()
        assert response.json()['errors'] == None
        assert response.json()['data']['status'] == Messages.Health.error()
        assert response.json()['data']['database'] == Messages.Health.error()
        assert response.json()['data']['backend'] == Messages.Health.running()
        assert response.status_code == status.HTTP_200_OK

    def test_get_health_returns_200_ok_database_generic_error(self, api_client):
        self.cursor_error(Exception)
        response = api_client.get(self.__get_url())

        
        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.retrieved_successfully()
        assert response.json()['errors'] == None
        assert response.json()['data']['status'] == Messages.Health.error()
        assert response.json()['data']['database'] == Messages.Health.error()
        assert response.json()['data']['backend'] == Messages.Health.error_with_message("Exception")
        assert response.status_code == status.HTTP_200_OK

    def test_get_health_returns_503_serializer_invalid(self, api_client):
        self.create_serializer_object(
            "health_api.api.views.health_view.HealthResponseSerializer",
            HealthResponseSerializer, 
            None
        )
        response = api_client.get(self.__get_url())

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

    def __get_url(self):
        return f"/{SERVER_URL_V1}{HEALTH_ENDPOINT}"