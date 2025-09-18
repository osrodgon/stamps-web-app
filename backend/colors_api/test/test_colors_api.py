import os
from unittest.mock import patch
import pytest
from rest_framework import status

# Assuming a similar serializer structure as in other apps
from colors_api.api.serializers.color_response_serializer import ColorResponseSerializer
from common.test.api_client import api_client
from common.test.colors_api_test_data import (
    colors_table,
    color_post_payload_ok,
    color_put_payload_ok,
)
from colors_api.models import Color


@pytest.mark.django_db
class TestColorsAPI:
    """
    Test suite for the Colors API endpoints.
    """
    def test_list_colors(self, api_client, colors_table):
        """
        Tests successful retrieval of a list of colors.
        """
        response = api_client.get(self.__get_url())
        
        original = ColorResponseSerializer(colors_table, many=True)
        
        assert response.json()['success'] is True
        assert response.json()['message'] == "Retrieved successfully"
        assert response.json()['errors'] is None
        assert len(response.json()['data']) == len(colors_table)
        assert response.json()['data'] == original.data
        assert response.status_code == status.HTTP_200_OK
        
    def test_list_colors_empty(self, api_client):
        """
        Tests retrieval of an empty list of colors.
        """
        response = api_client.get(self.__get_url())
        
        assert response.json()['success'] is True
        assert response.json()['message'] == "Retrieved successfully"
        assert response.json()['errors'] is None
        assert len(response.json()['data']) == 0
        assert response.status_code == status.HTTP_200_OK


    def test_create_color_success(self, api_client, color_post_payload_ok):
        """
        Tests successful creation of a new color.
        """
        response = api_client.post(self.__get_url(), color_post_payload_ok)
        
        assert response.json()['success'] is True
        assert response.json()['message'] == "Created successfully"
        assert response.json()['errors'] is None
        assert response.json()['data']['name'] == color_post_payload_ok['name']
        assert response.status_code == status.HTTP_201_CREATED

    def test_create_color_invalid_payload_missing(self, api_client):
        """
        Tests creating a color with a missing 'name' field.
        """
        response = api_client.post(self.__get_url(), {})
        
        assert response.json()['success'] is False
        assert response.json()['message'] == "Request failed"
        assert response.json()['data'] is None
        assert response.json()['errors'][0]['field'] == "name"
        assert response.json()['errors'][0]['message'] == "This field is required."
        assert response.json()['errors'][0]['code'] == "required"
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        
    def test_create_color_duplicate_name(self, api_client, colors_table):
        """
        Tests creating a color with a name that already exists.
        """
        response = api_client.post(self.__get_url(), {'name': colors_table[0].name})
        
        assert response.json()['success'] is False
        assert response.json()['message'] == "Request failed"
        assert response.json()['data'] is None
        assert response.json()['errors'][0]['field'] == "name"
        assert response.json()['errors'][0]['message'] == "Color with this name already exists."
        assert response.json()['errors'][0]['code'] == "unique"
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_retrieve_color_success(self, api_client, colors_table):
        """
        Tests successful retrieval of a single color by ID.
        """
        response = api_client.get(self.__get_url() + "1")

        assert response.json()['success'] is True
        assert response.json()['message'] == "Retrieved successfully"
        assert response.json()['errors'] is None
        assert response.json()['data']['name'] == colors_table[0].name
        assert response.status_code == status.HTTP_200_OK

    def test_retrieve_color_not_found(self, api_client):
        """
        Tests retrieving a color that does not exist.
        """
        response = api_client.get(self.__get_url() + "999")
        
        assert response.json()['success'] is False
        assert response.json()['message'] == "Request failed"
        assert response.json()['data'] is None
        assert response.json()['errors'][0]['field'] is None
        assert response.json()['errors'][0]['message'] == "Color with id: 999 not found."
        assert response.json()['errors'][0]['code'] == "other"
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_color_success(self, api_client, colors_table,  color_put_payload_ok):
        """
        Tests successful update of an existing color.
        """
        response = api_client.put(self.__get_url() + "1", color_put_payload_ok)
        
        assert response.json()['success'] is True
        assert response.json()['message'] == "Updated successfully"
        assert response.json()['errors'] is None
        assert response.json()['data']['name'] == color_put_payload_ok['name']
        assert response.status_code == status.HTTP_200_OK

    def test_update_color_duplicate_name(self, api_client, colors_table):
        """
        Tests updating a color to a name that already exists.
        """
        response = api_client.put(self.__get_url() + "1", {'name': colors_table[1].name})
        
        assert response.json()['success'] is False
        assert response.json()['message'] == "Request failed"
        assert response.json()['data'] is None
        assert response.json()['errors'][0]['field'] == "name"
        assert response.json()['errors'][0]['message'] == "Color with this name already exists."
        assert response.json()['errors'][0]['code'] == "unique"
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
    def test_update_color_not_found(self, api_client):
        """
        Tests updating a color that does not exist.
        """
        response = api_client.put(self.__get_url() + "999", {'name': 'New Name'})
        
        assert response.json()['success'] is False
        assert response.json()['message'] == "Request failed"
        assert response.json()['data'] is None
        assert response.json()['errors'][0]['field'] is None
        assert response.json()['errors'][0]['message'] == "Cannot update color with id: 999. Not found in the database."
        assert response.json()['errors'][0]['code'] == "other"
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
    def test_delete_color_success(self, api_client, colors_table):
        """
        Tests successful deletion of a color.
        """
        response = api_client.delete(self.__get_url() + "1")
        
        assert response.json()['success'] is True
        assert response.json()['message'] == "Deleted successfully"
        assert response.json()['errors'] is None
        assert response.json()['data']['message'] == "Successfully deleted color with id: 1."
        assert response.status_code == status.HTTP_200_OK

    def test_delete_color_not_found(self, api_client):
        """
        Tests deleting a color that does not exist.
        """
        response = api_client.delete(self.__get_url() + "999")
        
        assert response.json()['success'] is False
        assert response.json()['message'] == "Request failed"
        assert response.json()['data'] is None
        assert response.json()['errors'][0]['field'] is None
        assert response.json()['errors'][0]['message'] == "Cannot delete color with id: 999. Not found in the database."
        assert response.json()['errors'][0]['code'] == "other"
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
    @patch('colors_api.api.views.colors_by_id_view.Color.objects.get')
    def test_delete_color_database_error(self, mock_get, api_client):
        """
        Tests deleting a color that raises a database error.
        """
        mock_get.side_effect = Exception("Database connection lost")
        response = api_client.delete(self.__get_url() + "1")

        assert response.json()['data'] == None
        assert response.json()['success'] == False
        assert response.json()['message'] == "Request failed"
        assert response.json()['errors'][0]['field'] == None
        assert response.json()['errors'][0]['message'] == "Cannot delete color with id: 1. Not found in the database."
        assert response.json()['errors'][0]['code'] == "other"
        assert response.status_code == status.HTTP_404_NOT_FOUND
        

        
    def test_color_model_str_representation(self):
        """
        Tests the string representation of the Color model.
        """
        test_name = "test_name"
        color = Color.objects.create(
            name=test_name
        )
        
        assert str(color) == test_name
        
    def __get_url(self):
        return "/" + str(os.getenv("COLORS_URL_V1"))