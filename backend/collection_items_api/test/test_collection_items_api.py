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
from common.test.abstract_api_unit_test import AbstractApiUnitTest
from common.test.stamps_api_test_data import stamps_table
from common.test.issues_api_test_data import issues_table
from common.test.countries_api_test_data import countries_table
from common.test.stamp_types_api_test_data import stamp_types_table
from common.test.paper_types_api_test_data import paper_types_table
from common.test.locations_api_test_data import locations_table
from common.test.year_api_test_data import years_table
from common.test.colors_api_test_data import colors_table
from common.test.users_api_test_data import users_table
from common.test.condition_types_api_test_data import condition_types_table

@pytest.mark.django_db
class TestCollectionItemsAPI(AbstractApiUnitTest):
    def test_get_all_collection_items_returns_200_ok_data(self, api_client, collection_items_table):
        self.permission(granted=True)
        response = api_client.get(self.__get_url())

        original = CollectionItemsResponseSerializer(collection_items_table, many=True)

        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.retrieved_successfully()
        assert response.json()['errors'] == None
        assert len(response.json()['data']) == len(collection_items_table)
        assert response.json()['data'] == original.data
        assert response.status_code == status.HTTP_200_OK

    def test_get_all_collection_items_returns_200_ok_no_data(self, api_client):
        self.permission(granted=True)
        response = api_client.get(self.__get_url())

        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.retrieved_successfully()
        assert response.json()['errors'] == None
        assert len(response.json()['data']) == 0
        assert response.status_code == status.HTTP_200_OK

    def test_get_all_collection_items_returns_403_invalid_key(self, api_client):
        self.permission(granted=False, message=Messages.APIKey.invalid_key())
        response = api_client.get(self.__get_url())

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.APIKey.invalid_key()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_all_collection_items_returns_403_invalid_user(self, api_client):
        self.permission(granted=False, message=Messages.APIKey.invalid_user())
        response = api_client.get(self.__get_url())

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.APIKey.invalid_user()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_all_collection_items_returns_500_database_error_connection_lost(self, api_client):
        self.permission(granted=True)
        self.connection_lost(CollectionItem, self.GET_ALL)
        response = api_client.get(self.__get_url())

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Database.connection_lost()
        assert response.json()['errors'][0]['code'] == Messages.Code.connection_lost()
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_post_collection_item_returns_201_created(self, api_client, collections_table, stamps_table, locations_table, collection_item_post_payload_ok):
        self.permission(granted=True)
        response = api_client.post(self.__get_url(), collection_item_post_payload_ok, format='json')

        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.created_successfully()
        assert response.json()['errors'] == None
        assert response.json()['data']['location'] is not None
        assert response.json()['data']['location']['id'] == collection_item_post_payload_ok['location']
        assert response.json()['data']['collection']['id'] == collection_item_post_payload_ok['collection']
        assert response.json()['data']['stamp']['id'] == collection_item_post_payload_ok['stamp']
        assert response.status_code == status.HTTP_201_CREATED
        
    def test_post_collection_item_returns_400_missing_field(self, api_client, collection_item_post_payload_ok):
        del collection_item_post_payload_ok['stamp']
        self.permission(granted=True)
        response = api_client.post(self.__get_url(), collection_item_post_payload_ok, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == "stamp"
        assert response.json()['errors'][0]['message'] == Messages.field_required()
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_post_collection_item_returns_400_invalid_field(self, api_client, collection_item_post_payload_ok):
        collection_item_post_payload_ok['new_field'] = 'new_value'
        self.permission(granted=True)
        response = api_client.post(self.__get_url(), collection_item_post_payload_ok, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == "new_field"
        assert response.json()['errors'][0]['message'] == Messages.field_not_allowed()
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_post_collection_item_returns_403_invalid_key(self, api_client, collection_item_post_payload_ok):
        self.permission(granted=False, message=Messages.APIKey.invalid_key())
        response = api_client.post(self.__get_url(), collection_item_post_payload_ok, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.APIKey.invalid_key()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_post_collection_item_returns_403_invalid_user(self, api_client, collection_item_post_payload_ok):
        self.permission(granted=False, message=Messages.APIKey.invalid_user())
        response = api_client.post(self.__get_url(), collection_item_post_payload_ok, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.APIKey.invalid_user()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_post_collection_item_returns_500_database_error_connection_lost(self, api_client, collection_item_post_payload_ok):
        self.permission(granted=True)
        self.connection_lost(CollectionItem, self.POST)
        response = api_client.post(self.__get_url(), collection_item_post_payload_ok, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Database.connection_lost()
        assert response.json()['errors'][0]['code'] == Messages.Code.connection_lost()
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_get_one_collection_item_returns_200_ok(self, api_client, collection_items_table):
        self.permission(granted=True)
        item_id = collection_items_table[0].id
        response = api_client.get(f"{self.__get_url()}{item_id}")

        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.retrieved_successfully()
        assert response.json()['errors'] == None
        assert response.json()['data']['id'] == item_id
        assert response.status_code == status.HTTP_200_OK

    def test_get_one_collection_item_returns_403_invalid_key(self, api_client, collection_items_table):
        self.permission(granted=False, message=Messages.APIKey.invalid_key())
        item_id = collection_items_table[0].id
        response = api_client.get(f"{self.__get_url()}{item_id}")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.APIKey.invalid_key()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_one_collection_item_returns_403_invalid_user(self, api_client, collection_items_table):
        self.permission(granted=False, message=Messages.APIKey.invalid_user())
        item_id = collection_items_table[0].id
        response = api_client.get(f"{self.__get_url()}{item_id}")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.APIKey.invalid_user()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_one_collection_item_returns_404_not_found(self, api_client):
        self.permission(granted=True)
        response = api_client.get(f"{self.__get_url()}999")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['message'] == Messages.Get.not_found("collection item", "999")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_one_collection_item_returns_500_database_error_connection_lost(self, api_client, collection_items_table):
        self.permission(granted=True)
        self.connection_lost(CollectionItem, self.GET_ONE)
        item_id = collection_items_table[0].id
        response = api_client.get(f"{self.__get_url()}{item_id}")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Database.connection_lost()
        assert response.json()['errors'][0]['code'] == Messages.Code.connection_lost()
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_put_collection_item_returns_200_ok(self, api_client, collection_items_table, collection_item_put_payload_ok):
        item_id = collection_items_table[0].id
        self.permission(granted=True)
        response = api_client.put(f"{self.__get_url()}{item_id}", collection_item_put_payload_ok, format='json')

        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.updated_successfully()
        assert response.json()['errors'] == None
        assert response.json()['data']['collection']['id'] == collection_items_table[0].collection.id
        assert response.json()['data']['price_paid'] == collection_item_put_payload_ok['price_paid']
        assert response.json()['data']['note'] == collection_item_put_payload_ok['note']
        assert response.status_code == status.HTTP_200_OK

    def test_put_collection_item_returns_400_invalid_field(self, api_client, collection_items_table, collection_item_put_payload_ok):
        collection_item_put_payload_ok["new_field"] = "new_value"
        item_id = collection_items_table[0].id
        self.permission(granted=True)
        response = api_client.put(f"{self.__get_url()}{item_id}", collection_item_put_payload_ok, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == "new_field"
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_put_collection_item_returns_403_invalid_key(self, api_client, collection_items_table, collection_item_put_payload_ok):
        self.permission(granted=False, message=Messages.APIKey.invalid_key())
        item_id = collection_items_table[0].id
        response = api_client.put(f"{self.__get_url()}{item_id}", collection_item_put_payload_ok, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.APIKey.invalid_key()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_put_collection_item_returns_403_invalid_user(self, api_client, collection_items_table, collection_item_put_payload_ok):
        self.permission(granted=False, message=Messages.APIKey.invalid_user())
        item_id = collection_items_table[0].id
        response = api_client.put(f"{self.__get_url()}{item_id}", collection_item_put_payload_ok, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.APIKey.invalid_user()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_put_collection_item_returns_404_not_found(self, api_client, collection_item_put_payload_ok):
        self.permission(granted=True)
        response = api_client.put(f"{self.__get_url()}999", collection_item_put_payload_ok, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['message'] == Messages.Put.not_found("collection item", "999")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_put_collection_item_returns_500_database_error_connection_lost(self, api_client, collection_items_table, collection_item_put_payload_ok):
        self.permission(granted=True)
        self.connection_lost(CollectionItem, self.PUT)
        item_id = collection_items_table[0].id
        response = api_client.put(f"{self.__get_url()}{item_id}", collection_item_put_payload_ok, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Database.connection_lost()
        assert response.json()['errors'][0]['code'] == Messages.Code.connection_lost()
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_delete_collection_item_returns_200_ok(self, api_client, collection_items_table):
        item_id = collection_items_table[0].id
        self.permission(granted=True)
        response = api_client.delete(f"{self.__get_url()}{item_id}")

        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.deleted_successfully()
        assert response.json()['errors'] == None
        assert response.json()['data']['message'] == Messages.Delete.deleted_one("collection item", item_id)
        assert response.status_code == status.HTTP_200_OK

    def test_delete_collection_item_returns_403_invalid_key(self, api_client, collection_items_table):
        self.permission(granted=False, message=Messages.APIKey.invalid_key())
        item_id = collection_items_table[0].id
        response = api_client.delete(f"{self.__get_url()}{item_id}")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.APIKey.invalid_key()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_collection_item_returns_403_invalid_user(self, api_client, collection_items_table):
        self.permission(granted=False, message=Messages.APIKey.invalid_user())
        item_id = collection_items_table[0].id
        response = api_client.delete(f"{self.__get_url()}{item_id}")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.APIKey.invalid_user()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_collection_item_returns_404_not_found(self, api_client):
        self.permission(granted=True)
        response = api_client.delete(f"{self.__get_url()}999")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['message'] == Messages.Delete.not_found("collection item", "999")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_collection_item_returns_500_database_error_connection_lost(self, api_client, collection_items_table):
        self.permission(granted=True)
        self.connection_lost(CollectionItem, self.DELETE)
        item_id = collection_items_table[0].id
        response = api_client.delete(f"{self.__get_url()}{item_id}")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Database.connection_lost()
        assert response.json()['errors'][0]['code'] == Messages.Code.connection_lost()
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

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