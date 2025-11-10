import pytest
from rest_framework import status

from _backend.settings import STAMP_TYPES_URL_V1
from common.api.messages import Messages
from common.test.abstract_api_unit_test import AbstractApiUnitTest
from common.test.api_client import api_client
from common.test.stamp_types_api_test_data import (
    stamp_types_table,
    stamp_type_post_payload_ok,
    stamp_type_put_payload_ok
)
from stamp_types_api.api.serializers.stamp_type_response_serializer import StampTypeResponseSerializer
from stamp_types_api.models import StampType


@pytest.mark.django_db
class TestStampTypesAPI(AbstractApiUnitTest):
    def test_get_all_stamp_types_returns_200_ok_data(self, api_client, stamp_types_table):
        self.permission(granted=True)
        response = api_client.get(self.__get_url())

        original = StampTypeResponseSerializer(stamp_types_table,many=True)

        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.retrieved_successfully()
        assert response.json()['errors'] == None
        assert len(response.json()['data']) == len(original.data)
        assert response.json()['data'] == original.data
        assert response.status_code == status.HTTP_200_OK

    def test_get_all_stamp_types_returns_200_ok_no_data(self, api_client):
        self.permission(granted=True)
        response = api_client.get(self.__get_url())

        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.retrieved_successfully()
        assert response.json()['errors'] == None
        assert len(response.json()['data']) == 0
        assert response.status_code == status.HTTP_200_OK

    def test_get_all_stamp_types_returns_403_header_missing(self, api_client):
        response = api_client.get(self.__get_url())

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.header_missing()
        assert response.json()['errors'][0]['code'] == Messages.Code.authentication_failed()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_all_stamp_types_returns_403_invalid_format(self, api_client):
        self.permission(granted=False, message=Messages.Auth.invalid_format())
        response = api_client.get(self.__get_url())

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.invalid_format()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_all_stamp_types_returns_403_auth_type_not_supported(self, api_client):
        self.permission(granted=False, message=Messages.Auth.not_supported())
        response = api_client.get(self.__get_url())

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.not_supported()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_all_stamp_types_returns_403_invalid_api_key(self, api_client):
        self.permission(granted=False, message=Messages.Auth.invalid_api_key())
        response = api_client.get(self.__get_url())

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == "detail"
        assert response.json()['errors'][0]['message'] == Messages.Auth.invalid_api_key()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_all_stamp_types_returns_403_not_enough_rights(self, api_client):
        self.permission(granted=False, message=Messages.Auth.not_enough_rights())
        response = api_client.get(self.__get_url())

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == "detail"
        assert response.json()['errors'][0]['message'] == Messages.Auth.not_enough_rights()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_all_stamp_types_returns_403_basic_auth_user_or_password_invalid(self, api_client):
        self.permission(granted=False, message=Messages.Auth.user_or_password_invalid())
        response = api_client.get(self.__get_url())

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.user_or_password_invalid()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_all_stamp_types_returns_403_basic_auth_user_not_found(self, api_client):
        self.permission(granted=False, message=Messages.Auth.user_not_found())
        response = api_client.get(self.__get_url())

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.user_not_found()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_all_stamp_types_returns_500_database_error_connection_lost(self, api_client):
        self.permission(granted=True)
        self.connection_lost(StampType, self.GET_ALL)
        response = api_client.get(self.__get_url())

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Database.connection_lost()
        assert response.json()['errors'][0]['code'] == Messages.Code.connection_lost()
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_post_stamp_type_returns_201_created(self, api_client, stamp_type_post_payload_ok):
        self.permission(granted=True)
        response = api_client.post(self.__get_url(), stamp_type_post_payload_ok, format='json')

        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.created_successfully()
        assert response.json()['errors'] == None
        assert response.json()['data']['name'] == stamp_type_post_payload_ok["name"]
        assert response.status_code == status.HTTP_201_CREATED

    def test_post_stamp_type_returns_400_missing_field(self, api_client, stamp_type_post_payload_ok):
        self.permission(granted=True)
        del stamp_type_post_payload_ok["name"]
        response = api_client.post(self.__get_url(), stamp_type_post_payload_ok, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == "name"
        assert response.json()['errors'][0]['message'] == Messages.field_required()
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_post_stamp_type_returns_400_invalid_field(self, api_client, stamp_type_post_payload_ok):
        self.permission(granted=True)
        stamp_type_post_payload_ok['new_field'] = 'new_value'
        response = api_client.post(self.__get_url(), stamp_type_post_payload_ok, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == "new_field"
        assert response.json()['errors'][0]['message'] == Messages.field_not_allowed()
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_post_stamp_type_returns_403_header_missing(self, api_client):
        response = api_client.post(self.__get_url())

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.header_missing()
        assert response.json()['errors'][0]['code'] == Messages.Code.authentication_failed()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_post_stamp_type_returns_403_invalid_format(self, api_client):
        self.permission(granted=False, message=Messages.Auth.invalid_format())
        response = api_client.post(self.__get_url())

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.invalid_format()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_post_stamp_type_returns_403_auth_type_not_supported(self, api_client):
        self.permission(granted=False, message=Messages.Auth.not_supported())
        response = api_client.post(self.__get_url())

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.not_supported()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_post_stamp_type_returns_403_invalid_api_key(self, api_client, stamp_type_post_payload_ok):
        self.permission(granted=False, message=Messages.Auth.invalid_api_key())
        response = api_client.post(self.__get_url(), stamp_type_post_payload_ok, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == "detail"
        assert response.json()['errors'][0]['message'] == Messages.Auth.invalid_api_key()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_post_stamp_type_returns_403_not_enough_rights(self, api_client, stamp_type_post_payload_ok):
        self.permission(granted=False, message=Messages.Auth.not_enough_rights())
        response = api_client.post(self.__get_url(), stamp_type_post_payload_ok, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == "detail"
        assert response.json()['errors'][0]['message'] == Messages.Auth.not_enough_rights()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_post_stamp_type_returns_403_basic_auth_user_or_password_invalid(self, api_client):
        self.permission(granted=False, message=Messages.Auth.user_or_password_invalid())
        response = api_client.post(self.__get_url())

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.user_or_password_invalid()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_post_stamp_type_returns_403_basic_auth_user_not_found(self, api_client):
        self.permission(granted=False, message=Messages.Auth.user_not_found())
        response = api_client.post(self.__get_url())

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.user_not_found()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_post_stamp_type_returns_500_database_error_connection_lost(self, api_client, stamp_type_post_payload_ok):
        self.permission(granted=True)
        self.connection_lost(StampType, self.POST)
        response = api_client.post(self.__get_url(), stamp_type_post_payload_ok, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Database.connection_lost()
        assert response.json()['errors'][0]['code'] == Messages.Code.connection_lost()
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_get_one_stamp_type_returns_200_ok(self, api_client, stamp_types_table):
        self.permission(granted=True)
        stamp_type_id = stamp_types_table[0].id
        response = api_client.get(f"{self.__get_url()}{stamp_type_id}")

        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.retrieved_successfully()
        assert response.json()['errors'] == None
        assert response.json()['data']['name'] == stamp_types_table[0].name
        assert response.status_code == status.HTTP_200_OK

    def test_get_one_stamp_type_returns_403_header_missing(self, api_client, stamp_types_table):
        stamp_type_id = stamp_types_table[0].id
        response = api_client.get(f"{self.__get_url()}{stamp_type_id}")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.header_missing()
        assert response.json()['errors'][0]['code'] == Messages.Code.authentication_failed()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_one_stamp_type_returns_403_invalid_format(self, api_client, stamp_types_table):
        self.permission(granted=False, message=Messages.Auth.invalid_format())
        stamp_type_id = stamp_types_table[0].id
        response = api_client.get(f"{self.__get_url()}{stamp_type_id}")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.invalid_format()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_one_stamp_type_returns_403_auth_type_not_supported(self, api_client, stamp_types_table):
        self.permission(granted=False, message=Messages.Auth.not_supported())
        stamp_type_id = stamp_types_table[0].id
        response = api_client.get(f"{self.__get_url()}{stamp_type_id}")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.not_supported()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_one_stamp_type_returns_403_invalid_api_key(self, api_client, stamp_types_table):
        self.permission(granted=False, message=Messages.Auth.invalid_api_key())
        stamp_type_id = stamp_types_table[0].id
        response = api_client.get(f"{self.__get_url()}{stamp_type_id}")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == "detail"
        assert response.json()['errors'][0]['message'] == Messages.Auth.invalid_api_key()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_one_stamp_type_returns_403_not_enough_rights(self, api_client, stamp_types_table):
        self.permission(granted=False, message=Messages.Auth.not_enough_rights())
        stamp_type_id = stamp_types_table[0].id
        response = api_client.get(f"{self.__get_url()}{stamp_type_id}")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == "detail"
        assert response.json()['errors'][0]['message'] == Messages.Auth.not_enough_rights()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_one_stamp_type_returns_403_basic_auth_user_or_password_invalid(self, api_client, stamp_types_table):
        self.permission(granted=False, message=Messages.Auth.user_or_password_invalid())
        stamp_type_id = stamp_types_table[0].id
        response = api_client.get(f"{self.__get_url()}{stamp_type_id}")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.user_or_password_invalid()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_one_stamp_type_returns_403_basic_auth_user_not_found(self, api_client, stamp_types_table):
        self.permission(granted=False, message=Messages.Auth.user_not_found())
        stamp_type_id = stamp_types_table[0].id
        response = api_client.get(f"{self.__get_url()}{stamp_type_id}")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.user_not_found()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_one_stamp_type_returns_404_not_found(self, api_client):
        self.permission(granted=True)
        response = api_client.get(f"{self.__get_url()}999")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['message'] == Messages.Get.not_found("stamptype", "999")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_one_stamp_type_returns_500_database_error_connection_lost(self, api_client, stamp_types_table):
        self.permission(granted=True)
        self.connection_lost(StampType, self.GET_ONE)
        stamp_type_id = stamp_types_table[0].id
        response = api_client.get(f"{self.__get_url()}{stamp_type_id}")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Database.connection_lost()
        assert response.json()['errors'][0]['code'] == Messages.Code.connection_lost()
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_put_stamp_type_returns_200_ok(self, api_client, stamp_types_table, stamp_type_put_payload_ok):
        self.permission(granted=True)
        stamp_type_id = stamp_types_table[0].id
        response = api_client.put(f"{self.__get_url()}{stamp_type_id}", stamp_type_put_payload_ok, format='json')

        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.updated_successfully()
        assert response.json()['errors'] == None
        assert response.json()['data']['name'] == stamp_type_put_payload_ok["name"]
        assert response.status_code == status.HTTP_200_OK

    def test_put_stamp_type_returns_400_invalid_field(self, api_client, stamp_types_table, stamp_type_put_payload_ok):
        self.permission(granted=True)
        stamp_type_id = stamp_types_table[0].id
        stamp_type_put_payload_ok["new_field"] = "new_value"
        response = api_client.put(f"{self.__get_url()}{stamp_type_id}", stamp_type_put_payload_ok, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == "new_field"
        assert response.json()['errors'][0]['message'] == Messages.field_not_allowed()
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_put_stamp_type_returns_403_header_missing(self, api_client, stamp_types_table):
        stamp_type_id = stamp_types_table[0].id
        response = api_client.put(f"{self.__get_url()}{stamp_type_id}")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.header_missing()
        assert response.json()['errors'][0]['code'] == Messages.Code.authentication_failed()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_put_stamp_type_returns_403_invalid_format(self, api_client, stamp_types_table):
        self.permission(granted=False, message=Messages.Auth.invalid_format())
        stamp_type_id = stamp_types_table[0].id
        response = api_client.put(f"{self.__get_url()}{stamp_type_id}")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.invalid_format()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_put_stamp_type_returns_403_auth_type_not_supported(self, api_client, stamp_types_table):
        self.permission(granted=False, message=Messages.Auth.not_supported())
        stamp_type_id = stamp_types_table[0].id
        response = api_client.put(f"{self.__get_url()}{stamp_type_id}")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.not_supported()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_put_stamp_type_returns_403_invalid_api_key(self, api_client, stamp_types_table, stamp_type_put_payload_ok):
        self.permission(granted=False, message=Messages.Auth.invalid_api_key())
        stamp_type_id = stamp_types_table[0].id
        response = api_client.put(f"{self.__get_url()}{stamp_type_id}", stamp_type_put_payload_ok, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == "detail"
        assert response.json()['errors'][0]['message'] == Messages.Auth.invalid_api_key()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_put_stamp_type_returns_403_not_enough_rights(self, api_client, stamp_types_table, stamp_type_put_payload_ok):
        self.permission(granted=False, message=Messages.Auth.not_enough_rights())
        stamp_type_id = stamp_types_table[0].id
        response = api_client.put(f"{self.__get_url()}{stamp_type_id}", stamp_type_put_payload_ok, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == "detail"
        assert response.json()['errors'][0]['message'] == Messages.Auth.not_enough_rights()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_put_stamp_type_returns_403_basic_auth_user_or_password_invalid(self, api_client, stamp_types_table):
        self.permission(granted=False, message=Messages.Auth.user_or_password_invalid())
        stamp_type_id = stamp_types_table[0].id
        response = api_client.put(f"{self.__get_url()}{stamp_type_id}")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.user_or_password_invalid()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_put_stamp_type_returns_403_basic_auth_user_not_found(self, api_client, stamp_types_table):
        self.permission(granted=False, message=Messages.Auth.user_not_found())
        stamp_type_id = stamp_types_table[0].id
        response = api_client.put(f"{self.__get_url()}{stamp_type_id}")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.user_not_found()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_put_stamp_type_returns_404_not_found(self, api_client, stamp_type_put_payload_ok):
        self.permission(granted=True)
        response = api_client.put(f"{self.__get_url()}999", stamp_type_put_payload_ok, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['message'] == Messages.Put.not_found("stamptype", "999")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_put_stamp_type_returns_500_database_error_connection_lost(self, api_client, stamp_types_table, stamp_type_put_payload_ok):
        self.permission(granted=True)
        self.connection_lost(StampType, self.PUT)
        stamp_type_id = stamp_types_table[0].id
        response = api_client.put(f"{self.__get_url()}{stamp_type_id}", stamp_type_put_payload_ok, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Database.connection_lost()
        assert response.json()['errors'][0]['code'] == Messages.Code.connection_lost()
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_delete_stamp_type_returns_200_ok(self, api_client, stamp_types_table):
        self.permission(granted=True)
        stamp_type_id = stamp_types_table[0].id
        response = api_client.delete(f"{self.__get_url()}{stamp_type_id}")

        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.deleted_successfully()
        assert response.json()['errors'] == None
        assert response.json()['data']['message'] == Messages.Delete.deleted_one("stamptype", str(stamp_type_id))
        assert response.status_code == status.HTTP_200_OK

    def test_delete_stamp_type_returns_403_header_missing(self, api_client, stamp_types_table):
        stamp_type_id = stamp_types_table[0].id
        response = api_client.delete(f"{self.__get_url()}{stamp_type_id}")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.header_missing()
        assert response.json()['errors'][0]['code'] == Messages.Code.authentication_failed()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_stamp_type_returns_403_invalid_format(self, api_client, stamp_types_table):
        self.permission(granted=False, message=Messages.Auth.invalid_format())
        stamp_type_id = stamp_types_table[0].id
        response = api_client.delete(f"{self.__get_url()}{stamp_type_id}")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.invalid_format()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_stamp_type_returns_403_auth_type_not_supported(self, api_client, stamp_types_table):
        self.permission(granted=False, message=Messages.Auth.not_supported())
        stamp_type_id = stamp_types_table[0].id
        response = api_client.delete(f"{self.__get_url()}{stamp_type_id}")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.not_supported()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_stamp_type_returns_403_invalid_api_key(self, api_client, stamp_types_table):
        self.permission(granted=False, message=Messages.Auth.invalid_api_key())
        stamp_type_id = stamp_types_table[0].id
        response = api_client.delete(f"{self.__get_url()}{stamp_type_id}")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == "detail"
        assert response.json()['errors'][0]['message'] == Messages.Auth.invalid_api_key()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_stamp_type_returns_403_not_enough_rights(self, api_client, stamp_types_table):
        self.permission(granted=False, message=Messages.Auth.not_enough_rights())
        stamp_type_id = stamp_types_table[0].id
        response = api_client.delete(f"{self.__get_url()}{stamp_type_id}")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == "detail"
        assert response.json()['errors'][0]['message'] == Messages.Auth.not_enough_rights()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_stamp_type_returns_403_basic_auth_user_or_password_invalid(self, api_client, stamp_types_table):
        self.permission(granted=False, message=Messages.Auth.user_or_password_invalid())
        stamp_type_id = stamp_types_table[0].id
        response = api_client.delete(f"{self.__get_url()}{stamp_type_id}")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.user_or_password_invalid()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_stamp_type_returns_403_basic_auth_user_not_found(self, api_client, stamp_types_table):
        self.permission(granted=False, message=Messages.Auth.user_not_found())
        stamp_type_id = stamp_types_table[0].id
        response = api_client.delete(f"{self.__get_url()}{stamp_type_id}")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.user_not_found()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_stamp_type_returns_404_not_found(self, api_client):
        self.permission(granted=True)
        response = api_client.delete(f"{self.__get_url()}999")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['message'] == Messages.Delete.not_found("stamptype", "999")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_stamp_type_returns_500_database_error_connection_lost(self, api_client, stamp_types_table):
        self.permission(granted=True)
        self.connection_lost(StampType, self.DELETE)
        stamp_type_id = stamp_types_table[0].id
        response = api_client.delete(f"{self.__get_url()}{stamp_type_id}")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Database.connection_lost()
        assert response.json()['errors'][0]['code'] == Messages.Code.connection_lost()
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_stamp_type_model_str_representation(self):
        test_name = "test_name"
        stamp_type = StampType.objects.create(
            name=test_name
        )

        assert str(stamp_type) == test_name

    def __get_url(self):
        return f"/{STAMP_TYPES_URL_V1}"
