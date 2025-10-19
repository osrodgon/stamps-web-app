import os
from unittest.mock import patch
from urllib import response
import pytest
from rest_framework import status

from _backend.settings import COLLECTIONS_URL_V1
from collections_api.api.serializers.collection_response_serializer import CollectionResponseSerializer
from collections_api.models import Collection
from common.api.messages import Messages
from common.test.api_client import api_client # api_client is needed for other fixtures
from common.test.collections_api_test_data import (
    collections_table,
    collection_post_payload_ok,
    collection_put_payload_ok,
)

@pytest.mark.django_db
class TestCollectionsAPI:
    test_user = "test_user"
    test_key = "test_key"
    
    """
    Test suite for the Collections API endpoints.
    """
    def test_list_collections_success(self, api_client, collections_table):
        """
        Tests successful retrieval of a list of collections.
        """
        with patch(
            'collections_api.api.views.collections_view.CollectionsView.api_key.authenticate',
            return_value=(self.test_user, self.test_key)
        ):
            response = api_client.get(self.__get_url())
        
        original = CollectionResponseSerializer(collections_table, many=True)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['success'] is True
        assert response.json()['message'] == Messages.retrieved_successfully()
        assert response.json()['errors'] is None
        assert len(response.json()['data']) == len(collections_table)
        assert response.json()['data'] == original.data
    
    def test_list_collections_empty(self, api_client):
        """
        Tests retrieval of an empty list of collections.
        """
        with patch(
            'collections_api.api.views.collections_view.CollectionsView.api_key.authenticate',
            return_value=(self.test_user, self.test_key)
        ):
            response = api_client.get(self.__get_url())
        
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['success'] is True
        assert response.json()['message'] == Messages.retrieved_successfully()
        assert response.json()['errors'] is None
        assert len(response.json()['data']) == 0
        
    def test_create_collection_success(self, api_client, collection_post_payload_ok):
        """
        Tests successful creation of a new collection.
        """
        with patch(
            'collections_api.api.views.collections_view.CollectionsView.api_key.authenticate',
            return_value=(self.test_user, self.test_key)
        ):
            response = api_client.post(self.__get_url(),collection_post_payload_ok)
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()['success'] is True
        assert response.json()['message'] == Messages.created_successfully()
        assert response.json()['errors'] is None
        assert response.json()['data']['name'] == collection_post_payload_ok['name']

    def test_create_collection_missing_name(self, api_client):
        """
        Tests creating a collection with a missing 'name' field.
        """
        with patch(
            'collections_api.api.views.collections_view.CollectionsView.api_key.authenticate',
            return_value=(self.test_user, self.test_key)
        ):
            response = api_client.post(self.__get_url(), {"description": "a description"})
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()['success'] is False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] is None
        assert response.json()['errors'][0]['field'] == "name"
        assert response.json()['errors'][0]['code'] == Messages.Code.required()
        assert response.json()['errors'][0]['message'] == Messages.field_required()

    def test_retrieve_collection_success(self, api_client, collections_table):
        """
        Tests successful retrieval of a single collection by ID.
        """
        collection_id = int(collections_table[0].id)
        with patch(
            'collections_api.api.views.collections_by_id_view.CollectionsByIdView.api_key.authenticate',
            return_value=(self.test_user, self.test_key)
        ):
            response = api_client.get(f"{self.__get_url()}{collection_id}")

        assert response.status_code == status.HTTP_200_OK
        assert response.json()['success'] is True
        assert response.json()['message'] == Messages.retrieved_successfully()
        assert response.json()['errors'] is None
        assert response.json()['data']['name'] == collections_table[0].name

    def test_retrieve_collection_not_found(self, api_client):
        """
        Tests retrieving a collection that does not exist.
        """
        with patch(
            'collections_api.api.views.collections_by_id_view.CollectionsByIdView.api_key.authenticate',
            return_value=(self.test_user, self.test_key)
        ):
            response = api_client.get(f"{self.__get_url()}999")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()['success'] is False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] is None
        assert response.json()['errors'][0]['code'] == Messages.Code.other()
        assert response.json()['errors'][0]['message'] == Messages.Get.not_found("collection", "999")

    def test_update_collection_success(self, api_client, collections_table, collection_put_payload_ok):
        """
        Tests successful update of an existing collection.
        """
        collection_id = collections_table[0].id
        with patch(
            'collections_api.api.views.collections_by_id_view.CollectionsByIdView.api_key.authenticate',
            return_value=(self.test_user, self.test_key)
        ):
            response = api_client.put(f"{self.__get_url()}{collection_id}", collection_put_payload_ok)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['success'] is True
        assert response.json()['message'] == Messages.updated_successfully()
        assert response.json()['errors'] is None
        assert response.json()['data']['name'] == collection_put_payload_ok['name']
        
    def test_update_collection_bad_request(self, api_client, collections_table, collection_put_payload_ok):
        """
        Tests updating a collection item with a missing 'stamp' field.
        """
        collection_put_payload_ok["new_field"]="new_value"
        item_id = collections_table[0].id
        with patch(
            'collections_api.api.views.collections_by_id_view.CollectionsByIdView.api_key.authenticate',
            return_value=(self.test_user, self.test_key)
        ):
            response = api_client.put(f"{self.__get_url()}{item_id}", collection_put_payload_ok)

        assert response.json()['data'] == None
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['errors'][0]['message'] == Messages.field_not_allowed()
        assert response.json()['errors'][0]['code'] == Messages.Code.invalid()
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()['errors'][0]['field'] == "new_field"

    def test_update_collection_not_found(self, api_client, collection_put_payload_ok):
        """
        Tests updating a collection that does not exist.
        """
        with patch(
            'collections_api.api.views.collections_by_id_view.CollectionsByIdView.api_key.authenticate',
            return_value=(self.test_user, self.test_key)
        ):
            response = api_client.put(f"{self.__get_url()}999", collection_put_payload_ok)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()['success'] is False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] is None
        assert response.json()['errors'][0]['message'] == Messages.Put.not_found("collection", "999")
    
    def test_delete_collection_success(self, api_client, collections_table):
        """
        Tests successful deletion of a collection.
        """
        collection_id = collections_table[0].id
        with patch(
            'collections_api.api.views.collections_by_id_view.CollectionsByIdView.api_key.authenticate',
            return_value=(self.test_user, self.test_key)
        ):
            response = api_client.delete(f"{self.__get_url()}{collection_id}")
        
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['success'] is True
        assert response.json()['message'] == Messages.deleted_successfully()
        assert response.json()['errors'] is None
        assert response.json()['data']['message'] == Messages.Delete.deleted_one("collection", str(collection_id))

    def test_delete_collection_not_found(self, api_client):
        """
        Tests deleting a collection that does not exist.
        """
        with patch(
            'collections_api.api.views.collections_by_id_view.CollectionsByIdView.api_key.authenticate',
            return_value=(self.test_user, self.test_key)
        ):
            response = api_client.delete(f"{self.__get_url()}999")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()['success'] is False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] is None
        assert response.json()['errors'][0]['message'] == Messages.Delete.not_found("collection", "999")
        
    @patch('collections_api.api.views.collections_by_id_view.Collection.objects.get')
    def test_delete_collection_database_error(self, mock_get, api_client, collections_table):
        """
        Tests deleting a collection when a database error occurs.
        """
        collection_id = collections_table[0].id
        mock_get.side_effect = Exception("Database connection lost")
        with patch(
            'collections_api.api.views.collections_by_id_view.CollectionsByIdView.api_key.authenticate',
            return_value=(self.test_user, self.test_key)
        ):
            response = api_client.delete(f"{self.__get_url()}{collection_id}")

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.json()['success'] is False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['errors'][0]['message'] == Messages.server_error()
        
    def test_delete_collection_auth_error(self, api_client, collections_table):
        """
        Tests deleting a collection when authentication fails.
        """
        response = api_client.delete(f"{self.__get_url()}999")
        
        assert response.status_code == status.HTTP_403_FORBIDDEN

        
    def test_collection_model_str_representation(self):
        """
        Tests the string representation of the Collection model.
        """
        test_name = "My Test Collection"
        collection = Collection.objects.create(
            name=test_name,
            user=self.test_user
        )
        
        assert str(collection) ==  f"{self.test_user} - {test_name}"
        
    def __get_url(self):
        return f"/{COLLECTIONS_URL_V1}"