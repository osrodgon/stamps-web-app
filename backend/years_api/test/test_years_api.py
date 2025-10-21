import pytest
from rest_framework import status

from _backend.settings import YEARS_URL_V1
from common.api.messages import Messages
from common.test.abstract_api_unit_test import AbstractApiUnitTest
from years_api.models import Year
from years_api.api.serializers.year_response_serializer import YearResponseSerializer
from common.test.api_client import api_client
from common.test.year_api_test_data import (
    years_table,
    year_post_payload_ok,
    year_put_payload_ok
)

@pytest.mark.django_db
class TestYearsAPI(AbstractApiUnitTest):
    def test_get_all_years_returns_200_ok_data(self, api_client, years_table):
        self.permission(granted=True)
        response = api_client.get(self.__get_url())

        original = YearResponseSerializer(years_table,many=True)

        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.retrieved_successfully()
        assert response.json()['errors'] == None
        assert len(response.json()['data']) == len(original.data)
        assert response.json()['data'] == original.data
        assert response.status_code == status.HTTP_200_OK

    def test_get_all_years_returns_200_ok_no_data(self, api_client):
        self.permission(granted=True)
        response = api_client.get(self.__get_url())

        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.retrieved_successfully()
        assert response.json()['errors'] == None
        assert len(response.json()['data']) == 0
        assert response.status_code == status.HTTP_200_OK

    def test_get_all_years_returns_403_invalid_key(self, api_client):
        self.permission(granted=False, message=Messages.APIKey.invalid_key())
        response = api_client.get(self.__get_url())

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.APIKey.invalid_key()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_all_years_returns_403_invalid_user(self, api_client):
        self.permission(granted=False, message=Messages.APIKey.invalid_user())
        response = api_client.get(self.__get_url())

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.APIKey.invalid_user()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_all_years_returns_500_database_error_connection_lost(self, api_client):
        self.permission(granted=True)
        self.connection_lost(Year, self.GET_ALL)
        response = api_client.get(self.__get_url())

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Database.connection_lost()
        assert response.json()['errors'][0]['code'] == Messages.Code.connection_lost()
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_post_year_returns_201_created(self, api_client, year_post_payload_ok):
        self.permission(granted=True)
        response = api_client.post(self.__get_url(), year_post_payload_ok, format='json')

        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.created_successfully()
        assert response.json()['errors'] == None
        assert response.json()['data']['year'] == year_post_payload_ok["year"]
        assert response.status_code == status.HTTP_201_CREATED

    def test_post_year_returns_400_missing_field(self, api_client, year_post_payload_ok):
        self.permission(granted=True)
        del year_post_payload_ok["year"]
        response = api_client.post(self.__get_url(), year_post_payload_ok, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == "year"
        assert response.json()['errors'][0]['message'] == Messages.field_required()
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_post_year_returns_400_invalid_field(self, api_client, year_post_payload_ok):
        self.permission(granted=True)
        year_post_payload_ok['new_field'] = 'new_value'
        response = api_client.post(self.__get_url(), year_post_payload_ok, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == "new_field"
        assert response.json()['errors'][0]['message'] == Messages.field_not_allowed()
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_post_year_returns_403_invalid_key(self, api_client, year_post_payload_ok):
        self.permission(granted=False, message=Messages.APIKey.invalid_key())
        response = api_client.post(self.__get_url(), year_post_payload_ok, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.APIKey.invalid_key()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_post_year_returns_403_invalid_user(self, api_client, year_post_payload_ok):
        self.permission(granted=False, message=Messages.APIKey.invalid_user())
        response = api_client.post(self.__get_url(), year_post_payload_ok, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.APIKey.invalid_user()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_post_year_returns_500_database_error_connection_lost(self, api_client, year_post_payload_ok):
        self.permission(granted=True)
        self.connection_lost(Year, self.POST)
        response = api_client.post(self.__get_url(), year_post_payload_ok, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Database.connection_lost()
        assert response.json()['errors'][0]['code'] == Messages.Code.connection_lost()
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_get_one_year_returns_200_ok(self, api_client, years_table):
        self.permission(granted=True)
        year_id = years_table[0].id
        response = api_client.get(f"{self.__get_url()}{year_id}")

        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.retrieved_successfully()
        assert response.json()['errors'] == None
        assert response.json()['data']['year'] == years_table[0].year
        assert response.status_code == status.HTTP_200_OK

    def test_get_one_year_returns_403_invalid_key(self, api_client, years_table):
        self.permission(granted=False, message=Messages.APIKey.invalid_key())
        year_id = years_table[0].id
        response = api_client.get(f"{self.__get_url()}{year_id}")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.APIKey.invalid_key()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_one_year_returns_403_invalid_user(self, api_client, years_table):
        self.permission(granted=False, message=Messages.APIKey.invalid_user())
        year_id = years_table[0].id
        response = api_client.get(f"{self.__get_url()}{year_id}")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.APIKey.invalid_user()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_one_year_returns_404_not_found(self, api_client):
        self.permission(granted=True)
        response = api_client.get(f"{self.__get_url()}999")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['message'] == Messages.Get.not_found("year", "999")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_one_year_returns_500_database_error_connection_lost(self, api_client, years_table):
        self.permission(granted=True)
        self.connection_lost(Year, self.GET_ONE)
        year_id = years_table[0].id
        response = api_client.get(f"{self.__get_url()}{year_id}")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Database.connection_lost()
        assert response.json()['errors'][0]['code'] == Messages.Code.connection_lost()
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_put_year_returns_200_ok(self, api_client, years_table, year_put_payload_ok):
        self.permission(granted=True)
        year_id = years_table[0].id
        response = api_client.put(f"{self.__get_url()}{year_id}", year_put_payload_ok, format='json')

        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.updated_successfully()
        assert response.json()['errors'] == None
        assert response.json()['data']['year'] == year_put_payload_ok["year"]
        assert response.status_code == status.HTTP_200_OK

    def test_put_year_returns_400_invalid_field(self, api_client, years_table, year_put_payload_ok):
        self.permission(granted=True)
        year_id = years_table[0].id
        year_put_payload_ok["new_field"] = "new_value"
        response = api_client.put(f"{self.__get_url()}{year_id}", year_put_payload_ok, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == "new_field"
        assert response.json()['errors'][0]['message'] == Messages.field_not_allowed()
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_put_year_returns_403_invalid_key(self, api_client, years_table, year_put_payload_ok):
        self.permission(granted=False, message=Messages.APIKey.invalid_key())
        year_id = years_table[0].id
        response = api_client.put(f"{self.__get_url()}{year_id}", year_put_payload_ok, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.APIKey.invalid_key()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_put_year_returns_403_invalid_user(self, api_client, years_table, year_put_payload_ok):
        self.permission(granted=False, message=Messages.APIKey.invalid_user())
        year_id = years_table[0].id
        response = api_client.put(f"{self.__get_url()}{year_id}", year_put_payload_ok, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.APIKey.invalid_user()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_put_year_returns_404_not_found(self, api_client, year_put_payload_ok):
        self.permission(granted=True)
        response = api_client.put(f"{self.__get_url()}999", year_put_payload_ok, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['message'] == Messages.Put.not_found("year", "999")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_put_year_returns_500_database_error_connection_lost(self, api_client, years_table, year_put_payload_ok):
        self.permission(granted=True)
        self.connection_lost(Year, self.PUT)
        year_id = years_table[0].id
        response = api_client.put(f"{self.__get_url()}{year_id}", year_put_payload_ok, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Database.connection_lost()
        assert response.json()['errors'][0]['code'] == Messages.Code.connection_lost()
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_delete_year_returns_200_ok(self, api_client, years_table):
        self.permission(granted=True)
        year_id = years_table[0].id
        response = api_client.delete(f"{self.__get_url()}{year_id}")

        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.deleted_successfully()
        assert response.json()['errors'] == None
        assert response.json()['data']['message'] == Messages.Delete.deleted_one("year", str(year_id))
        assert response.status_code == status.HTTP_200_OK

    def test_delete_year_returns_403_invalid_key(self, api_client, years_table):
        self.permission(granted=False, message=Messages.APIKey.invalid_key())
        year_id = years_table[0].id
        response = api_client.delete(f"{self.__get_url()}{year_id}")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.APIKey.invalid_key()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_year_returns_403_invalid_user(self, api_client, years_table):
        self.permission(granted=False, message=Messages.APIKey.invalid_user())
        year_id = years_table[0].id
        response = api_client.delete(f"{self.__get_url()}{year_id}")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.APIKey.invalid_user()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_year_returns_404_not_found(self, api_client):
        self.permission(granted=True)
        response = api_client.delete(f"{self.__get_url()}999")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['message'] == Messages.Delete.not_found("year", "999")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_year_returns_500_database_error_connection_lost(self, api_client, years_table):
        self.permission(granted=True)
        self.connection_lost(Year, self.DELETE)
        year_id = years_table[0].id
        response = api_client.delete(f"{self.__get_url()}{year_id}")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Database.connection_lost()
        assert response.json()['errors'][0]['code'] == Messages.Code.connection_lost()
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_year_model_str_representation(self):
        test_year_value = 2024
        year = Year.objects.create(year=test_year_value)

        assert str(year) == str(test_year_value)

    def __get_url(self):
        return f"/{YEARS_URL_V1}"