import pytest
from rest_framework import status

from _backend.settings import LOCATIONS_URL_V1
from common.api.messages import Messages
from common.test.abstract_api_unit_test import AbstractApiUnitTest
from common.test.api_client import api_client
from common.test.locations_api_test_data import (
    locations_table,
    location_post_payload_ok,
    location_put_payload_ok
)
from locations_api.models import Location
from locations_api.api.serializers.location_response_serializer import LocationResponseSerializer


@pytest.mark.django_db
class TestLocationsAPI(AbstractApiUnitTest):
    def test_get_all_locations_returns_200_ok_data(self, api_client, locations_table):
        self.permission(granted=True)
        response = api_client.get(self.__get_url())

        original = LocationResponseSerializer(locations_table, many=True)

        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.retrieved_successfully()
        assert response.json()['errors'] == None
        assert len(response.json()['data']) == len(original.data)
        assert response.json()['data'] == original.data
        assert response.status_code == status.HTTP_200_OK

    def test_get_all_locations_returns_200_ok_no_data(self, api_client):
        self.permission(granted=True)
        response = api_client.get(self.__get_url())

        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.retrieved_successfully()
        assert response.json()['errors'] == None
        assert len(response.json()['data']) == 0
        assert response.status_code == status.HTTP_200_OK

    def test_get_all_locations_returns_403_header_missing(self, api_client):
        response = api_client.get(self.__get_url())

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.header_missing()
        assert response.json()['errors'][0]['code'] == Messages.Code.authentication_failed()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_all_locations_returns_403_invalid_format(self, api_client):
        self.permission(granted=False, message=Messages.Auth.invalid_format())
        response = api_client.get(self.__get_url())

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.invalid_format()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_all_locations_returns_403_auth_type_not_supported(self, api_client):
        self.permission(granted=False, message=Messages.Auth.not_supported())
        response = api_client.get(self.__get_url())

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.not_supported()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_all_locations_returns_403_invalid_api_key(self, api_client):
        self.permission(granted=False, message=Messages.Auth.invalid_api_key())
        response = api_client.get(self.__get_url())

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == "detail"
        assert response.json()['errors'][0]['message'] == Messages.Auth.invalid_api_key()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_all_locations_returns_403_not_enough_rights(self, api_client):
        self.permission(granted=False, message=Messages.Auth.not_enough_rights())
        response = api_client.get(self.__get_url())

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == "detail"
        assert response.json()['errors'][0]['message'] == Messages.Auth.not_enough_rights()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_all_locations_returns_403_basic_auth_user_or_password_invalid(self, api_client):
        self.permission(granted=False, message=Messages.Auth.user_or_password_invalid())
        response = api_client.get(self.__get_url())

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.user_or_password_invalid()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_all_locations_returns_403_basic_auth_user_not_found(self, api_client):
        self.permission(granted=False, message=Messages.Auth.user_not_found())
        response = api_client.get(self.__get_url())

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.user_not_found()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_all_locations_returns_500_database_error_connection_lost(self, api_client):
        self.permission(granted=True)
        self.connection_lost(Location, self.GET_ALL)
        response = api_client.get(self.__get_url())

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Database.connection_lost()
        assert response.json()['errors'][0]['code'] == Messages.Code.connection_lost()
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_post_location_returns_201_created(self, api_client, location_post_payload_ok):
        self.permission(granted=True)
        response = api_client.post(self.__get_url(), location_post_payload_ok, format='json')

        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.created_successfully()
        assert response.json()['errors'] == None
        assert response.json()['data']['name'] == location_post_payload_ok["name"]
        assert response.status_code == status.HTTP_201_CREATED

    def test_post_location_returns_400_missing_field(self, api_client, location_post_payload_ok):
        self.permission(granted=True)
        del location_post_payload_ok["name"]
        response = api_client.post(self.__get_url(), location_post_payload_ok, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == "name"
        assert response.json()['errors'][0]['message'] == Messages.field_required()
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_post_location_returns_400_invalid_field(self, api_client, location_post_payload_ok):
        self.permission(granted=True)
        location_post_payload_ok['new_field'] = 'new_value'
        response = api_client.post(self.__get_url(), location_post_payload_ok, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == "new_field"
        assert response.json()['errors'][0]['message'] == Messages.field_not_allowed()
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_post_location_returns_403_header_missing(self, api_client):
        response = api_client.post(self.__get_url())

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.header_missing()
        assert response.json()['errors'][0]['code'] == Messages.Code.authentication_failed()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_post_location_returns_403_invalid_format(self, api_client):
        self.permission(granted=False, message=Messages.Auth.invalid_format())
        response = api_client.post(self.__get_url())

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.invalid_format()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_post_location_returns_403_auth_type_not_supported(self, api_client):
        self.permission(granted=False, message=Messages.Auth.not_supported())
        response = api_client.post(self.__get_url())

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.not_supported()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_post_location_returns_403_invalid_api_key(self, api_client, location_post_payload_ok):
        self.permission(granted=False, message=Messages.Auth.invalid_api_key())
        response = api_client.post(self.__get_url(), location_post_payload_ok, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == "detail"
        assert response.json()['errors'][0]['message'] == Messages.Auth.invalid_api_key()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_post_location_returns_403_not_enough_rights(self, api_client, location_post_payload_ok):
        self.permission(granted=False, message=Messages.Auth.not_enough_rights())
        response = api_client.post(self.__get_url(), location_post_payload_ok, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == "detail"
        assert response.json()['errors'][0]['message'] == Messages.Auth.not_enough_rights()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_post_location_returns_403_basic_auth_user_or_password_invalid(self, api_client):
        self.permission(granted=False, message=Messages.Auth.user_or_password_invalid())
        response = api_client.post(self.__get_url())

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.user_or_password_invalid()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_post_location_returns_403_basic_auth_user_not_found(self, api_client):
        self.permission(granted=False, message=Messages.Auth.user_not_found())
        response = api_client.post(self.__get_url())

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.user_not_found()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_post_location_returns_500_database_error_connection_lost(self, api_client, location_post_payload_ok):
        self.permission(granted=True)
        self.connection_lost(Location, self.POST)
        response = api_client.post(self.__get_url(), location_post_payload_ok, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Database.connection_lost()
        assert response.json()['errors'][0]['code'] == Messages.Code.connection_lost()
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_get_one_location_returns_200_ok(self, api_client, locations_table):
        self.permission(granted=True)
        location_id = locations_table[0].id
        response = api_client.get(f"{self.__get_url()}{location_id}")

        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.retrieved_successfully()
        assert response.json()['errors'] == None
        assert response.json()['data']['name'] == locations_table[0].name
        assert response.status_code == status.HTTP_200_OK

    def test_get_one_location_returns_403_header_missing(self, api_client, locations_table):
        location_id = locations_table[0].id
        response = api_client.get(f"{self.__get_url()}{location_id}")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.header_missing()
        assert response.json()['errors'][0]['code'] == Messages.Code.authentication_failed()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_one_location_returns_403_invalid_format(self, api_client, locations_table):
        self.permission(granted=False, message=Messages.Auth.invalid_format())
        location_id = locations_table[0].id
        response = api_client.get(f"{self.__get_url()}{location_id}")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.invalid_format()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_one_location_returns_403_auth_type_not_supported(self, api_client, locations_table):
        self.permission(granted=False, message=Messages.Auth.not_supported())
        location_id = locations_table[0].id
        response = api_client.get(f"{self.__get_url()}{location_id}")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.not_supported()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_one_location_returns_403_invalid_api_key(self, api_client, locations_table):
        self.permission(granted=False, message=Messages.Auth.invalid_api_key())
        location_id = locations_table[0].id
        response = api_client.get(f"{self.__get_url()}{location_id}")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == "detail"
        assert response.json()['errors'][0]['message'] == Messages.Auth.invalid_api_key()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_one_location_returns_403_not_enough_rights(self, api_client, locations_table):
        self.permission(granted=False, message=Messages.Auth.not_enough_rights())
        location_id = locations_table[0].id
        response = api_client.get(f"{self.__get_url()}{location_id}")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == "detail"
        assert response.json()['errors'][0]['message'] == Messages.Auth.not_enough_rights()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_one_location_returns_403_basic_auth_user_or_password_invalid(self, api_client, locations_table):
        self.permission(granted=False, message=Messages.Auth.user_or_password_invalid())
        location_id = locations_table[0].id
        response = api_client.get(f"{self.__get_url()}{location_id}")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.user_or_password_invalid()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_one_location_returns_403_basic_auth_user_not_found(self, api_client, locations_table):
        self.permission(granted=False, message=Messages.Auth.user_not_found())
        location_id = locations_table[0].id
        response = api_client.get(f"{self.__get_url()}{location_id}")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.user_not_found()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_one_location_returns_404_not_found(self, api_client):
        self.permission(granted=True)
        response = api_client.get(f"{self.__get_url()}999")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['message'] == Messages.Get.not_found("location", "999")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_one_location_returns_500_database_error_connection_lost(self, api_client, locations_table):
        self.permission(granted=True)
        self.connection_lost(Location, self.GET_ONE)
        location_id = locations_table[0].id
        response = api_client.get(f"{self.__get_url()}{location_id}")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Database.connection_lost()
        assert response.json()['errors'][0]['code'] == Messages.Code.connection_lost()
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_put_location_returns_200_ok(self, api_client, locations_table, location_put_payload_ok):
        self.permission(granted=True)
        location_id = locations_table[0].id
        response = api_client.put(f"{self.__get_url()}{location_id}", location_put_payload_ok, format='json')

        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.updated_successfully()
        assert response.json()['errors'] == None
        assert response.json()['data']['name'] == location_put_payload_ok["name"]
        assert response.status_code == status.HTTP_200_OK

    def test_put_location_returns_400_invalid_field(self, api_client, locations_table, location_put_payload_ok):
        self.permission(granted=True)
        location_id = locations_table[0].id
        location_put_payload_ok["new_field"] = "new_value"
        response = api_client.put(f"{self.__get_url()}{location_id}", location_put_payload_ok, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == "new_field"
        assert response.json()['errors'][0]['message'] == Messages.field_not_allowed()
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_put_location_returns_403_header_missing(self, api_client, locations_table):
        location_id = locations_table[0].id
        response = api_client.put(f"{self.__get_url()}{location_id}")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.header_missing()
        assert response.json()['errors'][0]['code'] == Messages.Code.authentication_failed()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_put_location_returns_403_invalid_format(self, api_client, locations_table):
        self.permission(granted=False, message=Messages.Auth.invalid_format())
        location_id = locations_table[0].id
        response = api_client.put(f"{self.__get_url()}{location_id}")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.invalid_format()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_put_location_returns_403_auth_type_not_supported(self, api_client, locations_table):
        self.permission(granted=False, message=Messages.Auth.not_supported())
        location_id = locations_table[0].id
        response = api_client.put(f"{self.__get_url()}{location_id}")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.not_supported()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_put_location_returns_403_invalid_api_key(self, api_client, locations_table, location_put_payload_ok):
        self.permission(granted=False, message=Messages.Auth.invalid_api_key())
        location_id = locations_table[0].id
        response = api_client.put(f"{self.__get_url()}{location_id}", location_put_payload_ok, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == "detail"
        assert response.json()['errors'][0]['message'] == Messages.Auth.invalid_api_key()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_put_location_returns_403_not_enough_rights(self, api_client, locations_table, location_put_payload_ok):
        self.permission(granted=False, message=Messages.Auth.not_enough_rights())
        location_id = locations_table[0].id
        response = api_client.put(f"{self.__get_url()}{location_id}", location_put_payload_ok, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == "detail"
        assert response.json()['errors'][0]['message'] == Messages.Auth.not_enough_rights()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_put_location_returns_403_basic_auth_user_or_password_invalid(self, api_client, locations_table):
        self.permission(granted=False, message=Messages.Auth.user_or_password_invalid())
        location_id = locations_table[0].id
        response = api_client.put(f"{self.__get_url()}{location_id}")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.user_or_password_invalid()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_put_location_returns_403_basic_auth_user_not_found(self, api_client, locations_table):
        self.permission(granted=False, message=Messages.Auth.user_not_found())
        location_id = locations_table[0].id
        response = api_client.put(f"{self.__get_url()}{location_id}")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.user_not_found()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_put_location_returns_404_not_found(self, api_client, location_put_payload_ok):
        self.permission(granted=True)
        response = api_client.put(f"{self.__get_url()}999", location_put_payload_ok, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['message'] == Messages.Put.not_found("location", "999")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_put_location_returns_500_database_error_connection_lost(self, api_client, locations_table, location_put_payload_ok):
        self.permission(granted=True)
        self.connection_lost(Location, self.PUT)
        location_id = locations_table[0].id
        response = api_client.put(f"{self.__get_url()}{location_id}", location_put_payload_ok, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Database.connection_lost()
        assert response.json()['errors'][0]['code'] == Messages.Code.connection_lost()
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_delete_location_returns_200_ok(self, api_client, locations_table):
        self.permission(granted=True)
        location_id = locations_table[0].id
        response = api_client.delete(f"{self.__get_url()}{location_id}")

        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.deleted_successfully()
        assert response.json()['errors'] == None
        assert response.json()['data']['message'] == Messages.Delete.deleted_one("location", str(location_id))
        assert response.status_code == status.HTTP_200_OK

    def test_delete_location_returns_403_header_missing(self, api_client, locations_table):
        location_id = locations_table[0].id
        response = api_client.delete(f"{self.__get_url()}{location_id}")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.header_missing()
        assert response.json()['errors'][0]['code'] == Messages.Code.authentication_failed()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_location_returns_403_invalid_format(self, api_client, locations_table):
        self.permission(granted=False, message=Messages.Auth.invalid_format())
        location_id = locations_table[0].id
        response = api_client.delete(f"{self.__get_url()}{location_id}")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.invalid_format()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_location_returns_403_auth_type_not_supported(self, api_client, locations_table):
        self.permission(granted=False, message=Messages.Auth.not_supported())
        location_id = locations_table[0].id
        response = api_client.delete(f"{self.__get_url()}{location_id}")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.not_supported()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_location_returns_403_invalid_api_key(self, api_client, locations_table):
        self.permission(granted=False, message=Messages.Auth.invalid_api_key())
        location_id = locations_table[0].id
        response = api_client.delete(f"{self.__get_url()}{location_id}")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == "detail"
        assert response.json()['errors'][0]['message'] == Messages.Auth.invalid_api_key()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_location_returns_403_not_enough_rights(self, api_client, locations_table):
        self.permission(granted=False, message=Messages.Auth.not_enough_rights())
        location_id = locations_table[0].id
        response = api_client.delete(f"{self.__get_url()}{location_id}")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == "detail"
        assert response.json()['errors'][0]['message'] == Messages.Auth.not_enough_rights()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_location_returns_403_basic_auth_user_or_password_invalid(self, api_client, locations_table):
        self.permission(granted=False, message=Messages.Auth.user_or_password_invalid())
        location_id = locations_table[0].id
        response = api_client.delete(f"{self.__get_url()}{location_id}")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.user_or_password_invalid()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_location_returns_403_basic_auth_user_not_found(self, api_client, locations_table):
        self.permission(granted=False, message=Messages.Auth.user_not_found())
        location_id = locations_table[0].id
        response = api_client.delete(f"{self.__get_url()}{location_id}")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.user_not_found()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_location_returns_404_not_found(self, api_client):
        self.permission(granted=True)
        response = api_client.delete(f"{self.__get_url()}999")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['message'] == Messages.Delete.not_found("location", "999")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_location_returns_500_database_error_connection_lost(self, api_client, locations_table):
        self.permission(granted=True)
        self.connection_lost(Location, self.DELETE)
        location_id = locations_table[0].id
        response = api_client.delete(f"{self.__get_url()}{location_id}")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Database.connection_lost()
        assert response.json()['errors'][0]['code'] == Messages.Code.connection_lost()
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_location_model_str_representation(self):
        test_name = "test_location"
        location = Location.objects.create(name=test_name)

        assert str(location) == test_name

    def __get_url(self):
        return f"/{LOCATIONS_URL_V1}"
