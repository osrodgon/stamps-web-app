import os
from unittest.mock import patch
import pytest
from rest_framework import status

from common.api.messages import Messages
from common.test.api_client import api_client
from common.test.config_api_test_data import (
    config_table,
    config_post_payload_ok,
    config_put_payload_ok
)
from config_api.api.serializers.config_response_serializer import ConfigResponseSerializer
from config_api.models import Config


@pytest.mark.django_db
class TestConfigAPI:
    def test_get_all_config_returns_data_200_ok(self, api_client, config_table):
        response = api_client.get(self.get_url())
        
        original = ConfigResponseSerializer(config_table,many=True)
        
        assert len(response.json()['data']) == len(original.data)
        assert response.json()['data'] == original.data
        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.retrieved_successfully()
        assert response.json()['errors'] == None
        assert response.status_code == status.HTTP_200_OK
        
    def test_get_all_config_returns_no_data_200_ok(self, api_client):
        response = api_client.get(self.get_url())
        
        assert len(response.json()['data']) == 0
        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.retrieved_successfully()
        assert response.json()['errors'] == None
        assert response.status_code == status.HTTP_200_OK
        
    def test_post_config_creates_record_201_created(self, api_client, config_post_payload_ok):
        response = api_client.post(self.get_url(), config_post_payload_ok)
        
        assert response.json()['data']['property'] == config_post_payload_ok["property"]
        assert response.json()['data']['value'] == config_post_payload_ok["value"]
        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.created_successfully() 
        assert response.json()['errors'] == None
        assert response.status_code == status.HTTP_201_CREATED
        
    def test_post_config_with_missing_property_returns_400_bad_request(self, api_client, config_post_payload_ok):
        del config_post_payload_ok["property"]
        response = api_client.post(self.get_url(), config_post_payload_ok)
        
        assert response.json()['data'] == None
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['errors'][0]['field'] == "property"
        assert response.json()['errors'][0]['message'] == Messages.field_required()
        assert response.json()['errors'][0]['code'] == Messages.Code.required()
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
    def test_post_config_with_invalid_field_returns_400_bad_request(self, api_client, config_post_payload_ok):
        config_post_payload_ok['new_field'] = 'new_value'
        response = api_client.post(self.get_url(), config_post_payload_ok)
        
        assert response.json()['data'] == None
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['errors'][0]['field'] == "new_field"
        assert response.json()['errors'][0]['message'] == Messages.field_not_allowed()
        assert response.json()['errors'][0]['code'] == Messages.Code.invalid()
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
    def test_post_config_with_missing_value_returns_400_bad_request(self, api_client, config_post_payload_ok):
        del config_post_payload_ok["value"]
        response = api_client.post(self.get_url(), config_post_payload_ok)
        
        assert response.json()['data'] == None
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['errors'][0]['field'] == "value"
        assert response.json()['errors'][0]['message'] == Messages.field_required()
        assert response.json()['errors'][0]['code'] == Messages.Code.required()
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
    def test_get_config_returns_data_200_ok(self, api_client, config_table):
        response = api_client.get(self.get_url() + "1")
        
        config = Config.objects.get(pk=1)
        original = ConfigResponseSerializer(config)
        
        assert response.json()['data']['property'] == original.data['property']
        assert response.json()['data']['value'] == original.data['value']
        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.retrieved_successfully()
        assert response.json()['errors'] == None
        assert response.status_code == status.HTTP_200_OK
    
    def test_get_config_returns_no_data_404_not_found(self, api_client):
        response = api_client.get(self.get_url() + "1")
        
        assert response.json()['data'] == None
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['errors'][0]['field'] == None
        assert response.json()['errors'][0]['message'] == Messages.Get.not_found("config entry", "1") 
        assert response.json()['errors'][0]['code'] == "other"
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
    def test_put_config_updates_record_200_ok(self, api_client, config_table, config_put_payload_ok):
        response = api_client.put(self.get_url() + "1", config_put_payload_ok)
        
        assert response.json()['data']['value'] == config_put_payload_ok["value"]
        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.updated_successfully()  
        assert response.json()['errors'] == None
        assert response.status_code == status.HTTP_200_OK
        
    def test_put_config_updates_record_404_not_found(self, api_client, config_put_payload_ok):
        response = api_client.put(self.get_url() + "1", config_put_payload_ok)
        
        assert response.json()['data'] == None
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['errors'][0]['field'] == None
        assert response.json()['errors'][0]['message'] == Messages.Put.not_found("config entry", "1")
        assert response.json()['errors'][0]['code'] == "other"
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
    def test_put_config_updates_record_400_bad_request(self, api_client, config_table, config_put_payload_ok):
        config_put_payload_ok["new_field"] = "new_value"
        response = api_client.put(self.get_url() + "1", config_put_payload_ok)
        
        assert response.json()['data'] == None
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['errors'][0]['field'] == "new_field"
        assert response.json()['errors'][0]['message'] == Messages.field_not_allowed()
        assert response.json()['errors'][0]['code'] == Messages.Code.invalid()
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
    def test_delete_config_deletes_record_200_ok(self, api_client, config_table):
        response = api_client.delete(self.get_url() + "1")
        
        assert response.json()['data']['message'] == Messages.Delete.deleted_one("config entry", "1")
        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.deleted_successfully()
        assert response.json()['errors'] == None
        assert response.status_code == status.HTTP_200_OK
        
    def test_delete_config_deletes_record_404_not_found(self, api_client):
        response = api_client.delete(self.get_url() + "1")
        
        assert response.json()['data'] == None
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['errors'][0]['field'] == None
        assert response.json()['errors'][0]['message'] == Messages.Delete.not_found("config entry", "1")    
        assert response.json()['errors'][0]['code'] == Messages.Code.other()
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
    @patch('config_api.api.views.config_by_id_view.Config.objects.get')
    def test_delete_config_deletes_record_database_error(self, mock_get, api_client, config_table):
        mock_get.side_effect = Exception("Database connection lost")
        response = api_client.delete(self.get_url() + "1")
        
        assert response.json()['data'] == None
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['errors'][0]['field'] == None
        assert response.json()['errors'][0]['message'] == Messages.Delete.not_found("config entry", "1")
        assert response.json()['errors'][0]['code'] == Messages.Code.other()
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
    def test_config_model_str_representation(self):
        test_property_value = "test_property"
        test_value = "test_value"
        config = Config.objects.create(
            property=test_property_value,
            value=test_value
        )
        
        assert str(config) == f"{test_property_value}: {test_value}"

        
    def get_url(self):
        return "/" + str(os.getenv("CONFIG_URL_V1"))
        
    
