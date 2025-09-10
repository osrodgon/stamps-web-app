from codecs import ascii_encode
from unittest.mock import patch
import pytest
import os
from rest_framework import status

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
        response = api_client.get(self.get_url())
        
        original = YearResponseSerializer(years_table,many=True)
        
        assert len(response.json()['data']) == len(original.data)
        assert response.json()['data'] == original.data
        assert response.json()['success'] == True
        assert response.json()['message'] == "Retrieved successfully"
        assert response.json()['errors'] == None
        assert response.status_code == status.HTTP_200_OK
    
    def test_get_years_returns_no_data_200_ok(self, api_client):
        response = api_client.get(self.get_url())
        
        assert len(response.json()['data']) == 0
        assert response.json()['success'] == True
        assert response.json()['message'] == "Retrieved successfully"
        assert response.json()['errors'] == None
        assert response.status_code == status.HTTP_200_OK

    def test_post_year_creates_record_201_created(self, api_client, year_post_payload_ok):
        response = api_client.post(self.get_url(), year_post_payload_ok)
        
        assert response.json()['data']['year'] == year_post_payload_ok["year"]
        assert response.json()['success'] == True
        assert response.json()['message'] == "Created successfully"
        assert response.json()['errors'] == None
        assert response.status_code == status.HTTP_201_CREATED
    
    def test_post_year_creates_record_400_bad_request(self, api_client, year_post_payload_ok):
        del year_post_payload_ok["year"]
        response = api_client.post(self.get_url(), year_post_payload_ok)
        
        assert response.json()['data'] == None
        assert response.json()['success'] == False
        assert response.json()['message'] == "Request failed"
        assert response.json()['errors'][0]['field'] == "year"
        assert response.json()['errors'][0]['message'] == "This field is required."
        assert response.json()['errors'][0]['code'] == "required"
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_post_year_with_invalid_field_returns_400_bad_request(self, api_client, year_post_payload_ok):
        year_post_payload_ok['new_field'] = 'new_value'
        response = api_client.post(self.get_url(), year_post_payload_ok)
        
        assert response.json()['data'] == None
        assert response.json()['success'] == False
        assert response.json()['message'] == "Request failed"
        assert response.json()['errors'][0]['field'] == "new_field"
        assert response.json()['errors'][0]['message'] == "This field is not allowed."
        assert response.json()['errors'][0]['code'] == "invalid"
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_get_year_returns_data_200_ok(self, api_client,years_table):
        response = api_client.get(self.get_url() + "1")
        
        year = Year.objects.get(pk=1)   
        original = YearResponseSerializer(year)
        
        assert response.json()['data']['year'] == original.data['year']
        assert response.json()['success'] == True
        assert response.json()['message'] == "Retrieved successfully"
        assert response.json()['errors'] == None
        assert response.status_code == status.HTTP_200_OK
        
    
    def test_get_year_returns_no_data_404_not_found(self, api_client):
        response = api_client.get(self.get_url() + "1")
        
        assert response.json()['data'] == None
        assert response.json()['success'] == False
        assert response.json()['message'] == "Request failed"
        assert response.json()['errors'][0]['field'] == None
        assert response.json()['errors'][0]['message'] == "Year with id: 1 not found"
        assert response.json()['errors'][0]['code'] == "other"
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
    def test_put_year_updates_record_200_ok(self, api_client, years_table, year_put_payload_ok):
        response = api_client.put(self.get_url() + "1", year_put_payload_ok)
        
        assert response.json()['data']['year'] == year_put_payload_ok["year"]
        assert response.json()['success'] == True
        assert response.json()['message'] == "Updated successfully"
        assert response.json()['errors'] == None
        assert response.status_code == status.HTTP_200_OK
    
    def test_put_year_updates_record_400_bad_request(self, api_client, years_table, year_put_payload_ok):
        del year_put_payload_ok["year"]
        response = api_client.put(self.get_url() + "1", year_put_payload_ok)
        
        assert response.json()['data'] == None
        assert response.json()['success'] == False
        assert response.json()['message'] == "Request failed"
        assert response.json()['errors'][0]['field'] == "year"
        assert response.json()['errors'][0]['message'] == "This field is required."
        assert response.json()['errors'][0]['code'] == "required"
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_put_year_updates_record_400_not_found(self, api_client, year_put_payload_ok):
        response = api_client.put(self.get_url() + "1", year_put_payload_ok)
        
        assert response.json()['data'] == None
        assert response.json()['success'] == False
        assert response.json()['message'] == "Request failed"
        assert response.json()['errors'][0]['field'] == None
        assert response.json()['errors'][0]['message'] == "Cannot update year with id: 1. Not found in the database"
        assert response.json()['errors'][0]['code'] == "other"
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_delete_year_deletes_record_200_ok(self, api_client, years_table):
        response = api_client.delete(self.get_url() + "1")
        
        
        assert response.json()['data']['message'] == "Successfully deleted year with id: 1"
        assert response.json()['success'] == True
        assert response.json()['message'] == "Deleted successfully"
        assert response.json()['errors'] == None
        assert response.status_code == status.HTTP_200_OK
        
    def test_delete_year_deletes_record_404_not_found(self, api_client):
        response = api_client.delete(self.get_url() + "1")
        
        
        assert response.json()['data'] == None
        assert response.json()['success'] == False
        assert response.json()['message'] == "Request failed"
        assert response.json()['errors'][0]['field'] == None
        assert response.json()['errors'][0]['message'] == "Cannot delete year with id: 1. Not found in the database"
        assert response.json()['errors'][0]['code'] == "other"
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
    @patch('years_api.api.views.years_by_id_view.Year.objects.get')
    def test_delete_year_deletes_record_database_error(self, mock_get, api_client, years_table):
        mock_get.side_effect = Exception("Database connection lost")
        response = api_client.delete(self.get_url() + "1")
                
        assert response.json()['data'] == None
        assert response.json()['success'] == False
        assert response.json()['message'] == "Request failed"
        assert response.json()['errors'][0]['field'] == None
        assert response.json()['errors'][0]['message'] == "Cannot delete year with id: 1. Not found in the database"
        assert response.json()['errors'][0]['code'] == "other"
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
    def test_year_model_str_representation(self):
        test_year_value = 2024
        year = Year.objects.create(year=test_year_value)
        
        assert str(year) == str(test_year_value)
        
    def get_url(self):
        return "/" + str(os.getenv("YEARS_URL_V1"))