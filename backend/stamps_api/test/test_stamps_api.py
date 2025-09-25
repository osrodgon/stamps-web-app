import os
from unittest.mock import patch
import pytest
from rest_framework import status

from common.api.messages import Messages
from common.test.api_client import api_client
from common.test.stamps_api_test_data import (
    stamps_table,
    stamp_post_payload_ok,
    stamp_put_payload_ok
)
from common.test.year_api_test_data import years_table
from common.test.countries_api_test_data import countries_table
from common.test.stamp_types_api_test_data import stamp_types_table
from common.test.paper_types_api_test_data import paper_types_table
from common.test.locations_api_test_data import locations_table
from common.test.issues_api_test_data import issues_table
from common.test.colors_api_test_data import colors_table

from stamps_api.api.serializers.stamp_response_serializer import StampResponseSerializer
from stamps_api.models import Stamp


@pytest.mark.django_db
class TestStampsAPI:
    def test_get_all_stamps_returns_data_200_ok(self, api_client, stamps_table):
        response = api_client.get(self.__get_url())
        
        original = StampResponseSerializer(stamps_table, many=True)
        
        assert len(response.json()['data']) == len(original.data)
        assert response.json()['data'] == original.data
        assert response.json()['success'] is True
        assert response.json()['message'] == Messages.retrieved_successfully()
        assert response.json()['errors'] is None
        assert response.status_code == status.HTTP_200_OK
        
    def test_get_all_stamps_returns_no_data_200_ok(self, api_client):
        response = api_client.get(self.__get_url())
        
        assert len(response.json()['data']) == 0
        assert response.json()['success'] is True
        assert response.json()['message'] == Messages.retrieved_successfully()
        assert response.json()['errors'] is None
        assert response.status_code == status.HTTP_200_OK
        
    def test_post_stamp_creates_record_201_created(self, api_client, stamp_post_payload_ok):
        response = api_client.post(self.__get_url(), stamp_post_payload_ok, format='json')
        
        assert response.json()['data']['name'] == stamp_post_payload_ok["name"]
        assert response.json()['data']['edifil_code'] == stamp_post_payload_ok["edifil_code"]
        assert response.json()['success'] is True
        assert response.json()['message'] == Messages.created_successfully()
        assert response.json()['errors'] is None
        assert response.status_code == status.HTTP_201_CREATED
        
    def test_post_stamp_with_missing_name_returns_400_bad_request(self, api_client, stamp_post_payload_ok):
        del stamp_post_payload_ok["name"]
        response = api_client.post(self.__get_url(), stamp_post_payload_ok, format='json')
        
        assert response.json()['data'] is None
        assert response.json()['success'] is False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['errors'][0]['field'] == "name"
        assert response.json()['errors'][0]['message'] == Messages.field_required()
        assert response.json()['errors'][0]['code'] == Messages.Code.required()
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
    def test_post_stamp_with_invalid_field_returns_400_bad_request(self, api_client, stamp_post_payload_ok):
        stamp_post_payload_ok['new_field'] = 'new_value'
        response = api_client.post(self.__get_url(), stamp_post_payload_ok, format='json')
        
        assert response.json()['data'] is None
        assert response.json()['success'] is False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['errors'][0]['field'] == "new_field"
        assert response.json()['errors'][0]['message'] == Messages.field_not_allowed()
        assert response.json()['errors'][0]['code'] == Messages.Code.invalid()
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
    def test_get_stamp_returns_data_200_ok(self, api_client, stamps_table):
        stamp_id = stamps_table[0].id
        response = api_client.get(f"{self.__get_url()}{stamp_id}")
        
        stamp = Stamp.objects.get(pk=stamp_id)
        original = StampResponseSerializer(stamp)
        
        assert response.json()['data']['name'] == original.data['name']
        assert response.json()['success'] is True
        assert response.json()['message'] == Messages.retrieved_successfully()
        assert response.json()['errors'] is None
        assert response.status_code == status.HTTP_200_OK
    
    def test_get_stamp_returns_no_data_404_not_found(self, api_client):
        response = api_client.get(self.__get_url() + "999")
        
        assert response.json()['data'] is None
        assert response.json()['success'] is False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['errors'][0]['field'] is None
        assert response.json()['errors'][0]['message'] == Messages.Get.not_found("Stamp", 999)
        assert response.json()['errors'][0]['code'] == Messages.Code.other()
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
    def test_put_stamp_updates_record_200_ok(self, api_client, stamps_table, stamp_put_payload_ok):
        stamp_id = stamps_table[0].id
        response = api_client.put(f"{self.__get_url()}{stamp_id}", stamp_put_payload_ok, format='json')
        
        assert response.json()['data']['name'] == stamp_put_payload_ok["name"]
        assert response.json()['success'] is True
        assert response.json()['message'] == Messages.updated_successfully()
        assert response.json()['errors'] is None
        assert response.status_code == status.HTTP_200_OK
        
    def test_put_stamp_updates_record_404_not_found(self, api_client, stamp_put_payload_ok):
        response = api_client.put(self.__get_url() + "999", stamp_put_payload_ok, format='json')
        
        assert response.json()['data'] is None
        assert response.json()['success'] is False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['errors'][0]['field'] is None
        assert response.json()['errors'][0]['message'] == Messages.Put.not_found("Stamp", 999)
        assert response.json()['errors'][0]['code'] == Messages.Code.other()
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    # TODO Pending    
    # def test_put_stamp_updates_record_400_bad_request(self, api_client, stamps_table, stamp_put_payload_ok):
    #     stamp_put_payload_ok["new_field"] = "new_value"
    #     response = api_client.put(self.__get_url() + "1", stamp_put_payload_ok)
        
    #     assert response.json()['data'] == None
    #     assert response.json()['success'] == False
    #     assert response.json()['message'] == Messages.failed()
    #     assert response.json()['errors'][0]['field'] == "new_field"
    #     assert response.json()['errors'][0]['message'] == Messages.field_not_allowed()
    #     assert response.json()['errors'][0]['code'] == Messages.Code.invalid()
    #     assert response.status_code == status.HTTP_400_BAD_REQUEST
        
    def test_delete_stamp_deletes_record_200_ok(self, api_client, stamps_table):
        stamp_id = stamps_table[0].id
        response = api_client.delete(f"{self.__get_url()}{stamp_id}")
        
        assert response.json()['data']['message'] == Messages.Delete.deleted_one("Stamp", stamp_id)
        assert response.json()['success'] is True
        assert response.json()['message'] == Messages.deleted_successfully()
        assert response.json()['errors'] is None
        assert response.status_code == status.HTTP_200_OK
        
    def test_delete_stamp_deletes_record_404_not_found(self, api_client):
        response = api_client.delete(self.__get_url() + "999")
        
        assert response.json()['data'] is None
        assert response.json()['success'] is False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['errors'][0]['field'] is None
        assert response.json()['errors'][0]['message'] == Messages.Delete.not_found("Stamp", 999)
        assert response.json()['errors'][0]['code'] == Messages.Code.other()
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
    @patch('stamps_api.api.views.stamps_by_id_view.Stamp.objects.get')
    def test_delete_stamp_deletes_record_database_error(self, mock_get, api_client, stamps_table):
        stamp_id = stamps_table[0].id
        mock_get.side_effect = Exception("Database connection lost")
        response = api_client.delete(f"{self.__get_url()}{stamp_id}")
        
        assert response.json()['data'] is None
        assert response.json()['success'] is False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['errors'][0]['field'] is None
        assert response.json()['errors'][0]['message'] == Messages.server_error()
        assert response.json()['errors'][0]['code'] == Messages.Code.other()
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        
    def __get_url(self):
        return "/" + str(os.getenv("STAMPS_URL_V1"))