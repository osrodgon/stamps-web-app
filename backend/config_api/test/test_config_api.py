import os
from unittest.mock import patch
import pytest
from rest_framework import status

from _backend.settings import CONFIG_URL_V1
from common.api.messages import Messages
from common.core import permissions
from common.test.abstract_api_unit_test import AbstractApiUnitTest
from common.test.api_client import api_client
from common.test.config_api_test_data import (
    config_table,
    config_post_payload_ok,
    config_put_payload_ok
)
from config_api.api.serializers.config_response_serializer import ConfigResponseSerializer
from config_api.models import Config


@pytest.mark.django_db
class TestConfigAPI(AbstractApiUnitTest):
    def test_get_all_config_returns_200_ok_data(self, api_client, config_table):
        self.permission(granted=True)
        response = api_client.get(self.__get_url())
        
        original = ConfigResponseSerializer(config_table,many=True)
        
        assert len(response.json()['data']) == len(original.data)
        assert response.json()['data'] == original.data
        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.retrieved_successfully()
        assert response.json()['errors'] == None
        assert response.status_code == status.HTTP_200_OK
        
    def test_get_all_config_returns_200_ok_no_data(self, api_client):
        self.permission(granted=True)
        response = api_client.get(self.__get_url())
        
        assert len(response.json()['data']) == 0
        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.retrieved_successfully()
        assert response.json()['errors'] == None
        assert response.status_code == status.HTTP_200_OK
        
    def test_get_all_config_returns_403_invalid_key(self, api_client):
        self.permission(granted=False, message=Messages.APIKey.invalid_key())
        response = api_client.get(self.__get_url())
        
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.APIKey.invalid_key()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
    def test_get_all_config_returns_403_invalid_user(self, api_client):
        self.permission(granted=False, message=Messages.APIKey.invalid_user())
        response = api_client.get(self.__get_url())
        
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.APIKey.invalid_user()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
    def test_get_all_config_returns_500_database_error_connection_lost(self, api_client, config_table):
        self.permission(granted=True)
        self.connection_lost(Config, self.GET_ALL)
        response = api_client.get(self.__get_url())

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Database.connection_lost()
        assert response.json()['errors'][0]['code'] == Messages.Code.connection_lost()
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_post_config_returns_201_created(self, api_client, config_post_payload_ok):
        self.permission(granted=True)
        response = api_client.post(self.__get_url(), config_post_payload_ok)
        
        assert response.json()['data']['property'] == config_post_payload_ok["property"]
        assert response.json()['data']['value'] == config_post_payload_ok["value"]
        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.created_successfully() 
        assert response.json()['errors'] == None
        assert response.status_code == status.HTTP_201_CREATED
        
    def test_post_config_returns_400_bad_request_missing_property(self, api_client, config_post_payload_ok):
        self.permission(granted=True)
        del config_post_payload_ok["property"]
        response = api_client.post(self.__get_url(), config_post_payload_ok)
        
        assert response.json()['data'] == None
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['errors'][0]['field'] == "property"
        assert response.json()['errors'][0]['message'] == Messages.field_required()
        assert response.json()['errors'][0]['code'] == Messages.Code.required()
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_post_config_returns_400_bad_request_missing_value(self, api_client, config_post_payload_ok):
        self.permission(granted=True)
        del config_post_payload_ok["value"]
        response = api_client.post(self.__get_url(), config_post_payload_ok)
        
        assert response.json()['data'] == None
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['errors'][0]['field'] == "value"
        assert response.json()['errors'][0]['message'] == Messages.field_required()
        assert response.json()['errors'][0]['code'] == Messages.Code.required()
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
    def test_post_config_returns_400_bad_request_invalid_field(self, api_client, config_post_payload_ok):
        self.permission(granted=True)
        config_post_payload_ok['new_field'] = 'new_value'
        response = api_client.post(self.__get_url(), config_post_payload_ok)
        
        assert response.json()['data'] == None
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['errors'][0]['field'] == "new_field"
        assert response.json()['errors'][0]['message'] == Messages.field_not_allowed()
        assert response.json()['errors'][0]['code'] == Messages.Code.invalid()
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
    def test_post_config_returns_403_invalid_key(self, api_client, config_post_payload_ok):
        self.permission(granted=False, message=Messages.APIKey.invalid_key())
        response = api_client.get(self.__get_url())
        
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.APIKey.invalid_key()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_post_config_returns_403_invalid_user(self, api_client, config_post_payload_ok):
        self.permission(granted=False, message=Messages.APIKey.invalid_user())
        response = api_client.get(self.__get_url())
        
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.APIKey.invalid_user()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
    def test_post_config_returns_500_database_error_connection_lost(self, api_client, config_table, config_post_payload_ok):
        self.permission(granted=True)
        self.connection_lost(Config, self.POST)
        response = api_client.post(self.__get_url(), config_post_payload_ok)

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Database.connection_lost()
        assert response.json()['errors'][0]['code'] == Messages.Code.connection_lost()
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        
    def test_get_one_config_returns_200_ok_data(self, api_client, config_table):
        self.permission(granted=True)
        id = str(config_table[1].id)
        response = api_client.get(self.__get_url() + id)
        
        config = Config.objects.get(pk=id)
        original = ConfigResponseSerializer(config)
        
        assert response.json()['data']['property'] == original.data['property']
        assert response.json()['data']['value'] == original.data['value']
        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.retrieved_successfully()
        assert response.json()['errors'] == None
        assert response.status_code == status.HTTP_200_OK
        
    def test_get_one_config_returns_403_invalid_key(self, api_client, config_table):
        self.permission(granted=False, message=Messages.APIKey.invalid_key())
        id = str(config_table[1].id)
        response = api_client.get(self.__get_url() + id)
        
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.APIKey.invalid_key()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
    def test_get_one_config_returns_403_invalid_user(self, api_client, config_table):
        self.permission(granted=False, message=Messages.APIKey.invalid_user())
        id = str(config_table[1].id)
        response = api_client.get(self.__get_url() + id)
        
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.APIKey.invalid_user()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_get_one_config_returns_404_not_found(self, api_client):
        self.permission(granted=True)
        response = api_client.get(self.__get_url() + "999")
        
        assert response.json()['data'] == None
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['errors'][0]['field'] == None
        assert response.json()['errors'][0]['message'] == Messages.Get.not_found("config entry", "999") 
        assert response.json()['errors'][0]['code'] == "other"
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
    def test_get_one_config_returns_500_database_error_connection_lost(self, api_client, config_table):
        self.permission(granted=True)
        self.connection_lost(Config, self.GET_ONE)
        id = str(config_table[1].id)
        response = api_client.get(self.__get_url() + id)

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Database.connection_lost()
        assert response.json()['errors'][0]['code'] == Messages.Code.connection_lost()
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        
    def test_put_config_returns_200_ok(self, api_client, config_table, config_put_payload_ok):
        self.permission(granted=True)
        id = str(config_table[1].id)
        response = api_client.put(self.__get_url() + id, config_put_payload_ok)
        
        assert response.json()['data']['value'] == config_put_payload_ok["value"]
        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.updated_successfully()  
        assert response.json()['errors'] == None
        assert response.status_code == status.HTTP_200_OK
        
    def test_put_config_returns_400_bad_request_invalid_field(self, api_client, config_table, config_put_payload_ok):
        self.permission(granted=True)
        config_put_payload_ok["new_field"] = "new_value"
        response = api_client.put(self.__get_url() + "1", config_put_payload_ok)
        
        assert response.json()['data'] == None
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['errors'][0]['field'] == "new_field"
        assert response.json()['errors'][0]['message'] == Messages.field_not_allowed()
        assert response.json()['errors'][0]['code'] == Messages.Code.invalid()
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
    def test_put_config_returns_403_invalid_key(self, api_client, config_table, config_put_payload_ok):
        self.permission(granted=False, message=Messages.APIKey.invalid_key())
        id = str(config_table[1].id)
        response = api_client.put(self.__get_url() + id, config_put_payload_ok)
        
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.APIKey.invalid_key()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
    def test_put_config_returns_403_invalid_user(self, api_client, config_table, config_put_payload_ok):
        self.permission(granted=False, message=Messages.APIKey.invalid_user())
        id = str(config_table[1].id)
        response = api_client.put(self.__get_url() + id, config_put_payload_ok)
        
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.APIKey.invalid_user()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
    def test_put_config_returns_404_not_found(self, api_client, config_put_payload_ok):
        self.permission(granted=True)
        response = api_client.put(self.__get_url() + "999" , config_put_payload_ok)
        
        assert response.json()['data'] == None
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['errors'][0]['field'] == None
        assert response.json()['errors'][0]['message'] == Messages.Put.not_found("config entry", "999")
        assert response.json()['errors'][0]['code'] == "other"
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
    def test_put_config_returns_500_database_error_connection_lost(self, api_client, config_table, config_put_payload_ok):
        self.permission(granted=True)
        self.connection_lost(Config, self.PUT)
        id = str(config_table[1].id)
        response = api_client.put(self.__get_url() + id, config_put_payload_ok)

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Database.connection_lost()
        assert response.json()['errors'][0]['code'] == Messages.Code.connection_lost()
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        
    def test_delete_config_returns_200_ok(self, api_client, config_table):
        self.permission(granted=True)
        id = str(config_table[1].id)
        response = api_client.delete(self.__get_url() + id)
        
        assert response.json()['data']['message'] == Messages.Delete.deleted_one("config entry", id)
        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.deleted_successfully()
        assert response.json()['errors'] == None
        assert response.status_code == status.HTTP_200_OK

    def test_delete_config_returns_403_invalid_key(self, api_client, config_table):
        self.permission(granted=False, message=Messages.APIKey.invalid_key())
        id = str(config_table[1].id)
        response = api_client.delete(self.__get_url() + id)
        
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.APIKey.invalid_key()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
    def test_delete_config_returns_403_invalid_user(self, api_client, config_table):
        self.permission(granted=False, message=Messages.APIKey.invalid_user())
        id = str(config_table[1].id)
        response = api_client.delete(self.__get_url() + id)
        
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.APIKey.invalid_user()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_delete_config_returns_404_not_found(self, api_client):
        self.permission(granted=True)
        response = api_client.delete(self.__get_url() + "999")
        
        assert response.json()['data'] == None
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['errors'][0]['field'] == None
        assert response.json()['errors'][0]['message'] == Messages.Delete.not_found("config entry", "999")    
        assert response.json()['errors'][0]['code'] == Messages.Code.other()
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
    def test_delete_config_returns_500_database_error_connection_lost(self, api_client, config_table):
        self.permission(granted=True)
        self.connection_lost(Config, self.DELETE)
        id = str(config_table[1].id)
        response = api_client.delete(self.__get_url() + id)
        
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Database.connection_lost()
        assert response.json()['errors'][0]['code'] == Messages.Code.connection_lost()
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        
    def test_config_model_str_representation(self):
        test_property_value = "test_property"
        test_value = "test_value"
        config = Config.objects.create(
            property=test_property_value,
            value=test_value
        )
        
        assert str(config) == f"{test_property_value}: {test_value}"

        
    def __get_url(self):
        return f"/{CONFIG_URL_V1}"
    
