from unittest.mock import patch
from urllib import response
import pytest
from rest_framework import status

from _backend.settings import COLLECTION_ITEMS_URL_V1
from collection_items_api.api.serializers.collection_items_response_serializer import CollectionItemsResponseSerializer
from collection_items_api.models import CollectionItem
from common.api.messages import Messages
from common.test.api_client import api_client
from common.test.collection_items_api_test_data import (
    collection_items_table,
    collection_item_post_payload_ok,
    collection_item_put_payload_ok,
)
from common.test.collections_api_test_data import collections_table
from common.test.year_api_test_data import years_table
from common.test.countries_api_test_data import countries_table
from common.test.stamp_types_api_test_data import stamp_types_table
from common.test.paper_types_api_test_data import paper_types_table
from common.test.locations_api_test_data import locations_table
from common.test.issues_api_test_data import issues_table
from common.test.colors_api_test_data import colors_table
from common.test.stamps_api_test_data import stamps_table


@pytest.mark.django_db
class TestCollectionItemsAPI:
    """
    Test suite for the Collection Items API endpoints.
    """
    test_user = "test_user"
    test_key = "test_key"

    def test_list_collection_items_success(self, api_client, collection_items_table):
        """
        Tests successful retrieval of a list of collection items.
        """
        response = api_client.get(self.__get_url())

        original = CollectionItemsResponseSerializer(collection_items_table, many=True)

        assert response.status_code == status.HTTP_200_OK
        assert response.json()['data'] == original.data
        assert len(response.json()['data']) == len(collection_items_table)

    def test_list_collection_items_empty(self, api_client):
        """
        Tests retrieval of an empty list of collection items.
        """
        response = api_client.get(self.__get_url())

        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()['data']) == 0

    def test_create_collection_item_success(self, api_client, collections_table, stamps_table, collection_item_post_payload_ok):
        """
        Tests successful creation of a new collection item.
        """
        response = api_client.post(self.__get_url(), collection_item_post_payload_ok)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()['data']['collection']['id'] == collection_item_post_payload_ok['collection']
        assert response.json()['data']['stamp']['id'] == collection_item_post_payload_ok['stamp']

    def test_create_collection_item_missing_field(self, api_client, collection_item_post_payload_ok):
        """
        Tests creating a collection item with a missing 'stamp' field.
        """
        del collection_item_post_payload_ok['stamp']
        response = api_client.post(self.__get_url(), collection_item_post_payload_ok)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()['errors'][0]['field'] == "stamp"

    def test_create_collection_item_duplicate(self, api_client, collection_items_table):
        """
        Tests creating a collection item that already exists (duplicate).
        """
        payload = {
            "collection": collection_items_table[0].collection.id,
            "stamp": collection_items_table[0].stamp.id
        }
        response = api_client.post(self.__get_url(), payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()['errors'][0]['code'] == 'unique'

    def test_retrieve_collection_item_success(self, api_client, collection_items_table):
        """
        Tests successful retrieval of a single collection item by ID.
        """
        item_id = collection_items_table[0].id
        response = api_client.get(f"{self.__get_url()}{item_id}")

        assert response.status_code == status.HTTP_200_OK
        assert response.json()['data']['id'] == item_id

    def test_retrieve_collection_item_not_found(self, api_client):
        """
        Tests retrieving a collection item that does not exist.
        """
        response = api_client.get(f"{self.__get_url()}999")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()['errors'][0]['message'] == Messages.Get.not_found("collection item", "999")

    def test_update_collection_item_success(self, api_client, collection_items_table, collection_item_put_payload_ok):
        """
        Tests successful update of an existing collection item.
        """
        item_id = collection_items_table[0].id
        response = api_client.put(f"{self.__get_url()}{item_id}", collection_item_put_payload_ok)

        assert response.status_code == status.HTTP_200_OK
        # This field is not in the payload, so it should not change
        assert response.json()['data']['collection']['id'] == collection_items_table[0].collection.id
        
    def test_update_collection_item_bad_request(self, api_client, collection_items_table, collection_item_put_payload_ok):
        """
        Tests updating a collection item with a missing 'stamp' field.
        """
        collection_item_put_payload_ok["new_field"]="new_value"
        item_id = collection_items_table[0].id
        response = api_client.put(f"{self.__get_url()}{item_id}", collection_item_put_payload_ok)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()['errors'][0]['field'] == "new_field"

    def test_update_collection_item_not_found(self, api_client, collection_item_put_payload_ok):
        """
        Tests updating a collection item that does not exist.
        """
        response = api_client.put(f"{self.__get_url()}999", collection_item_put_payload_ok)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()['errors'][0]['message'] == Messages.Put.not_found("collection item", "999")

    def test_delete_collection_item_success(self, api_client, collection_items_table):
        """
        Tests successful deletion of a collection item.
        """
        item_id = collection_items_table[0].id
        response = api_client.delete(f"{self.__get_url()}{item_id}")

        assert response.status_code == status.HTTP_200_OK

    def test_delete_collection_item_not_found(self, api_client):
        """
        Tests deleting a collection item that does not exist.
        """
        response = api_client.delete(f"{self.__get_url()}999")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()['errors'][0]['message'] == Messages.Delete.not_found("collection item", "999")

    @patch('collection_items_api.api.views.collection_items_by_id_view.CollectionItem.objects.get')
    def test_delete_collection_item_database_error(self, mock_get, api_client, collection_items_table):
        """
        Tests deleting a collection item when a database error occurs.
        """
        item_id = collection_items_table[0].id
        mock_get.side_effect = Exception("Database connection lost")
        response = api_client.delete(f"{self.__get_url()}{item_id}")

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.json()['errors'][0]['message'] == Messages.server_error()
        
    def test_delete_collection_item_access_denied(self, api_client, collection_items_table):
        """
        Tests deleting a collection item when access is denied.
        """
        item_id = collection_items_table[0].id
        response = api_client.delete(f"{self.__get_url()}{item_id}")

        assert response.status_code == status.HTTP_403_FORBIDDEN
        
    def test_collection_item_model_str_representation(self, collections_table, stamps_table):
        """
        Tests the string representation of the CollectionItem model.
        """
        collection_item = CollectionItem.objects.create(
            collection=collections_table[0],
            stamp=stamps_table[0]
        )

        assert str(collection_item) == f"{collections_table[0].user} - {stamps_table[0].name}"


    def __get_url(self):
        return f"/{COLLECTION_ITEMS_URL_V1}"