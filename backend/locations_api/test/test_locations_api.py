import os
from unittest.mock import patch
import pytest
from rest_framework import status

from common.api.messages import Messages
from common.test.api_client import api_client
from common.test.locations_api_test_data import (
    locations_table,
    location_post_payload_ok,
    location_put_payload_ok
)
from locations_api.models import Location
from locations_api.api.serializers.location_response_serializer import LocationResponseSerializer


@pytest.mark.django_db
class TestLocationsAPI:
    def test_get_all_locations_returns_data_200_ok(self, api_client, locations_table):
        response = api_client.get(self.__get_url())

        original = LocationResponseSerializer(locations_table, many=True)

        assert len(response.json()['data']) == len(original.data)
        assert response.json()['data'] == original.data
        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.retrieved_successfully()
        assert response.json()['errors'] == None
        assert response.status_code == status.HTTP_200_OK

    def test_get_all_locations_returns_no_data_200_ok(self, api_client):
        response = api_client.get(self.__get_url())

        assert len(response.json()['data']) == 0
        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.retrieved_successfully()
        assert response.json()['errors'] == None
        assert response.status_code == status.HTTP_200_OK

    def test_post_location_creates_record_201_created(self, api_client, location_post_payload_ok):
        response = api_client.post(self.__get_url(), location_post_payload_ok)

        assert response.json()[
            'data']['name'] == location_post_payload_ok["name"]
        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.created_successfully()
        assert response.json()['errors'] == None
        assert response.status_code == status.HTTP_201_CREATED

    def test_post_location_with_missing_name_returns_400_bad_request(self, api_client, location_post_payload_ok):
        del location_post_payload_ok["name"]
        response = api_client.post(self.__get_url(), {})

        assert response.json()['data'] == None
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['errors'][0]['field'] == "name"
        assert response.json()['errors'][0]['message'] == Messages.field_required()
        assert response.json()['errors'][0]['code'] == Messages.Code.required()
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_post_location_with_invalid_field_returns_400_bad_request(self, api_client, location_post_payload_ok):
        location_post_payload_ok['new_field'] = 'new_value'
        response = api_client.post(self.__get_url(), location_post_payload_ok)

        assert response.json()['data'] == None
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['errors'][0]['field'] == "new_field"
        assert response.json()['errors'][0]['message'] == Messages.field_not_allowed()
        assert response.json()['errors'][0]['code'] == Messages.Code.invalid()
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_get_location_returns_data_200_ok(self, api_client, locations_table):
        response = api_client.get(self.__get_url() + "1")

        location = Location.objects.get(pk=1)
        original = LocationResponseSerializer(location)

        assert response.json()['data']['name'] == original.data['name']
        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.retrieved_successfully()
        assert response.json()['errors'] == None
        assert response.status_code == status.HTTP_200_OK

    def test_get_location_returns_no_data_404_not_found(self, api_client):
        response = api_client.get(self.__get_url() + "1")

        assert response.json()['data'] == None
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['errors'][0]['field'] == None
        assert response.json()['errors'][0]['message'] == Messages.Get.not_found("location", 1)
        assert response.json()['errors'][0]['code'] == Messages.Code.other()
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_put_location_updates_record_200_ok(self, api_client, locations_table, location_put_payload_ok):
        response = api_client.put(self.__get_url() + "1", location_put_payload_ok)

        assert response.json()['data']['name'] == location_put_payload_ok["name"]
        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.updated_successfully()
        assert response.json()['errors'] == None
        assert response.status_code == status.HTTP_200_OK

    def test_put_location_updates_record_404_not_found(self, api_client, location_put_payload_ok):
        response = api_client.put(self.__get_url() + "1", location_put_payload_ok)

        assert response.json()['data'] == None
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['errors'][0]['field'] == None
        assert response.json()['errors'][0]['message'] == Messages.Put.not_found("location", 1)
        assert response.json()['errors'][0]['code'] == Messages.Code.other()
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
    def test_put_location_updates_record_400_bad_request(self, api_client, locations_table, location_put_payload_ok):
        location_put_payload_ok["new_field"] = "new_value"
        response = api_client.put(self.__get_url() + "1", location_put_payload_ok)

        assert response.json()['data'] == None
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['errors'][0]['field'] == "new_field"
        assert response.json()['errors'][0]['message'] == Messages.field_not_allowed()
        assert response.json()['errors'][0]['code'] == Messages.Code.invalid()
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        

    def test_delete_location_deletes_record_200_ok(self, api_client, locations_table):
        response = api_client.delete(self.__get_url() + "1")
        
        assert response.json()['data']['message'] == Messages.Delete.deleted_one("location", 1)
        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.deleted_successfully()
        assert response.json()['errors'] == None
        assert response.status_code == status.HTTP_200_OK

    def test_delete_location_deletes_record_404_not_found(self, api_client):
        response = api_client.delete(self.__get_url() + "1")

        assert response.json()['data'] == None
        assert response.json()['success'] == False
        assert response.json()['errors'][0]['field'] == None
        assert response.json()['errors'][0]['message'] == Messages.Delete.not_found("location", 1)
        assert response.json()['errors'][0]['code'] == Messages.Code.other()
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
    @patch('locations_api.api.views.locations_by_id_view.Location.objects.get')
    def test_delete_location_deletes_record_database_error(self, mock_get, api_client, locations_table):
        mock_get.side_effect = Exception("Database connection lost")
        response = api_client.delete(self.__get_url() + "1")
        
        assert response.json()['data'] == None
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['errors'][0]['field'] == None
        assert response.json()['errors'][0]['message'] == Messages.server_error()
        assert response.json()['errors'][0]['code'] == Messages.Code.other()
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_location_model_str_representation(self):
        test_name = "test_location"
        location = Location.objects.create(name=test_name)

        assert str(location) == test_name

    def __get_url(self):
        return "/" + str(os.getenv("LOCATIONS_URL_V1"))
