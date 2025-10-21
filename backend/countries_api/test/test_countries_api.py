import os
from unittest.mock import patch
from urllib import response
import pytest
from rest_framework import status

from _backend.settings import COUNTRIES_URL_V1
from common import api
from common.api.messages import Messages
from common.test.abstract_api_unit_test import AbstractApiUnitTest
from countries_api.api.serializers.country_response_serializer import CountryResponseSerializer
from common.test.api_client import api_client
from common.test.countries_api_test_data import (
    countries_table,
    country_post_payload_ok,
    country_put_payload_ok,
)
from countries_api.models import Country


@pytest.mark.django_db
class TestCountriesAPI(AbstractApiUnitTest):
    """
    Test suite for the Countries API endpoints.
    """
    def test_get_all_countries_returns_200_ok_data(self, api_client, countries_table):
        self.permission(granted=True)
        response = api_client.get(self.__get_url())
        
        original = CountryResponseSerializer(countries_table, many=True)
        
        assert len(response.json()['data']) == len(countries_table)
        assert response.json()['data'] == original.data
        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.retrieved_successfully()
        assert response.json()['errors'] == None
        assert response.status_code == status.HTTP_200_OK
        
    def test_get_all_countries_returns_200_ok_no_data(self, api_client):
        self.permission(granted=True)
        response = api_client.get(self.__get_url())
        
        assert len(response.json()['data']) == 0
        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.retrieved_successfully()
        assert response.json()['errors'] == None
        assert response.status_code == status.HTTP_200_OK
        
    def test_get_all_countries_returns_403_invalid_key(self, api_client, countries_table):
        self.permission(granted=False, message=Messages.APIKey.invalid_key())
        response = api_client.get(self.__get_url())

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.APIKey.invalid_key()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
    def test_get_all_countries_returns_403_invalid_user(self, api_client, countries_table):
        self.permission(granted=False, message=Messages.APIKey.invalid_user())
        response = api_client.get(self.__get_url())

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.APIKey.invalid_user()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
    def test_get_all_countries_returns_500_database_error_connection_lost(self, api_client, countries_table):
        self.permission(granted=True)
        self.connection_lost(Country, self.GET_ALL)
        response = api_client.get(self.__get_url())

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Database.connection_lost()
        assert response.json()['errors'][0]['code'] == Messages.Code.connection_lost()
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_post_country_returns_201_created(self, api_client, country_post_payload_ok):
        self.permission(granted=True)
        response = api_client.post(self.__get_url(), country_post_payload_ok)
        
        assert response.json()['data']['name'] == country_post_payload_ok['name']
        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.created_successfully()
        assert response.json()['errors'] == None
        assert response.status_code == status.HTTP_201_CREATED

    def test_post_country_returns_400_bad_request_missing_field(self, api_client, country_post_payload_ok):
        self.permission(granted=True)
        del country_post_payload_ok['name']
        response = api_client.post(self.__get_url())
        
        assert response.json()['data'] == None
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['errors'][0]['field'] == "name"
        assert response.json()['errors'][0]['message'] == Messages.field_required()
        assert response.json()['errors'][0]['code'] == Messages.Code.required()
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        

    def test_post_country_returns_400_bad_request_invalid_field(self, api_client, country_post_payload_ok):
        self.permission(granted=True)
        country_post_payload_ok['new_field'] = 'new_value'
        response = api_client.post(self.__get_url(), country_post_payload_ok)
        
        assert response.json()['data'] == None
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['errors'][0]['field'] == "new_field"
        assert response.json()['errors'][0]['message'] == Messages.field_not_allowed()
        assert response.json()['errors'][0]['code'] == Messages.Code.invalid()
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
    def test_post_country_returns_400_bad_request_duplicate_name(self, api_client, countries_table):
        self.permission(granted=True)
        response = api_client.post(self.__get_url(), {'name': countries_table[0].name})
        
        assert response.json()['data'] == None
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['errors'][0]['field'] == "name"
        assert response.json()['errors'][0]['message'] == Messages.Post.already_exists("country", "name")
        assert response.json()['errors'][0]['code'] == Messages.Code.unique()
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
    def test_post_country_returns_403_invalid_key(self, api_client, country_post_payload_ok):
        self.permission(granted=False, message=Messages.APIKey.invalid_key())
        response = api_client.post(self.__get_url(), country_post_payload_ok)
        
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.APIKey.invalid_key()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
    def test_post_country_returns_403_invalid_user(self, api_client, country_post_payload_ok):
        self.permission(granted=False, message=Messages.APIKey.invalid_user())
        response = api_client.post(self.__get_url(), country_post_payload_ok)
        
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.APIKey.invalid_user()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
    def test_post_country_returns_500_database_error_connection_lost(self, api_client, country_post_payload_ok):
        self.permission(granted=True)
        self.connection_lost(Country, self.POST)
        response = api_client.post(self.__get_url(), country_post_payload_ok)

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Database.connection_lost()
        assert response.json()['errors'][0]['code'] == Messages.Code.connection_lost()
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        
    def test_get_one_country_returns_200_ok(self, api_client, countries_table,):
        self.permission(granted=True)
        id = str(countries_table[0].id)
        response = api_client.get(self.__get_url() + id)

        assert response.json()['data']['name'] == countries_table[0].name
        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.retrieved_successfully()
        assert response.json()['errors'] == None
        assert response.status_code == status.HTTP_200_OK
        
    def test_get_one_country_returns_403_invalid_key(self, api_client, countries_table):
        self.permission(granted=False, message=Messages.APIKey.invalid_key())
        id = str(countries_table[0].id)
        response = api_client.get(self.__get_url() + id)
        
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.APIKey.invalid_key()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
    def test_get_one_country_returns_403_invalid_user(self, api_client, countries_table):
        self.permission(granted=False, message=Messages.APIKey.invalid_user())
        id = str(countries_table[0].id)
        response = api_client.get(self.__get_url() + id)
        
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.APIKey.invalid_user()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_one_country_returns_404_not_found(self, api_client):
        self.permission(granted=True)
        response = api_client.get(self.__get_url() + "999")
        
        assert response.json()['data'] == None
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['errors'][0]['field'] == None
        assert response.json()['errors'][0]['message'] == Messages.Get.not_found("country", "999")
        assert response.json()['errors'][0]['code'] == Messages.Code.other()
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
    def test_get_one_country_returns_500_database_error_connection_lost(self, api_client, countries_table):
        self.permission(granted=True)
        self.connection_lost(Country, self.GET_ONE)
        id = str(countries_table[0].id)
        response = api_client.get(self.__get_url() + id)

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Database.connection_lost()
        assert response.json()['errors'][0]['code'] == Messages.Code.connection_lost()
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_put_country_returns_200_ok(self, api_client, countries_table,  country_put_payload_ok):
        self.permission(granted=True)
        response = api_client.put(self.__get_url() + "1", country_put_payload_ok)
        
        assert response.json()['data']['name'] == country_put_payload_ok['name'] 
        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.updated_successfully()
        assert response.json()['errors'] == None
        assert response.status_code == status.HTTP_200_OK
        
    def test_put_country_returns_400_bad_request_missing_field(self, api_client, countries_table, country_post_payload_ok):
        self.permission(granted=True)
        del country_post_payload_ok["name"]
        response = api_client.put(self.__get_url() + "1", country_post_payload_ok)
        
        assert response.json()['data'] == None
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['errors'][0]['field'] == "name"
        assert response.json()['errors'][0]['message'] == Messages.field_required()
        assert response.json()['errors'][0]['code'] == Messages.Code.required()
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_put_country_returns_400_bad_request_duplicate_name(self, api_client, countries_table):
        self.permission(granted=True)
        response = api_client.put(self.__get_url() + "1", {'name': countries_table[1].name})
        
        assert response.json()['data'] == None
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['errors'][0]['field'] == "name"
        assert response.json()['errors'][0]['message'] == Messages.Put.already_exists("country", "name")
        assert response.json()['errors'][0]['code'] == Messages.Code.unique()
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
    def test_put_country_returns_403_invalid_key(self, api_client, country_put_payload_ok):
        self.permission(granted=False, message=Messages.APIKey.invalid_key())
        response = api_client.put(self.__get_url() + "999", country_put_payload_ok)
        
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.APIKey.invalid_key()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
    def test_put_country_returns_403_invalid_user(self, api_client, country_put_payload_ok):
        self.permission(granted=False, message=Messages.APIKey.invalid_user())
        response = api_client.put(self.__get_url() + "999", country_put_payload_ok)
        
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.APIKey.invalid_user()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_put_country_returns_404_not_found(self, api_client, country_put_payload_ok):
        self.permission(granted=True)
        response = api_client.put(self.__get_url() + "999", country_put_payload_ok)

        assert response.json()['data'] == None
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['errors'][0]['field'] == None
        assert response.json()['errors'][0]['message'] == Messages.Put.not_found("country", "999")
        assert response.json()['errors'][0]['code'] == Messages.Code.other()
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
    def test_put_country_returns_500_database_error_connection_lost(self, api_client, countries_table, country_put_payload_ok):
        self.permission(granted=True)
        self.connection_lost(Country, self.PUT)
        id = str(countries_table[0].id)
        response = api_client.put(self.__get_url() + id, country_put_payload_ok)

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Database.connection_lost()
        assert response.json()['errors'][0]['code'] == Messages.Code.connection_lost()
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        
    def test_delete_country_returns_200_ok(self, api_client, countries_table):
        self.permission(granted=True)
        id = str(countries_table[0].id)
        response = api_client.delete(self.__get_url() + id)
        
        assert response.json()['data']['message'] == Messages.Delete.deleted_one("country", id)
        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.deleted_successfully()
        assert response.json()['errors'] == None
        assert response.status_code == status.HTTP_200_OK
        
    def test_delete_country_returns_403_invalid_key(self, api_client, countries_table):
        self.permission(granted=False, message=Messages.APIKey.invalid_key())
        id = str(countries_table[0].id)
        response = api_client.delete(self.__get_url() + id)
        
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.APIKey.invalid_key()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
    def test_delete_country_returns_403_invalid_user(self, api_client, countries_table):
        self.permission(granted=False, message=Messages.APIKey.invalid_user())
        id = str(countries_table[0].id)
        response = api_client.delete(self.__get_url() + id)
        
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.APIKey.invalid_user()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_country_returns_404_not_found(self, api_client):
        self.permission(granted=True)
        response = api_client.delete(self.__get_url() + "999")
        
        assert response.json()['data'] == None
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['errors'][0]['field'] == None
        assert response.json()['errors'][0]['message'] == Messages.Delete.not_found("country", "999")
        assert response.json()['errors'][0]['code'] == Messages.Code.other()
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
    def test_delete_country_returns_500_database_error_connection_lost(self, api_client, countries_table):
        self.permission(granted=True)
        self.connection_lost(Country, self.DELETE)
        id = str(countries_table[0].id)
        response = api_client.delete(self.__get_url() + id)
                
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Database.connection_lost()
        assert response.json()['errors'][0]['code'] == Messages.Code.connection_lost()
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        
    def test_country_model_str_representacion(self):
        test_country_value = "Constantinopla"
        
        country = Country.objects.create(name=test_country_value)
        
        assert str(country) == test_country_value
        
    def __get_url(self):
        return f"/{COUNTRIES_URL_V1}"
    