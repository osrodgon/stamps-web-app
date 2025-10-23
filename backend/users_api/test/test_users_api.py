import pytest
from rest_framework import status
from django.contrib.auth.hashers import check_password

from _backend.settings import USERS_URL_V1
from common.api.messages import Messages
from common.test.abstract_api_unit_test import AbstractApiUnitTest
from common.test.api_client import api_client
from common.test.users_api_test_data import (
    users_table,
    user_post_payload_ok,
    user_put_payload_ok
)
from users_api.models import UserCollection
from users_api.api.serializers.user_response_serializer import UserResponseSerializer


@pytest.mark.django_db
class TestUsersAPI(AbstractApiUnitTest):
    def test_get_all_users_returns_200_ok_data(self, api_client, users_table):
        self.permission(granted=True)
        response = api_client.get(self.__get_url())

        original = UserResponseSerializer(users_table, many=True)

        assert response.json()['success'] is True
        assert response.json()['message'] == Messages.retrieved_successfully()
        assert response.json()['errors'] is None
        assert len(response.json()['data']) == len(original.data)
        assert response.json()['data'] == original.data
        assert response.status_code == status.HTTP_200_OK

    def test_get_all_users_returns_200_ok_no_data(self, api_client):
        self.permission(granted=True)
        response = api_client.get(self.__get_url())

        assert response.json()['success'] is True
        assert response.json()['message'] == Messages.retrieved_successfully()
        assert response.json()['errors'] is None
        assert len(response.json()['data']) == 0
        assert response.status_code == status.HTTP_200_OK

    def test_get_all_users_returns_403_invalid_key(self, api_client):
        self.permission(granted=False, message=Messages.APIKey.invalid_key())
        response = api_client.get(self.__get_url())

        assert response.json()['success'] is False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] is None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.APIKey.invalid_key()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_all_users_returns_403_invalid_user(self, api_client):
        self.permission(granted=False, message=Messages.APIKey.invalid_user())
        response = api_client.get(self.__get_url())

        assert response.json()['success'] is False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] is None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.APIKey.invalid_user()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_all_users_returns_500_database_error_connection_lost(self, api_client):
        self.permission(granted=True)
        self.connection_lost(UserCollection, self.GET_ALL)
        response = api_client.get(self.__get_url())

        assert response.json()['success'] is False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] is None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Database.connection_lost()
        assert response.json()['errors'][0]['code'] == Messages.Code.connection_lost()
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_post_user_returns_201_created(self, api_client, user_post_payload_ok):
        self.permission(granted=True)
        response = api_client.post(self.__get_url(), user_post_payload_ok, format='json')

        assert response.json()['success'] is True
        assert response.json()['message'] == Messages.created_successfully()
        assert response.json()['errors'] is None
        assert response.json()['data']['username'] == user_post_payload_ok["username"]
        assert response.status_code == status.HTTP_201_CREATED
        
        created_user = UserCollection.objects.get(id=response.json()['data']['id'])
        assert check_password(user_post_payload_ok['password'], created_user.password_hash)

    def test_post_user_returns_400_missing_field(self, api_client, user_post_payload_ok):
        self.permission(granted=True)
        del user_post_payload_ok["username"]
        response = api_client.post(self.__get_url(), user_post_payload_ok, format='json')

        assert response.json()['success'] is False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] is None
        assert response.json()['errors'][0]['field'] == "username"
        assert response.json()['errors'][0]['message'] == Messages.field_required()
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_post_user_returns_400_invalid_field(self, api_client, user_post_payload_ok):
        self.permission(granted=True)
        user_post_payload_ok['new_field'] = 'new_value'
        response = api_client.post(self.__get_url(), user_post_payload_ok, format='json')

        assert response.json()['success'] is False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] is None
        assert response.json()['errors'][0]['field'] == "new_field"
        assert response.json()['errors'][0]['message'] == Messages.field_not_allowed()
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_post_user_returns_403_invalid_key(self, api_client, user_post_payload_ok):
        self.permission(granted=False, message=Messages.APIKey.invalid_key())
        response = api_client.post(self.__get_url(), user_post_payload_ok, format='json')

        assert response.json()['success'] is False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] is None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.APIKey.invalid_key()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_post_user_returns_403_invalid_user(self, api_client, user_post_payload_ok):
        self.permission(granted=False, message=Messages.APIKey.invalid_user())
        response = api_client.post(self.__get_url(), user_post_payload_ok, format='json')

        assert response.json()['success'] is False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] is None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.APIKey.invalid_user()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_post_user_returns_500_database_error_connection_lost(self, api_client, user_post_payload_ok):
        self.permission(granted=True)
        self.connection_lost(UserCollection, self.POST)
        response = api_client.post(self.__get_url(), user_post_payload_ok, format='json')

        assert response.json()['success'] is False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] is None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Database.connection_lost()
        assert response.json()['errors'][0]['code'] == Messages.Code.connection_lost()
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_get_one_user_returns_200_ok(self, api_client, users_table):
        self.permission(granted=True)
        user_id = users_table[0].id
        response = api_client.get(f"{self.__get_url()}{user_id}")

        assert response.json()['success'] is True
        assert response.json()['message'] == Messages.retrieved_successfully()
        assert response.json()['errors'] is None
        assert response.json()['data']['username'] == users_table[0].username
        assert response.status_code == status.HTTP_200_OK

    def test_get_one_user_returns_403_invalid_key(self, api_client, users_table):
        self.permission(granted=False, message=Messages.APIKey.invalid_key())
        user_id = users_table[0].id
        response = api_client.get(f"{self.__get_url()}{user_id}")

        assert response.json()['success'] is False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] is None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.APIKey.invalid_key()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_one_user_returns_403_invalid_user(self, api_client, users_table):
        self.permission(granted=False, message=Messages.APIKey.invalid_user())
        user_id = users_table[0].id
        response = api_client.get(f"{self.__get_url()}{user_id}")

        assert response.json()['success'] is False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] is None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.APIKey.invalid_user()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_one_user_returns_404_not_found(self, api_client):
        self.permission(granted=True)
        response = api_client.get(f"{self.__get_url()}999")

        assert response.json()['success'] is False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] is None
        assert response.json()['errors'][0]['message'] == Messages.Get.not_found("collection user", "999")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_one_user_returns_500_database_error_connection_lost(self, api_client, users_table):
        self.permission(granted=True)
        self.connection_lost(UserCollection, self.GET_ONE)
        user_id = users_table[0].id
        response = api_client.get(f"{self.__get_url()}{user_id}")

        assert response.json()['success'] is False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] is None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Database.connection_lost()
        assert response.json()['errors'][0]['code'] == Messages.Code.connection_lost()
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_put_user_returns_200_ok(self, api_client, users_table, user_put_payload_ok):
        self.permission(granted=True)
        user_id = users_table[0].id
        response = api_client.put(f"{self.__get_url()}{user_id}", user_put_payload_ok, format='json')

        assert response.json()['success'] is True
        assert response.json()['message'] == Messages.updated_successfully()
        assert response.json()['errors'] is None
        assert response.json()['data']['username'] == user_put_payload_ok["username"]
        assert response.status_code == status.HTTP_200_OK

        updated_user = UserCollection.objects.get(id=user_id)
        assert check_password(user_put_payload_ok['password'], updated_user.password_hash)

    def test_put_user_returns_400_invalid_field(self, api_client, users_table, user_put_payload_ok):
        self.permission(granted=True)
        user_id = users_table[0].id
        user_put_payload_ok["new_field"] = "new_value"
        response = api_client.put(f"{self.__get_url()}{user_id}", user_put_payload_ok, format='json')

        assert response.json()['success'] is False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] is None
        assert response.json()['errors'][0]['field'] == "new_field"
        assert response.json()['errors'][0]['message'] == Messages.field_not_allowed()
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_put_user_returns_403_invalid_key(self, api_client, users_table, user_put_payload_ok):
        self.permission(granted=False, message=Messages.APIKey.invalid_key())
        user_id = users_table[0].id
        response = api_client.put(f"{self.__get_url()}{user_id}", user_put_payload_ok, format='json')

        assert response.json()['success'] is False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] is None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.APIKey.invalid_key()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_put_user_returns_403_invalid_user(self, api_client, users_table, user_put_payload_ok):
        self.permission(granted=False, message=Messages.APIKey.invalid_user())
        user_id = users_table[0].id
        response = api_client.put(f"{self.__get_url()}{user_id}", user_put_payload_ok, format='json')

        assert response.json()['success'] is False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] is None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.APIKey.invalid_user()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_put_user_returns_404_not_found(self, api_client, user_put_payload_ok):
        self.permission(granted=True)
        response = api_client.put(f"{self.__get_url()}999", user_put_payload_ok, format='json')

        assert response.json()['success'] is False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] is None
        assert response.json()['errors'][0]['message'] == Messages.Put.not_found("collection user", "999")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_put_user_returns_500_database_error_connection_lost(self, api_client, users_table, user_put_payload_ok):
        self.permission(granted=True)
        self.connection_lost(UserCollection, self.PUT)
        user_id = users_table[0].id
        response = api_client.put(f"{self.__get_url()}{user_id}", user_put_payload_ok, format='json')

        assert response.json()['success'] is False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] is None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Database.connection_lost()
        assert response.json()['errors'][0]['code'] == Messages.Code.connection_lost()
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_delete_user_returns_200_ok(self, api_client, users_table):
        self.permission(granted=True)
        user_id = users_table[0].id
        response = api_client.delete(f"{self.__get_url()}{user_id}")

        assert response.json()['success'] is True
        assert response.json()['message'] == Messages.deleted_successfully()
        assert response.json()['errors'] is None
        assert response.json()['data']['message'] == Messages.Delete.deleted_one("collection user", str(user_id))
        assert response.status_code == status.HTTP_200_OK

    def test_delete_user_returns_403_invalid_key(self, api_client, users_table):
        self.permission(granted=False, message=Messages.APIKey.invalid_key())
        user_id = users_table[0].id
        response = api_client.delete(f"{self.__get_url()}{user_id}")

        assert response.json()['success'] is False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] is None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.APIKey.invalid_key()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_user_returns_403_invalid_user(self, api_client, users_table):
        self.permission(granted=False, message=Messages.APIKey.invalid_user())
        user_id = users_table[0].id
        response = api_client.delete(f"{self.__get_url()}{user_id}")

        assert response.json()['success'] is False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] is None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.APIKey.invalid_user()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_user_returns_404_not_found(self, api_client):
        self.permission(granted=True)
        response = api_client.delete(f"{self.__get_url()}999")

        assert response.json()['success'] is False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] is None
        assert response.json()['errors'][0]['message'] == Messages.Delete.not_found("collection user", "999")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_user_returns_500_database_error_connection_lost(self, api_client, users_table):
        self.permission(granted=True)
        self.connection_lost(UserCollection, self.DELETE)
        user_id = users_table[0].id
        response = api_client.delete(f"{self.__get_url()}{user_id}")

        assert response.json()['success'] is False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] is None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Database.connection_lost()
        assert response.json()['errors'][0]['code'] == Messages.Code.connection_lost()
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_user_model_str_representation(self):
        test_username = "test_user"
        user = UserCollection.objects.create(
            username=test_username,
            email="str@example.com",
            password_hash="test",
            first_name="first",
            last_name="last"
        )

        assert str(user) == test_username

    def __get_url(self):
        return f"/{USERS_URL_V1}"