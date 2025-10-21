import pytest
from rest_framework import status

from _backend.settings import STAMPS_URL_V1
from common.api.messages import Messages
from common.test.abstract_api_unit_test import AbstractApiUnitTest
from common.test.api_client import api_client
from common.test.stamps_api_test_data import (
    stamps_table,
    stamp_post_payload_ok,
    stamp_put_payload_ok
)
from common.test.year_api_test_data import years_table
from common.test.countries_api_test_data import countries_table
from common.test.stamp_types_api_test_data import stamp_types_table
from common.test.paper_types_api_test_data import paper_types_table
from common.test.locations_api_test_data import locations_table
from common.test.issues_api_test_data import issues_table
from common.test.colors_api_test_data import colors_table

from stamps_api.api.serializers.stamp_response_serializer import StampResponseSerializer
from stamps_api.models import Stamp


@pytest.mark.django_db
class TestStampsAPI(AbstractApiUnitTest):
    def test_get_all_stamps_returns_200_ok_data(self, api_client, stamps_table):
        self.permission(granted=True)
        response = api_client.get(self.__get_url())

        original = StampResponseSerializer(stamps_table, many=True)

        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.retrieved_successfully()
        assert response.json()['errors'] == None
        assert len(response.json()['data']) == len(original.data)
        assert response.json()['data'] == original.data
        assert response.status_code == status.HTTP_200_OK

    def test_get_all_stamps_returns_200_ok_no_data(self, api_client):
        self.permission(granted=True)
        response = api_client.get(self.__get_url())

        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.retrieved_successfully()
        assert response.json()['errors'] == None
        assert len(response.json()['data']) == 0
        assert response.status_code == status.HTTP_200_OK

    def test_get_all_stamps_returns_403_invalid_key(self, api_client):
        self.permission(granted=False, message=Messages.APIKey.invalid_key())
        response = api_client.get(self.__get_url())

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.APIKey.invalid_key()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_all_stamps_returns_403_invalid_user(self, api_client):
        self.permission(granted=False, message=Messages.APIKey.invalid_user())
        response = api_client.get(self.__get_url())

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.APIKey.invalid_user()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_all_stamps_returns_500_database_error_connection_lost(self, api_client):
        self.permission(granted=True)
        self.connection_lost(Stamp, self.GET_ALL)
        response = api_client.get(self.__get_url())

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Database.connection_lost()
        assert response.json()['errors'][0]['code'] == Messages.Code.connection_lost()
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_post_stamp_returns_201_created(self, api_client, stamp_post_payload_ok):
        self.permission(granted=True)
        response = api_client.post(self.__get_url(), stamp_post_payload_ok, format='json')

        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.created_successfully()
        assert response.json()['errors'] == None
        assert response.json()['data']['name'] == stamp_post_payload_ok["name"]
        assert response.json()['data']['edifil_code'] == stamp_post_payload_ok["edifil_code"]
        assert response.status_code == status.HTTP_201_CREATED

    def test_post_stamp_returns_400_missing_field(self, api_client, stamp_post_payload_ok):
        self.permission(granted=True)
        del stamp_post_payload_ok["name"]
        response = api_client.post(self.__get_url(), stamp_post_payload_ok, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == "name"
        assert response.json()['errors'][0]['message'] == Messages.field_required()
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_post_stamp_returns_400_invalid_field(self, api_client, stamp_post_payload_ok):
        self.permission(granted=True)
        stamp_post_payload_ok['new_field'] = 'new_value'
        response = api_client.post(self.__get_url(), stamp_post_payload_ok, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == "new_field"
        assert response.json()['errors'][0]['message'] == Messages.field_not_allowed()
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_post_stamp_returns_403_invalid_key(self, api_client, stamp_post_payload_ok):
        self.permission(granted=False, message=Messages.APIKey.invalid_key())
        response = api_client.post(self.__get_url(), stamp_post_payload_ok, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.APIKey.invalid_key()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_post_stamp_returns_403_invalid_user(self, api_client, stamp_post_payload_ok):
        self.permission(granted=False, message=Messages.APIKey.invalid_user())
        response = api_client.post(self.__get_url(), stamp_post_payload_ok, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.APIKey.invalid_user()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_post_stamp_returns_500_database_error_connection_lost(self, api_client, stamp_post_payload_ok):
        self.permission(granted=True)
        self.connection_lost(Stamp, self.POST)
        response = api_client.post(self.__get_url(), stamp_post_payload_ok, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Database.connection_lost()
        assert response.json()['errors'][0]['code'] == Messages.Code.connection_lost()
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_get_one_stamp_returns_200_ok(self, api_client, stamps_table):
        self.permission(granted=True)
        stamp_id = stamps_table[0].id
        response = api_client.get(f"{self.__get_url()}{stamp_id}")

        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.retrieved_successfully()
        assert response.json()['errors'] == None
        assert response.json()['data']['name'] == stamps_table[0].name
        assert response.status_code == status.HTTP_200_OK

    def test_get_one_stamp_returns_403_invalid_key(self, api_client, stamps_table):
        self.permission(granted=False, message=Messages.APIKey.invalid_key())
        stamp_id = stamps_table[0].id
        response = api_client.get(f"{self.__get_url()}{stamp_id}")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.APIKey.invalid_key()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_one_stamp_returns_403_invalid_user(self, api_client, stamps_table):
        self.permission(granted=False, message=Messages.APIKey.invalid_user())
        stamp_id = stamps_table[0].id
        response = api_client.get(f"{self.__get_url()}{stamp_id}")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.APIKey.invalid_user()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_one_stamp_returns_404_not_found(self, api_client):
        self.permission(granted=True)
        response = api_client.get(f"{self.__get_url()}999")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['message'] == Messages.Get.not_found("stamp", "999")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_one_stamp_returns_500_database_error_connection_lost(self, api_client, stamps_table):
        self.permission(granted=True)
        self.connection_lost(Stamp, self.GET_ONE)
        stamp_id = stamps_table[0].id
        response = api_client.get(f"{self.__get_url()}{stamp_id}")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Database.connection_lost()
        assert response.json()['errors'][0]['code'] == Messages.Code.connection_lost()
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_put_stamp_returns_200_ok(self, api_client, stamps_table, stamp_put_payload_ok):
        self.permission(granted=True)
        stamp_id = stamps_table[0].id
        response = api_client.put(f"{self.__get_url()}{stamp_id}", stamp_put_payload_ok, format='json')

        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.updated_successfully()
        assert response.json()['errors'] == None
        assert response.json()['data']['name'] == stamp_put_payload_ok["name"]
        assert response.status_code == status.HTTP_200_OK

    def test_put_stamp_returns_400_invalid_field(self, api_client, stamps_table, stamp_put_payload_ok):
        self.permission(granted=True)
        stamp_id = stamps_table[0].id
        stamp_put_payload_ok["new_field"] = "new_value"
        response = api_client.put(f"{self.__get_url()}{stamp_id}", stamp_put_payload_ok, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == "new_field"
        assert response.json()['errors'][0]['message'] == Messages.field_not_allowed()
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_put_stamp_returns_403_invalid_key(self, api_client, stamps_table, stamp_put_payload_ok):
        self.permission(granted=False, message=Messages.APIKey.invalid_key())
        stamp_id = stamps_table[0].id
        response = api_client.put(f"{self.__get_url()}{stamp_id}", stamp_put_payload_ok, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.APIKey.invalid_key()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_put_stamp_returns_403_invalid_user(self, api_client, stamps_table, stamp_put_payload_ok):
        self.permission(granted=False, message=Messages.APIKey.invalid_user())
        stamp_id = stamps_table[0].id
        response = api_client.put(f"{self.__get_url()}{stamp_id}", stamp_put_payload_ok, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.APIKey.invalid_user()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_put_stamp_returns_404_not_found(self, api_client, stamp_put_payload_ok):
        self.permission(granted=True)
        response = api_client.put(f"{self.__get_url()}999", stamp_put_payload_ok, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['message'] == Messages.Put.not_found("stamp", "999")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_put_stamp_returns_500_database_error_connection_lost(self, api_client, stamps_table, stamp_put_payload_ok):
        self.permission(granted=True)
        self.connection_lost(Stamp, self.PUT)
        stamp_id = stamps_table[0].id
        response = api_client.put(f"{self.__get_url()}{stamp_id}", stamp_put_payload_ok, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Database.connection_lost()
        assert response.json()['errors'][0]['code'] == Messages.Code.connection_lost()
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_delete_stamp_returns_200_ok(self, api_client, stamps_table):
        self.permission(granted=True)
        stamp_id = stamps_table[0].id
        response = api_client.delete(f"{self.__get_url()}{stamp_id}")

        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.deleted_successfully()
        assert response.json()['errors'] == None
        assert response.json()['data']['message'] == Messages.Delete.deleted_one("stamp", stamp_id)
        assert response.status_code == status.HTTP_200_OK

    def test_delete_stamp_returns_403_invalid_key(self, api_client, stamps_table):
        self.permission(granted=False, message=Messages.APIKey.invalid_key())
        stamp_id = stamps_table[0].id
        response = api_client.delete(f"{self.__get_url()}{stamp_id}")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.APIKey.invalid_key()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_stamp_returns_403_invalid_user(self, api_client, stamps_table):
        self.permission(granted=False, message=Messages.APIKey.invalid_user())
        stamp_id = stamps_table[0].id
        response = api_client.delete(f"{self.__get_url()}{stamp_id}")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.APIKey.invalid_user()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_stamp_returns_404_not_found(self, api_client):
        self.permission(granted=True)
        response = api_client.delete(f"{self.__get_url()}999")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['message'] == Messages.Delete.not_found("stamp", "999")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_stamp_returns_500_database_error_connection_lost(self, api_client, stamps_table):
        self.permission(granted=True)
        self.connection_lost(Stamp, self.DELETE)
        stamp_id = stamps_table[0].id
        response = api_client.delete(f"{self.__get_url()}{stamp_id}")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Database.connection_lost()
        assert response.json()['errors'][0]['code'] == Messages.Code.connection_lost()
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_stamp_model_str_representation(self, stamps_table, issues_table):
        test_name = "test_name"
        test_edifil_code = "A000"

        stamp = Stamp.objects.create(
            name=test_name,
            edifil_code=test_edifil_code,
            issue=issues_table[0],
        )

        assert str(stamp) == f"{test_edifil_code} - {test_name}"

    def __get_url(self):
        return f"/{STAMPS_URL_V1}"