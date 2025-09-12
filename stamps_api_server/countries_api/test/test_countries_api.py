import os
from unittest.mock import patch
import pytest
from rest_framework import status

from countries_api.api.serializers.country_response_serializer import CountryResponseSerializer
from common.test.api_client import api_client
from common.test.countries_api_test_data import (
    countries_table,
    country_post_payload_ok,
    country_put_payload_ok,
)
from countries_api.models import Country


@pytest.mark.django_db
class TestCountriesAPI:
    """
    Test suite for the Countries API endpoints.
    """
    def test_list_countries(self, api_client, countries_table):
        response = api_client.get(self.__get_url())
        
        original = CountryResponseSerializer(countries_table, many=True)
        
        assert len(response.json()['data']) == len(countries_table)
        assert response.json()['data'] == original.data
        assert response.json()['success'] == True
        assert response.json()['message'] == "Retrieved successfully"
        assert response.json()['errors'] == None
        assert response.status_code == status.HTTP_200_OK
        
    def test_list_countries_empty(self, api_client):
        response = api_client.get(self.__get_url())
        
        assert len(response.json()['data']) == 0
        assert response.json()['success'] == True
        assert response.json()['message'] == "Retrieved successfully"
        assert response.json()['errors'] == None
        assert response.status_code == status.HTTP_200_OK


    def test_create_country_success(self, api_client, country_post_payload_ok):
        response = api_client.post(self.__get_url(), country_post_payload_ok)
        
        assert response.json()['data']['name'] == country_post_payload_ok['name']
        assert response.json()['success'] == True
        assert response.json()['message'] == "Created successfully"
        assert response.json()['errors'] == None
        assert response.status_code == status.HTTP_201_CREATED


    def test_create_country_invalid_payload_blank(self, api_client, country_post_payload_ok):
        del country_post_payload_ok['name']
        response = api_client.post(self.__get_url())
        
        assert response.json()['data'] == None
        assert response.json()['success'] == False
        assert response.json()['message'] == "Request failed"
        assert response.json()['errors'][0]['field'] == "name"
        assert response.json()['errors'][0]['message'] == "This field is required."
        assert response.json()['errors'][0]['code'] == "required"
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        

    def test_create_country_invalid_payload_missing(self, api_client, country_post_payload_ok):
        country_post_payload_ok['new_field'] = 'new_value'
        response = api_client.post(self.__get_url(), country_post_payload_ok)
        
        assert response.json()['data'] == None
        assert response.json()['success'] == False
        assert response.json()['message'] == "Request failed"
        assert response.json()['errors'][0]['field'] == "new_field"
        assert response.json()['errors'][0]['message'] == "This field is not allowed."
        assert response.json()['errors'][0]['code'] == "invalid"
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
    def test_create_country_duplicate_name(self, api_client, countries_table):
        response = api_client.post(self.__get_url(), {'name': countries_table[0].name})
        
        assert response.json()['data'] == None
        assert response.json()['success'] == False
        assert response.json()['message'] == "Request failed"
        assert response.json()['errors'][0]['field'] == "name"
        assert response.json()['errors'][0]['message'] == "Country with this name already exists."
        assert response.json()['errors'][0]['code'] == "unique"
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        

    def test_retrieve_country_success(self, api_client, countries_table,):
        response = api_client.get(self.__get_url() + "1")

        assert response.json()['data']['name'] == countries_table[0].name
        assert response.json()['success'] == True
        assert response.json()['message'] == "Retrieved successfully"
        assert response.json()['errors'] == None
        assert response.status_code == status.HTTP_200_OK

    def test_retrieve_country_not_found(self, api_client):
        response = api_client.get(self.__get_url() + "999")
        
        assert response.json()['data'] == None
        assert response.json()['success'] == False
        assert response.json()['message'] == "Request failed"
        assert response.json()['errors'][0]['field'] == None
        assert response.json()['errors'][0]['message'] == "Country with id: 999 not found"
        assert response.json()['errors'][0]['code'] == "other"
        assert response.status_code == status.HTTP_404_NOT_FOUND
        

    def test_update_country_success(self, api_client, countries_table,  country_put_payload_ok):
        response = api_client.put(self.__get_url() + "1", country_put_payload_ok)
        
        assert response.json()['data']['name'] == country_put_payload_ok['name'] 
        assert response.json()['success'] == True
        assert response.json()['message'] == "Updated successfully"
        assert response.json()['errors'] == None
        assert response.status_code == status.HTTP_200_OK

    def test_update_country_duplicate_name(self, api_client, countries_table):
        response = api_client.put(self.__get_url() + "1", {'name': countries_table[1].name})
        
        assert response.json()['data'] == None
        assert response.json()['success'] == False
        assert response.json()['message'] == "Request failed"
        assert response.json()['errors'][0]['field'] == "name"
        assert response.json()['errors'][0]['message'] == "Country with this name already exists."
        assert response.json()['errors'][0]['code'] == "unique"
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_country_not_found(self, api_client, country_put_payload_ok):
        response = api_client.put(self.__get_url() + "999", country_put_payload_ok)

        assert response.json()['data'] == None
        assert response.json()['success'] == False
        assert response.json()['message'] == "Request failed"
        assert response.json()['errors'][0]['field'] == None
        assert response.json()['errors'][0]['message'] == "Cannot update Country with id: 999. Not found in the database"
        assert response.json()['errors'][0]['code'] == "other"
        assert response.status_code == status.HTTP_404_NOT_FOUND
        

    def test_update_country_invalid_payload(self, api_client, countries_table, country_post_payload_ok):
        del country_post_payload_ok["name"]
        response = api_client.put(self.__get_url() + "1", country_post_payload_ok)
        
        assert response.json()['data'] == None
        assert response.json()['success'] == False
        assert response.json()['message'] == "Request failed"
        assert response.json()['errors'][0]['field'] == "name"
        assert response.json()['errors'][0]['message'] == "This field is required."
        assert response.json()['errors'][0]['code'] == "required"
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
    def test_delete_country_success(self, api_client, countries_table):
        response = api_client.delete(self.__get_url() + "1")
        
        assert response.json()['data']['message'] == "Successfully deleted Country with id: 1"
        assert response.json()['success'] == True
        assert response.json()['message'] == "Deleted successfully"
        assert response.json()['errors'] == None
        assert response.status_code == status.HTTP_200_OK

    def test_delete_country_not_found(self, api_client):
        response = api_client.delete(self.__get_url() + "1")
        
        assert response.json()['data'] == None
        assert response.json()['success'] == False
        assert response.json()['message'] == "Request failed"
        assert response.json()['errors'][0]['field'] == None
        assert response.json()['errors'][0]['message'] == "Cannot delete Country with id: 1. Not found in the database"
        assert response.json()['errors'][0]['code'] == "other"
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
    @patch('countries_api.api.views.countries_by_id_view.Country.objects.get')
    def test_delete_country_deletes_record_database_error(self, mock_get, api_client, countries_table):
        mock_get.side_effect = Exception("Database connection lost")
        response = api_client.delete(self.__get_url() + "1")
                
        assert response.json()['data'] == None
        assert response.json()['success'] == False
        assert response.json()['message'] == "Request failed"
        assert response.json()['errors'][0]['field'] == None
        assert response.json()['errors'][0]['message'] == "Cannot delete Country with id: 1. Not found in the database"
        assert response.json()['errors'][0]['code'] == "other"
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
    def test_country_model_str_representacion(self):
        test_country_value = "Constantinopla"
        
        country = Country.objects.create(name=test_country_value)
        
        assert str(country) == test_country_value
        
    def __get_url(self):
        return "/" + str(os.getenv("COUNTRIES_URL_V1"))