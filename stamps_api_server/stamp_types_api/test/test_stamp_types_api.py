
import os
from unittest.mock import patch
import pytest
from rest_framework import status

from common.test.api_client import api_client
from common.test.stamp_types_api_test_data import (
    stamp_types_table,
    stamp_type_post_payload_ok,
    stamp_type_put_payload_ok
)
from stamp_types_api.api.serializers.stamp_type_response_serializer import StampTypeResponseSerializer
from stamp_types_api.models import StampType


@pytest.mark.django_db
class TestStampTypesAPI:
    def test_get_all_stamp_types_returns_data_200_ok(self, api_client, stamp_types_table):
        response = api_client.get(self.__get_url())
        
        original = StampTypeResponseSerializer(stamp_types_table,many=True)
        
        assert len(response.json()['data']) == len(original.data)
        assert response.json()['data'] == original.data
        assert response.json()['success'] == True
        assert response.json()['message'] == "Retrieved successfully"
        assert response.json()['errors'] == None
        assert response.status_code == status.HTTP_200_OK
        
    def test_get_all_stamp_types_returns_no_data_200_ok(self, api_client):
        response = api_client.get(self.__get_url())
        
        assert len(response.json()['data']) == 0
        assert response.json()['success'] == True
        assert response.json()['message'] == "Retrieved successfully"
        assert response.json()['errors'] == None
        assert response.status_code == status.HTTP_200_OK
        
    def test_post_stamp_type_creates_record_201_created(self, api_client, stamp_type_post_payload_ok):
        response = api_client.post(self.__get_url(), stamp_type_post_payload_ok)
        
        assert response.json()['data']['name'] == stamp_type_post_payload_ok["name"]
        assert response.json()['success'] == True
        assert response.json()['message'] == "Created successfully" 
        assert response.json()['errors'] == None
        assert response.status_code == status.HTTP_201_CREATED
        
    def test_post_stamp_type_with_missing_name_returns_400_bad_request(self, api_client, stamp_type_post_payload_ok):
        del stamp_type_post_payload_ok["name"]
        response = api_client.post(self.__get_url(), stamp_type_post_payload_ok)
        
        assert response.json()['data'] == None
        assert response.json()['success'] == False
        assert response.json()['message'] == "Request failed"
        assert response.json()['errors']['information'] != None
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
    def test_post_stamp_type_with_invalid_field_returns_400_bad_request(self, api_client, stamp_type_post_payload_ok):
        stamp_type_post_payload_ok['new_field'] = 'new_value'
        response = api_client.post(self.__get_url(), stamp_type_post_payload_ok)
        
        assert response.json()['data'] == None
        assert response.json()['success'] == False
        assert response.json()['message'] == "Request failed"
        assert response.json()['errors']['information'] != None
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
    def test_get_stamp_type_returns_data_200_ok(self, api_client, stamp_types_table):
        response = api_client.get(self.__get_url() + "1")
        
        stamp_type = StampType.objects.get(pk=1)
        original = StampTypeResponseSerializer(stamp_type)
        
        assert response.json()['data']['name'] == original.data['name']
        assert response.json()['success'] == True
        assert response.json()['message'] == "Retrieved successfully"
        assert response.json()['errors'] == None
        assert response.status_code == status.HTTP_200_OK
    
    def test_get_stamp_type_returns_no_data_404_not_found(self, api_client):
        response = api_client.get(self.__get_url() + "1")
        
        assert response.json()['data'] == None
        assert response.json()['success'] == False
        assert response.json()['message'] == "Request failed"
        assert response.json()['errors']['information'] != None
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
    def test_put_stamp_type_updates_record_200_ok(self, api_client, stamp_types_table, stamp_type_put_payload_ok):
        response = api_client.put(self.__get_url() + "1", stamp_type_put_payload_ok)
        
        assert response.json()['data']['name'] == stamp_type_put_payload_ok["name"]
        assert response.json()['success'] == True
        assert response.json()['message'] == "Updated successfully"
        assert response.json()['errors'] == None
        assert response.status_code == status.HTTP_200_OK
        
    def test_put_stamp_type_updates_record_404_not_found(self, api_client, stamp_type_put_payload_ok):
        response = api_client.put(self.__get_url() + "1", stamp_type_put_payload_ok)
        
        assert response.json()['data'] == None
        assert response.json()['success'] == False
        assert response.json()['message'] == "Request failed"
        assert response.json()['errors']['information'] != None
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
    def test_put_stamp_type_updates_record_400_bad_request(self, api_client, stamp_types_table, stamp_type_put_payload_ok):
        stamp_type_put_payload_ok["new_field"] = "new_value"
        response = api_client.put(self.__get_url() + "1", stamp_type_put_payload_ok)
        
        assert response.json()['data'] == None
        assert response.json()['success'] == False
        assert response.json()['message'] == "Request failed"
        assert response.json()['errors']['information'] != None
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
    def test_delete_stamp_type_deletes_record_200_ok(self, api_client, stamp_types_table):
        response = api_client.delete(self.__get_url() + "1")
        
        assert response.json()['data']['information'] == "Successfully deleted StampType with id: 1"
        assert response.json()['success'] == True
        assert response.json()['message'] == "Deleted successfully"
        assert response.json()['errors'] == None
        assert response.status_code == status.HTTP_200_OK
        
    def test_delete_stamp_type_deletes_record_404_not_found(self, api_client):
        response = api_client.delete(self.__get_url() + "1")
        
        assert response.json()['data'] == None
        assert response.json()['success'] == False
        assert response.json()['message'] == "Request failed"
        assert response.json()['errors']['information'] != None
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
    @patch('stamp_types_api.api.views.stamp_types_by_id_view.StampType.objects.get')
    def test_delete_stamp_type_deletes_record_database_error(self, mock_get, api_client, stamp_types_table):
        mock_get.side_effect = Exception("Database connection lost")
        response = api_client.delete(self.__get_url() + "1")
        
        assert response.json()['data'] == None
        assert response.json()['success'] == False
        assert response.json()['message'] == "Request failed"
        assert response.json()['errors']['information'] != None
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
    def test_stamp_type_model_str_representation(self):
        test_name = "test_name"
        stamp_type = StampType.objects.create(
            name=test_name
        )
        
        assert str(stamp_type) == test_name

        
    def __get_url(self):
        return "/" + str(os.getenv("STAMP_TYPES_URL_V1"))
