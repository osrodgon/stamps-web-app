import pytest
from rest_framework import status

from _backend.settings import CONDITION_TYPES_URL_V1
from common.api.messages import Messages
from common.test.abstract_api_unit_test import AbstractApiUnitTest
from common.test.api_client import api_client # noqa
from common.test.condition_types_api_test_data import (
    condition_types_table, # noqa
    condition_type_post_payload_ok,
    condition_type_put_payload_ok,
)
from condition_types_api.api.serializers.condition_type_response_serializer import ConditionTypeResponseSerializer
from condition_types_api.models import ConditionType

@pytest.mark.django_db
class TestConditionTypesAPI(AbstractApiUnitTest):
    def test_get_all_condition_types_returns_200_ok_data(self, api_client, condition_types_table):
        self.permission(granted=True)
        response = api_client.get(self.__get_url())

        original = ConditionTypeResponseSerializer(condition_types_table, many=True)

        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.retrieved_successfully()
        assert response.json()['errors'] == None
        assert len(response.json()['data']) == len(condition_types_table)
        assert response.json()['data'] == original.data
        assert response.status_code == status.HTTP_200_OK

    def test_get_all_condition_types_returns_200_ok_no_data(self, api_client):
        self.permission(granted=True)
        response = api_client.get(self.__get_url())

        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.retrieved_successfully()
        assert response.json()['errors'] == None
        assert len(response.json()['data']) == 0
        assert response.status_code == status.HTTP_200_OK

    def test_get_all_condition_types_returns_403_header_missing(self, api_client):
        response = api_client.get(self.__get_url())

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.header_missing()
        assert response.json()['errors'][0]['code'] == Messages.Code.authentication_failed()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_all_condition_types_returns_403_invalid_format(self, api_client):
        self.permission(granted=False, message=Messages.Auth.invalid_format())
        response = api_client.get(self.__get_url())

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.invalid_format()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_all_condition_types_returns_403_auth_type_not_supported(self, api_client):
        self.permission(granted=False, message=Messages.Auth.not_supported())
        response = api_client.get(self.__get_url())

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.not_supported()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_all_condition_types_returns_403_invalid_api_key(self, api_client):
        self.permission(granted=False, message=Messages.Auth.invalid_api_key())
        response = api_client.get(self.__get_url())

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == "detail"
        assert response.json()['errors'][0]['message'] == Messages.Auth.invalid_api_key()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_all_condition_types_returns_403_not_enough_rights(self, api_client):
        self.permission(granted=False, message=Messages.Auth.not_enough_rights())
        response = api_client.get(self.__get_url())

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == "detail"
        assert response.json()['errors'][0]['message'] == Messages.Auth.not_enough_rights()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_all_condition_types_returns_403_basic_auth_user_or_password_invalid(self, api_client):
        self.permission(granted=False, message=Messages.Auth.user_or_password_invalid())
        response = api_client.get(self.__get_url())

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.user_or_password_invalid()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_all_condition_types_returns_403_basic_auth_user_not_found(self, api_client):
        self.permission(granted=False, message=Messages.Auth.user_not_found())
        response = api_client.get(self.__get_url())

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.user_not_found()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_all_condition_types_returns_500_database_error_connection_lost(self, api_client):
        self.permission(granted=True)
        self.connection_lost(ConditionType, self.GET_ALL)
        response = api_client.get(self.__get_url())

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Database.connection_lost()
        assert response.json()['errors'][0]['code'] == Messages.Code.connection_lost()
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_post_condition_type_returns_201_created(self, api_client, condition_type_post_payload_ok):
        self.permission(granted=True)
        response = api_client.post(self.__get_url(), condition_type_post_payload_ok, format='json')

        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.created_successfully()
        assert response.json()['errors'] == None
        assert response.json()['data']['name'] == condition_type_post_payload_ok["name"]
        assert response.status_code == status.HTTP_201_CREATED

    def test_post_condition_type_returns_400_missing_field(self, api_client, condition_type_post_payload_ok):
        del condition_type_post_payload_ok['name']
        self.permission(granted=True)
        response = api_client.post(self.__get_url(), condition_type_post_payload_ok, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == "name"
        assert response.json()['errors'][0]['message'] == Messages.field_required()
        assert response.json()['errors'][0]['code'] == Messages.Code.required()
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_post_condition_type_returns_400_bad_request_invalid_payload_field_not_allowed(self, api_client, condition_type_post_payload_ok):
        self.permission(granted=True)
        condition_type_post_payload_ok["new_field"] = "new_value"
        response = api_client.post(self.__get_url(), condition_type_post_payload_ok, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == "new_field"
        assert response.json()['errors'][0]['message'] == Messages.field_not_allowed()
        assert response.json()['errors'][0]['code'] == Messages.Code.invalid()
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_post_condition_type_returns_400_bad_request_duplicate_name(self, api_client, condition_types_table):
        self.permission(granted=True)
        payload = {"name": condition_types_table[0].name, "description": "Some description"}
        response = api_client.post(self.__get_url(), payload, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == "name"
        assert response.json()['errors'][0]['message'] == Messages.Post.already_exists("condition type", "name")
        assert response.json()['errors'][0]['code'] == Messages.Code.unique()
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_post_condition_type_returns_403_header_missing(self, api_client):
        response = api_client.post(self.__get_url())

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.header_missing()
        assert response.json()['errors'][0]['code'] == Messages.Code.authentication_failed()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_post_condition_type_returns_403_invalid_format(self, api_client):
        self.permission(granted=False, message=Messages.Auth.invalid_format())
        response = api_client.post(self.__get_url())

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.invalid_format()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_post_condition_type_returns_403_auth_type_not_supported(self, api_client):
        self.permission(granted=False, message=Messages.Auth.not_supported())
        response = api_client.post(self.__get_url())

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.not_supported()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_post_condition_type_returns_403_invalid_api_key(self, api_client, condition_type_post_payload_ok):
        self.permission(granted=False, message=Messages.Auth.invalid_api_key())
        response = api_client.post(self.__get_url(), condition_type_post_payload_ok, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == "detail"
        assert response.json()['errors'][0]['message'] == Messages.Auth.invalid_api_key()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_post_condition_type_returns_403_not_enough_rights(self, api_client, condition_type_post_payload_ok):
        self.permission(granted=False, message=Messages.Auth.not_enough_rights())
        response = api_client.post(self.__get_url(), condition_type_post_payload_ok, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == "detail"
        assert response.json()['errors'][0]['message'] == Messages.Auth.not_enough_rights()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_post_condition_type_returns_403_basic_auth_user_or_password_invalid(self, api_client):
        self.permission(granted=False, message=Messages.Auth.user_or_password_invalid())
        response = api_client.post(self.__get_url())

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.user_or_password_invalid()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_post_condition_type_returns_403_basic_auth_user_not_found(self, api_client):
        self.permission(granted=False, message=Messages.Auth.user_not_found())
        response = api_client.post(self.__get_url())

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.user_not_found()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_post_condition_type_returns_500_database_error_connection_lost(self, api_client, condition_type_post_payload_ok):
        self.permission(granted=True)
        self.connection_lost(ConditionType, self.POST)
        response = api_client.post(self.__get_url(), condition_type_post_payload_ok, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Database.connection_lost()
        assert response.json()['errors'][0]['code'] == Messages.Code.connection_lost()
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_get_one_condition_type_returns_200_ok_data(self, api_client, condition_types_table):
        self.permission(granted=True)
        condition_type_id = condition_types_table[0].id
        response = api_client.get(f"{self.__get_url()}{condition_type_id}")

        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.retrieved_successfully()
        assert response.json()['errors'] == None
        assert response.json()['data']['name'] == condition_types_table[0].name
        assert response.status_code == status.HTTP_200_OK

    def test_get_one_condition_type_returns_403_header_missing(self, api_client, condition_types_table):
        condition_type_id = condition_types_table[0].id
        response = api_client.get(f"{self.__get_url()}{condition_type_id}")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.header_missing()
        assert response.json()['errors'][0]['code'] == Messages.Code.authentication_failed()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_one_condition_type_returns_403_invalid_format(self, api_client, condition_types_table):
        self.permission(granted=False, message=Messages.Auth.invalid_format())
        condition_type_id = condition_types_table[0].id
        response = api_client.get(f"{self.__get_url()}{condition_type_id}")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.invalid_format()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_one_condition_type_returns_403_auth_type_not_supported(self, api_client, condition_types_table):
        self.permission(granted=False, message=Messages.Auth.not_supported())
        condition_type_id = condition_types_table[0].id
        response = api_client.get(f"{self.__get_url()}{condition_type_id}")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.not_supported()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_one_condition_type_returns_403_invalid_api_key(self, api_client, condition_types_table):
        self.permission(granted=False, message=Messages.Auth.invalid_api_key())
        condition_type_id = condition_types_table[0].id
        response = api_client.get(f"{self.__get_url()}{condition_type_id}")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == "detail"
        assert response.json()['errors'][0]['message'] == Messages.Auth.invalid_api_key()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_one_condition_type_returns_403_not_enough_rights(self, api_client, condition_types_table):
        self.permission(granted=False, message=Messages.Auth.not_enough_rights())
        condition_type_id = condition_types_table[0].id
        response = api_client.get(f"{self.__get_url()}{condition_type_id}")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == "detail"
        assert response.json()['errors'][0]['message'] == Messages.Auth.not_enough_rights()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_one_condition_type_returns_403_basic_auth_user_or_password_invalid(self, api_client, condition_types_table):
        self.permission(granted=False, message=Messages.Auth.user_or_password_invalid())
        condition_type_id = condition_types_table[0].id
        response = api_client.get(f"{self.__get_url()}{condition_type_id}")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.user_or_password_invalid()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_one_condition_type_returns_403_basic_auth_user_not_found(self, api_client, condition_types_table):
        self.permission(granted=False, message=Messages.Auth.user_not_found())
        condition_type_id = condition_types_table[0].id
        response = api_client.get(f"{self.__get_url()}{condition_type_id}")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.user_not_found()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_one_condition_type_returns_404_not_found(self, api_client):
        self.permission(granted=True)
        response = api_client.get(f"{self.__get_url()}999")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == None
        assert response.json()['errors'][0]['message'] == Messages.Get.not_found("condition type", "999")
        assert response.json()['errors'][0]['code'] == Messages.Code.other()
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_one_condition_type_returns_500_database_error_connection_lost(self, api_client, condition_types_table):
        self.permission(granted=True)
        self.connection_lost(ConditionType, self.GET_ONE)
        condition_type_id = condition_types_table[0].id
        response = api_client.get(f"{self.__get_url()}{condition_type_id}")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == "detail"
        assert response.json()['errors'][0]['message'] == Messages.Database.connection_lost()
        assert response.json()['errors'][0]['code'] == Messages.Code.connection_lost()
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_put_condition_type_returns_200_ok(self, api_client, condition_types_table, condition_type_put_payload_ok):
        condition_type_id = condition_types_table[0].id
        self.permission(granted=True)
        response = api_client.put(f"{self.__get_url()}{condition_type_id}", condition_type_put_payload_ok, format='json')

        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.updated_successfully()
        assert response.json()['errors'] == None
        assert response.json()['data']['name'] == condition_type_put_payload_ok["name"]
        assert response.status_code == status.HTTP_200_OK

    def test_put_condition_type_returns_400_invalid_field(self, api_client, condition_types_table, condition_type_put_payload_ok):
        condition_type_put_payload_ok["new_field"] = "new_value"
        item_id = condition_types_table[0].id
        self.permission(granted=True)
        response = api_client.put(f"{self.__get_url()}{item_id}", condition_type_put_payload_ok, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == "new_field"
        assert response.json()['errors'][0]['message'] == Messages.field_not_allowed()
        assert response.json()['errors'][0]['code'] == Messages.Code.invalid()
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_put_condition_type_returns_400_bad_request_missing_field(self, api_client, condition_types_table, condition_type_put_payload_ok):
        self.permission(granted=True)
        condition_type_id = condition_types_table[0].id
        del condition_type_put_payload_ok["name"]
        response = api_client.put(f"{self.__get_url()}{condition_type_id}", condition_type_put_payload_ok, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == "name"
        assert response.json()['errors'][0]['message'] == Messages.field_required()
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_put_condition_type_returns_403_invalid_key(self, api_client, condition_types_table, condition_type_put_payload_ok):
        self.permission(granted=False, message=Messages.Auth.invalid_api_key())
        item_id = condition_types_table[0].id
        response = api_client.put(f"{self.__get_url()}{item_id}", condition_type_put_payload_ok, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.invalid_api_key()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_put_condition_type_returns_403_invalid_user(self, api_client, condition_types_table, condition_type_put_payload_ok):
        self.permission(granted=False, message=Messages.Auth.not_enough_rights())
        item_id = condition_types_table[0].id
        response = api_client.put(f"{self.__get_url()}{item_id}", condition_type_put_payload_ok, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.not_enough_rights()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_put_condition_type_returns_400_bad_request_duplicate_name(self, api_client, condition_types_table):
        self.permission(granted=True)
        # Create a second condition type to have a name to conflict with
        ConditionType.objects.create(name="Existing Name")
        condition_type_id = condition_types_table[0].id
        payload = {"name": "Existing Name"}
        response = api_client.put(f"{self.__get_url()}{condition_type_id}", payload, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == "name"
        assert response.json()['errors'][0]['message'] == Messages.Put.already_exists("condition type", "name")
        assert response.json()['errors'][0]['code'] == Messages.Code.unique()
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_put_condition_type_returns_404_not_found(self, api_client, condition_type_put_payload_ok):
        self.permission(granted=True)
        response = api_client.put(f"{self.__get_url()}999", condition_type_put_payload_ok, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == None
        assert response.json()['errors'][0]['message'] == Messages.Put.not_found("condition type", "999")
        assert response.json()['errors'][0]['code'] == Messages.Code.other()
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_put_condition_type_returns_500_database_error_connection_lost(self, api_client, condition_types_table, condition_type_put_payload_ok):
        self.permission(granted=True)
        self.connection_lost(ConditionType, self.PUT)
        condition_type_id = condition_types_table[0].id
        response = api_client.put(f"{self.__get_url()}{condition_type_id}", condition_type_put_payload_ok, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Database.connection_lost()
        assert response.json()['errors'][0]['code'] == Messages.Code.connection_lost()
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_delete_condition_type_returns_200_ok(self, api_client, condition_types_table):
        condition_type_id = condition_types_table[0].id
        self.permission(granted=True)
        response = api_client.delete(f"{self.__get_url()}{condition_type_id}")

        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.deleted_successfully()
        assert response.json()['errors'] == None
        assert response.json()['data']['message'] == Messages.Delete.deleted_one("condition type", str(condition_type_id))
        assert response.status_code == status.HTTP_200_OK

    def test_delete_condition_type_returns_403_header_missing(self, api_client, condition_types_table):
        condition_type_id = condition_types_table[0].id
        response = api_client.delete(f"{self.__get_url()}{condition_type_id}")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.header_missing()
        assert response.json()['errors'][0]['code'] == Messages.Code.authentication_failed()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_condition_type_returns_403_invalid_format(self, api_client, condition_types_table):
        self.permission(granted=False, message=Messages.Auth.invalid_format())
        condition_type_id = condition_types_table[0].id
        response = api_client.delete(f"{self.__get_url()}{condition_type_id}")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.invalid_format()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_condition_type_returns_403_auth_type_not_supported(self, api_client, condition_types_table):
        self.permission(granted=False, message=Messages.Auth.not_supported())
        condition_type_id = condition_types_table[0].id
        response = api_client.delete(f"{self.__get_url()}{condition_type_id}")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.not_supported()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_condition_type_returns_403_invalid_api_key(self, api_client, condition_types_table):
        self.permission(granted=False, message=Messages.Auth.invalid_api_key())
        condition_type_id = condition_types_table[0].id
        response = api_client.delete(f"{self.__get_url()}{condition_type_id}")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == "detail"
        assert response.json()['errors'][0]['message'] == Messages.Auth.invalid_api_key()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_condition_type_returns_403_not_enough_rights(self, api_client, condition_types_table):
        self.permission(granted=False, message=Messages.Auth.not_enough_rights())
        condition_type_id = condition_types_table[0].id
        response = api_client.delete(f"{self.__get_url()}{condition_type_id}")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == "detail"
        assert response.json()['errors'][0]['message'] == Messages.Auth.not_enough_rights()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_condition_type_returns_403_basic_auth_user_or_password_invalid(self, api_client, condition_types_table):
        self.permission(granted=False, message=Messages.Auth.user_or_password_invalid())
        condition_type_id = condition_types_table[0].id
        response = api_client.delete(f"{self.__get_url()}{condition_type_id}")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.user_or_password_invalid()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_condition_type_returns_403_basic_auth_user_not_found(self, api_client, condition_types_table):
        self.permission(granted=False, message=Messages.Auth.user_not_found())
        condition_type_id = condition_types_table[0].id
        response = api_client.delete(f"{self.__get_url()}{condition_type_id}")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.user_not_found()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_condition_type_returns_404_not_found(self, api_client):
        self.permission(granted=True)
        response = api_client.delete(f"{self.__get_url()}999")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == None
        assert response.json()['errors'][0]['message'] == Messages.Delete.not_found("condition type", "999")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_condition_type_returns_500_database_error_connection_lost(self, api_client, condition_types_table):
        self.permission(granted=True)
        self.connection_lost(ConditionType, self.DELETE)
        item_id = condition_types_table[0].id
        response = api_client.delete(f"{self.__get_url()}{item_id}")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Database.connection_lost()
        assert response.json()['errors'][0]['code'] == Messages.Code.connection_lost()
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_condition_type_model_str_representation(self):
        test_name = "test_condition_type"
        condition_type = ConditionType.objects.create(name=test_name)
        assert str(condition_type) == test_name

    def __get_url(self):
        return f"/{CONDITION_TYPES_URL_V1}"