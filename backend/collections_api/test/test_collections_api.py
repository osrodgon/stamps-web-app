import pytest
from rest_framework import status

from _backend.settings import COLLECTIONS_URL_V1
from collections_api.api.serializers.collection_response_serializer import CollectionResponseSerializer
from collections_api.models import Collection
from common import api
from common.api.messages import Messages
from common.test.abstract_api_unit_test import AbstractApiUnitTest
from common.test.api_client import api_client # api_client == needed for other fixtures
from common.test.collections_api_test_data import (
    collections_table,
    collection_post_payload_ok,
    collection_put_payload_ok,
)
from common.test.users_api_test_data import users_table
from users_api.models import UserCollection



@pytest.mark.django_db
class TestCollectionsAPI(AbstractApiUnitTest):
    def test_get_all_collections_returns_200_ok_data(self, api_client, collections_table, users_table):
        self.permission(granted=True)
        response = api_client.get(self.__get_url())

        original = CollectionResponseSerializer(collections_table, many=True)

        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.retrieved_successfully()
        assert response.json()['errors'] == None
        assert len(response.json()['data']) == len(collections_table)
        assert response.json()['data'] == original.data
        assert response.status_code == status.HTTP_200_OK

    def test_get_all_collections_returns_200_ok_no_data(self, api_client):
        self.permission(granted=True)
        response = api_client.get(self.__get_url())

        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.retrieved_successfully()
        assert response.json()['errors'] == None
        assert len(response.json()['data']) == 0
        assert response.status_code == status.HTTP_200_OK

    def test_get_all_collections_returns_403_invalid_key(self, api_client):
        self.permission(granted=False, message=Messages.APIKey.invalid_key())
        response = api_client.get(self.__get_url())

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.APIKey.invalid_key()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_all_collections_returns_403_invalid_user(self, api_client):
        self.permission(granted=False, message=Messages.APIKey.invalid_user())
        response = api_client.get(self.__get_url())

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.APIKey.invalid_user()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
    def test_get_all_collections_returns_500_database_error_connection_lost(self, api_client):
        self.permission(granted=True)
        self.connection_lost(Collection, self.GET_ALL)
        response = api_client.get(self.__get_url())

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Database.connection_lost()
        assert response.json()['errors'][0]['code'] == Messages.Code.connection_lost()
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_post_collection_returns_201_created(self, api_client, collection_post_payload_ok):
        self.permission(granted=True)
        self.get_name()
        self.get_user()
        response = api_client.post(self.__get_url(), collection_post_payload_ok, format='json')

        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.created_successfully()
        assert response.json()['errors'] == None
        assert response.json()['data']['name'] == collection_post_payload_ok['name']
        assert response.status_code == status.HTTP_201_CREATED

    def test_post_collection_returns_400_missing_field(self, api_client, collection_post_payload_ok):
        self.permission(granted=True)
        self.get_name()
        self.get_user()
        del collection_post_payload_ok['name']
        response = api_client.post(self.__get_url(), collection_post_payload_ok, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'name'
        assert response.json()['errors'][0]['message'] == Messages.field_required()
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_post_collection_returns_400_invalid_field(self, api_client, collection_post_payload_ok):
        self.permission(granted=True)
        self.get_name()
        self.get_user()
        collection_post_payload_ok['new_field'] = 'new_value'
        response = api_client.post(self.__get_url(), collection_post_payload_ok, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'new_field'
        assert response.json()['errors'][0]['message'] == Messages.field_not_allowed()
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_post_collection_returns_403_invalid_key(self, api_client, collection_post_payload_ok):
        self.permission(granted=False, message=Messages.APIKey.invalid_key())
        response = api_client.post(self.__get_url(), collection_post_payload_ok, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.APIKey.invalid_key()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_post_collection_returns_403_invalid_user(self, api_client, collection_post_payload_ok):
        self.permission(granted=False, message=Messages.APIKey.invalid_user())
        response = api_client.post(self.__get_url(), collection_post_payload_ok, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.APIKey.invalid_user()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
    def test_post_collection_returns_404_not_found(self, api_client, collection_post_payload_ok):
        self.permission(granted=True)
        self.get_name()
        response = api_client.post(self.__get_url(), collection_post_payload_ok, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == None
        assert response.json()['errors'][0]['message'] == Messages.Database.unknow_user()
        assert response.json()['errors'][0]['code'] == Messages.Code.other()   
        assert response.status_code == status.HTTP_404_NOT_FOUND


    def test_post_collection_returns_500_database_error_connection_lost(self, api_client, collection_post_payload_ok):
        self.permission(granted=True)
        self.get_name()
        self.get_user()
        self.connection_lost(Collection, self.POST)
        response = api_client.post(self.__get_url(), collection_post_payload_ok, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Database.connection_lost()
        assert response.json()['errors'][0]['code'] == Messages.Code.connection_lost()
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_get_one_collection_returns_200_ok(self, api_client, collections_table):
        self.permission(granted=True)
        collection_id = collections_table[0].id
        response = api_client.get(f"{self.__get_url()}{collection_id}")

        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.retrieved_successfully()
        assert response.json()['errors'] == None
        assert response.json()['data']['name'] == collections_table[0].name
        assert response.status_code == status.HTTP_200_OK

    def test_get_one_collection_returns_403_invalid_key(self, api_client, collections_table):
        self.permission(granted=False, message=Messages.APIKey.invalid_key())
        collection_id = collections_table[0].id
        response = api_client.get(f"{self.__get_url()}{collection_id}")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.APIKey.invalid_key()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_one_collection_returns_403_invalid_user(self, api_client, collections_table):
        self.permission(granted=False, message=Messages.APIKey.invalid_user())
        collection_id = collections_table[0].id
        response = api_client.get(f"{self.__get_url()}{collection_id}")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.APIKey.invalid_user()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_one_collection_returns_404_not_found(self, api_client):
        self.permission(granted=True)
        response = api_client.get(f"{self.__get_url()}999")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['message'] == Messages.Get.not_found("collection", "999")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_one_collection_returns_500_database_error_connection_lost(self, api_client, collections_table):
        self.permission(granted=True)
        self.connection_lost(Collection, self.GET_ONE)
        collection_id = collections_table[0].id
        response = api_client.get(f"{self.__get_url()}{collection_id}")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Database.connection_lost()
        assert response.json()['errors'][0]['code'] == Messages.Code.connection_lost()
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_put_collection_returns_200_ok(self, api_client, collections_table, collection_put_payload_ok):
        self.permission(granted=True)
        collection_id = collections_table[0].id
        response = api_client.put(f"{self.__get_url()}{collection_id}", collection_put_payload_ok, format='json')

        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.updated_successfully()
        assert response.json()['errors'] == None
        assert response.json()['data']['name'] == collection_put_payload_ok['name']
        assert response.status_code == status.HTTP_200_OK

    def test_put_collection_returns_400_invalid_field(self, api_client, collections_table, collection_put_payload_ok):
        self.permission(granted=True)
        collection_id = collections_table[0].id
        collection_put_payload_ok['new_field'] = 'new_value'
        response = api_client.put(f"{self.__get_url()}{collection_id}", collection_put_payload_ok, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['message'] == Messages.field_not_allowed()
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_put_collection_returns_403_invalid_key(self, api_client, collections_table, collection_put_payload_ok):
        self.permission(granted=False, message=Messages.APIKey.invalid_key())
        collection_id = collections_table[0].id
        response = api_client.put(f"{self.__get_url()}{collection_id}", collection_put_payload_ok, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.APIKey.invalid_key()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_put_collection_returns_403_invalid_user(self, api_client, collections_table, collection_put_payload_ok):
        self.permission(granted=False, message=Messages.APIKey.invalid_user())
        collection_id = collections_table[0].id
        response = api_client.put(f"{self.__get_url()}{collection_id}", collection_put_payload_ok, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.APIKey.invalid_user()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_put_collection_returns_404_not_found(self, api_client, collection_put_payload_ok):
        self.permission(granted=True)
        response = api_client.put(f"{self.__get_url()}999", collection_put_payload_ok, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['message'] == Messages.Put.not_found("collection", "999")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_put_collection_returns_500_database_error_connection_lost(self, api_client, collections_table, collection_put_payload_ok):
        self.permission(granted=True)
        self.connection_lost(Collection, self.PUT)
        collection_id = collections_table[0].id
        response = api_client.put(f"{self.__get_url()}{collection_id}", collection_put_payload_ok, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Database.connection_lost()
        assert response.json()['errors'][0]['code'] == Messages.Code.connection_lost()
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_delete_collection_returns_200_ok(self, api_client, collections_table):
        self.permission(granted=True)
        collection_id = collections_table[0].id
        response = api_client.delete(f"{self.__get_url()}{collection_id}")

        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.deleted_successfully()
        assert response.json()['errors'] == None
        assert response.json()['data']['message'] == Messages.Delete.deleted_one("collection", str(collection_id))
        assert response.status_code == status.HTTP_200_OK

    def test_delete_collection_returns_403_invalid_key(self, api_client, collections_table):
        self.permission(granted=False, message=Messages.APIKey.invalid_key())
        collection_id = collections_table[0].id
        response = api_client.delete(f"{self.__get_url()}{collection_id}")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.APIKey.invalid_key()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_collection_returns_403_invalid_user(self, api_client, collections_table):
        self.permission(granted=False, message=Messages.APIKey.invalid_user())
        collection_id = collections_table[0].id
        response = api_client.delete(f"{self.__get_url()}{collection_id}")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.APIKey.invalid_user()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_collection_returns_404_not_found(self, api_client):
        self.permission(granted=True)
        response = api_client.delete(f"{self.__get_url()}999")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['message'] == Messages.Delete.not_found("collection", "999")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_collection_returns_500_database_error_connection_lost(self, api_client, collections_table):
        self.permission(granted=True)
        self.connection_lost(Collection, self.DELETE)
        collection_id = collections_table[0].id
        response = api_client.delete(f"{self.__get_url()}{collection_id}")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Database.connection_lost()
        assert response.json()['errors'][0]['code'] == Messages.Code.connection_lost()
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_collection_model_str_representation(self):
        test_name = "My Test Collection"
        user = UserCollection.objects.create(
            username="testuser1",
            email="test1@example.com",
            password_hash="fake_hash_xas1sasas",
            first_name="Test",
            last_name="UserOne"
        )

        collection = Collection.objects.create(
            name=test_name,
            user=user
        )

        assert str(collection) == f"{user.username} - {test_name}"

    def __get_url(self):
        return f"/{COLLECTIONS_URL_V1}"