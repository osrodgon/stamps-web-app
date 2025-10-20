from unittest.mock import patch
import pytest
from rest_framework import status

# Assuming a similar serializer structure as in other apps
from _backend.settings import COLORS_URL_V1
from colors_api.api.serializers.color_response_serializer import ColorResponseSerializer
from common.api.messages import Messages
from common.test.abstract_api import AbstractAPI
from common.test.api_client import api_client
from common.test.colors_api_test_data import (
    colors_table,
    color_post_payload_ok,
    color_put_payload_ok,
)
from colors_api.models import Color


@pytest.mark.django_db
class TestColorsAPI(AbstractAPI):
    def test_get_all_colors_returns_200_ok_data(self, api_client, colors_table):
        self.permission(granted=True)
        response = api_client.get(self.__get_url())
        
        original = ColorResponseSerializer(colors_table, many=True)
        
        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.retrieved_successfully()
        assert response.json()['errors'] == None
        assert len(response.json()['data']) == len(colors_table)
        assert response.json()['data'] == original.data
        assert response.status_code == status.HTTP_200_OK
        
    def test_get_all_colors_returns_200_ok_no_data(self, api_client):
        self.permission(granted=True)
        response = api_client.get(self.__get_url())
        
        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.retrieved_successfully()
        assert response.json()['errors'] == None
        assert len(response.json()['data']) == 0
        assert response.status_code == status.HTTP_200_OK
        
    def test_get_all_colors_returns_403_invalid_key(self, api_client):
        self.permission(granted=False, message=Messages.APIKey.invalid_key())
        response = api_client.get(self.__get_url())
        
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.APIKey.invalid_key()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
    def test_get_all_colors_returns_403_invalid_user(self, api_client):
        self.permission(granted=False, message=Messages.APIKey.invalid_user())
        response = api_client.get(self.__get_url())
        
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.APIKey.invalid_user()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
    def test_get_all_colors_returns_500_database_error_connection_lost(self, api_client):
        self.permission(granted=True)
        self.connection_lost('colors_api.api.views.colors_view.Color.objects.all')
        response = api_client.get(self.__get_url())

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Database.connection_lost()
        assert response.json()['errors'][0]['code'] == Messages.Code.connection_lost()
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_post_color_returns_201_created(self, api_client, color_post_payload_ok):
        self.permission(granted=True)
        response = api_client.post(self.__get_url(), color_post_payload_ok)
        
        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.created_successfully()
        assert response.json()['errors'] == None
        assert response.json()['data']['name'] == color_post_payload_ok['name']
        assert response.status_code == status.HTTP_201_CREATED

    def test_post_color_returns_400_bad_request_invalid_payload_missing_name(self, api_client):
        self.permission(granted=True)
        response = api_client.post(self.__get_url(), {})
        
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == "name"
        assert response.json()['errors'][0]['message'] == Messages.field_required()
        assert response.json()['errors'][0]['code'] == Messages.Code.required()
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
    def test_post_color_returns_400_bad_request_invalid_payload_field_not_allowed(self, api_client, color_post_payload_ok):
        self.permission(granted=True)
        color_post_payload_ok['invalid_field'] = 'value'
        response = api_client.post(self.__get_url(), color_post_payload_ok)
        
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == "invalid_field"
        assert response.json()['errors'][0]['message'] == Messages.field_not_allowed()
        assert response.json()['errors'][0]['code'] == Messages.Code.invalid()
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_post_color_returns_400_bad_request_duplicate_name(self, api_client, colors_table):
        self.permission(granted=True)
        response = api_client.post(self.__get_url(), {'name': colors_table[0].name})
        
        assert response.json()['success'] is False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] is None
        assert response.json()['errors'][0]['field'] == "name"
        assert response.json()['errors'][0]['message'] == Messages.Post.already_exists("color", 'name')  
        assert response.json()['errors'][0]['code'] == Messages.Code.unique()
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
    def test_post_color_returns_403_invalid_key(self, api_client, color_post_payload_ok):
        self.permission(granted=False, message=Messages.APIKey.invalid_key())
        response = api_client.post(self.__get_url(), color_post_payload_ok)
        
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.APIKey.invalid_key()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
    def test_post_color_returns_403_invalid_user(self, api_client, color_post_payload_ok):
        self.permission(granted=False, message=Messages.APIKey.invalid_user())
        response = api_client.post(self.__get_url(), color_post_payload_ok)
        
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.APIKey.invalid_user()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
    def test_post_color_returns_500_database_error_connection_lost(self, api_client, color_post_payload_ok):
        self.permission(granted=True)
        self.connection_lost('colors_api.api.views.colors_view.Color.save')
        response = api_client.post(self.__get_url(), color_post_payload_ok)

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Database.connection_lost()
        assert response.json()['errors'][0]['code'] == Messages.Code.connection_lost()
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_get_one_color_returns_200_ok_data(self, api_client, colors_table):
        self.permission(granted=True)
        id = str(colors_table[0].id)
        response = api_client.get(self.__get_url() + id)

        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.retrieved_successfully()
        assert response.json()['errors'] == None
        assert response.json()['data']['name'] == colors_table[0].name
        assert response.status_code == status.HTTP_200_OK
        
    def test_get_one_color_returns_403_invalid_key(self, api_client, colors_table):
        self.permission(granted=False, message=Messages.APIKey.invalid_key())
        id = str(colors_table[0].id)
        response = api_client.get(self.__get_url() + id)
        
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.APIKey.invalid_key()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
    def test_get_one_color_returns_403_invalid_user(self, api_client, colors_table):
        self.permission(granted=False, message=Messages.APIKey.invalid_user())
        id = str(colors_table[0].id)
        response = api_client.get(self.__get_url() + id)
        
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.APIKey.invalid_user()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_one_color_returns_404_not_found(self, api_client):
        self.permission(granted=True)
        response = api_client.get(self.__get_url() + "999")
        
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == None
        assert response.json()['errors'][0]['message'] == Messages.Get.not_found("color", "999")
        assert response.json()['errors'][0]['code'] == Messages.Code.other()
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
    def test_get_one_color_returns_500_database_error_connection_lost(self, api_client, colors_table):
        self.permission(granted=True)
        self.connection_lost('colors_api.api.views.colors_by_id_view.Color.objects.get')
        id = str(colors_table[0].id)
        response = api_client.get(self.__get_url() + id)

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Database.connection_lost()
        assert response.json()['errors'][0]['code'] == Messages.Code.connection_lost()
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_put_color_returns_200_ok(self, api_client, colors_table,  color_put_payload_ok):
        self.permission(granted=True)
        id = str(colors_table[0].id)
        response = api_client.put(self.__get_url() + id, color_put_payload_ok)
        
        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.updated_successfully()
        assert response.json()['errors'] == None
        assert response.json()['data']['name'] == color_put_payload_ok['name']
        assert response.status_code == status.HTTP_200_OK

    def test_put_color_returns_400_bad_request_duplicate_name(self, api_client, colors_table):
        self.permission(granted=True)
        id = str(colors_table[0].id)
        response = api_client.put(self.__get_url() + id, {'name': colors_table[1].name})
        
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == "name"
        assert response.json()['errors'][0]['message'] == Messages.Put.already_exists("color", colors_table[1].name) 
        assert response.json()['errors'][0]['code'] == Messages.Code.unique()
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
    def test_put_color_returns_403_invalid_key(self, api_client, colors_table, color_put_payload_ok):
        self.permission(granted=False, message=Messages.APIKey.invalid_key())
        id = str(colors_table[0].id)
        response = api_client.put(self.__get_url() + id, color_put_payload_ok)
        
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.APIKey.invalid_key()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
    def test_put_color_returns_403_invalid_user(self, api_client, colors_table, color_put_payload_ok):
        self.permission(granted=False, message=Messages.APIKey.invalid_user())
        id = str(colors_table[0].id)
        response = api_client.put(self.__get_url() + id, color_put_payload_ok)
        
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.APIKey.invalid_user()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
    def test_put_color_returns_404_not_found(self, api_client):
        self.permission(granted=True)
        response = api_client.put(self.__get_url() + "999", {'name': 'New Name'})
        
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == None
        assert response.json()['errors'][0]['message'] == Messages.Put.not_found("color", "999")
        assert response.json()['errors'][0]['code'] == Messages.Code.other()
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
    def test_put_color_returns_500_database_error_connection_lost(self, api_client, colors_table, color_put_payload_ok):
        self.permission(granted=True)
        self.connection_lost('colors_api.api.views.colors_by_id_view.Color.save')
        id = str(colors_table[0].id)
        response = api_client.put(self.__get_url() + id, color_put_payload_ok)

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Database.connection_lost()
        assert response.json()['errors'][0]['code'] == Messages.Code.connection_lost()
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        
    def test_delete_color_returns_200_ok(self, api_client, colors_table):
        self.permission(granted=True)
        id = str(colors_table[0].id)
        response = api_client.delete(self.__get_url() + id)
        
        assert response.json()['success'] is True
        assert response.json()['message'] == Messages.deleted_successfully()
        assert response.json()['errors'] is None
        assert response.json()['data']['message'] == Messages.Delete.deleted_one("color", "1")
        assert response.status_code == status.HTTP_200_OK
        
    def test_delete_color_returns_403_invalid_key(self, api_client, colors_table):
        self.permission(granted=False, message=Messages.APIKey.invalid_key())
        id = str(colors_table[0].id)
        response = api_client.delete(self.__get_url() + id)

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.APIKey.invalid_key()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
    def test_delete_color_returns_403_invalid_user(self, api_client, colors_table):
        self.permission(granted=False, message=Messages.APIKey.invalid_user())
        id = str(colors_table[0].id)
        response = api_client.delete(self.__get_url() + id)

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.APIKey.invalid_user()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_color_returns_404not_found(self, api_client):
        self.permission(granted=True)
        response = api_client.delete(self.__get_url() + "999")
        
        assert response.json()['success'] is False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] is None
        assert response.json()['errors'][0]['field'] is None
        assert response.json()['errors'][0]['message'] == Messages.Delete.not_found("color", "999")
        assert response.json()['errors'][0]['code'] == Messages.Code.other()
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
    def test_delete_color_returns_500_database_error_connection_lost(self, api_client, colors_table):
        self.permission(granted=True)
        self.connection_lost('colors_api.api.views.colors_by_id_view.Color.delete')
        id = str(colors_table[0].id)
        response = api_client.delete(self.__get_url() + id)

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Database.connection_lost()
        assert response.json()['errors'][0]['code'] == Messages.Code.connection_lost()
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_color_model_str_representation(self):
        test_name = "test_name"
        color = Color.objects.create(
            name=test_name
        )
        
        assert str(color) == test_name
        
    def __get_url(self):
        return f"/{COLORS_URL_V1}"