from codecs import ascii_encode
from unittest.mock import patch
import pytest
import os
from rest_framework import status

from common.api.messages import Messages
from years_api.models import Year
from years_api.api.serializers.year_response_serializer import YearResponseSerializer
from common.test.api_client import api_client
from common.test.year_api_test_data import (
    years_table,
    year_post_payload_ok,
    year_put_payload_ok
)

@pytest.mark.django_db
class TestYearAPI:
    def test_get_years_returns_data_200_ok(self, api_client, years_table):
        response = api_client.get(self.__get_url())
        
        original = YearResponseSerializer(years_table,many=True)
        
        assert len(response.json()['data']) == len(original.data)
        assert response.json()['data'] == original.data
        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.retrieved_successfully()
        assert response.json()['errors'] == None
        assert response.status_code == status.HTTP_200_OK
    
    def test_get_years_returns_no_data_200_ok(self, api_client):
        response = api_client.get(self.__get_url())
        
        assert len(response.json()['data']) == 0
        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.retrieved_successfully()
        assert response.json()['errors'] == None
        assert response.status_code == status.HTTP_200_OK

    def test_post_year_creates_record_201_created(self, api_client, year_post_payload_ok):
        response = api_client.post(self.__get_url(), year_post_payload_ok)
        
        assert response.json()['data']['year'] == year_post_payload_ok["year"]
        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.created_successfully()
        assert response.json()['errors'] == None
        assert response.status_code == status.HTTP_201_CREATED
    
    def test_post_year_creates_record_400_bad_request(self, api_client, year_post_payload_ok):
        del year_post_payload_ok["year"]
        response = api_client.post(self.__get_url(), year_post_payload_ok)
        
        assert response.json()['data'] == None
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['errors'][0]['field'] == "year"
        assert response.json()['errors'][0]['message'] == Messages.field_required()
        assert response.json()['errors'][0]['code'] == Messages.Code.required()
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_post_year_with_invalid_field_returns_400_bad_request(self, api_client, year_post_payload_ok):
        year_post_payload_ok['new_field'] = 'new_value'
        response = api_client.post(self.__get_url(), year_post_payload_ok)
        
        assert response.json()['data'] == None
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['errors'][0]['field'] == "new_field"
        assert response.json()['errors'][0]['message'] == Messages.field_not_allowed()
        assert response.json()['errors'][0]['code'] == Messages.Code.invalid()
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_get_year_returns_data_200_ok(self, api_client,years_table):
        response = api_client.get(self.__get_url() + "1")
        
        year = Year.objects.get(pk=1)   
        original = YearResponseSerializer(year)
        
        assert response.json()['data']['year'] == original.data['year']
        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.retrieved_successfully()
        assert response.json()['errors'] == None
        assert response.status_code == status.HTTP_200_OK
        
    
    def test_get_year_returns_no_data_404_not_found(self, api_client):
        response = api_client.get(self.__get_url() + "1")
        
        assert response.json()['data'] == None
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['errors'][0]['field'] == None
        assert response.json()['errors'][0]['message'] == Messages.Get.not_found("year", 1)
        assert response.json()['errors'][0]['code'] == Messages.Code.other()
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
    def test_put_year_updates_record_200_ok(self, api_client, years_table, year_put_payload_ok):
        response = api_client.put(self.__get_url() + "1", year_put_payload_ok)
        
        assert response.json()['data']['year'] == year_put_payload_ok["year"]
        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.updated_successfully()
        assert response.json()['errors'] == None
        assert response.status_code == status.HTTP_200_OK
    
    def test_put_year_updates_record_400_bad_request(self, api_client, years_table, year_put_payload_ok):
        del year_put_payload_ok["year"]
        response = api_client.put(self.__get_url() + "1", year_put_payload_ok)
        
        assert response.json()['data'] == None
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['errors'][0]['field'] == "year"
        assert response.json()['errors'][0]['message'] == Messages.field_required()
        assert response.json()['errors'][0]['code'] == Messages.Code.required()
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_put_year_updates_record_400_not_found(self, api_client, year_put_payload_ok):
        response = api_client.put(self.__get_url() + "1", year_put_payload_ok)
        
        assert response.json()['data'] == None
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['errors'][0]['field'] == None
        assert response.json()['errors'][0]['message'] == Messages.Put.not_found("year", 1)
        assert response.json()['errors'][0]['code'] == Messages.Code.other()
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_delete_year_deletes_record_200_ok(self, api_client, years_table):
        response = api_client.delete(self.__get_url() + "1")
        
        
        assert response.json()['data']['message'] == Messages.Delete.deleted_one("year", 1)
        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.deleted_successfully()
        assert response.json()['errors'] == None
        assert response.status_code == status.HTTP_200_OK
        
    def test_delete_year_deletes_record_404_not_found(self, api_client):
        response = api_client.delete(self.__get_url() + "1")
        
        
        assert response.json()['data'] == None
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['errors'][0]['field'] == None
        assert response.json()['errors'][0]['message'] == Messages.Delete.not_found("year", 1)
        assert response.json()['errors'][0]['code'] == Messages.Code.other()
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
    @patch('years_api.api.views.years_by_id_view.Year.objects.get')
    def test_delete_year_deletes_record_database_error(self, mock_get, api_client, years_table):
        mock_get.side_effect = Exception("Database connection lost")
        response = api_client.delete(self.__get_url() + "1")
                
        assert response.json()['data'] == None
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['errors'][0]['field'] == None
        assert response.json()['errors'][0]['message'] == Messages.Delete.not_found("year", 1)
        assert response.json()['errors'][0]['code'] == Messages.Code.other()
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
    def test_year_model_str_representation(self):
        test_year_value = 2024
        year = Year.objects.create(year=test_year_value)
        
        assert str(year) == str(test_year_value)
        
    def __get_url(self):
        return "/" + str(os.getenv("YEARS_URL_V1"))