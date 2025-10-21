import pytest
from rest_framework import status

from _backend.settings import PAPER_TYPES_URL_V1
from common.api.messages import Messages
from common.test.abstract_api_unit_test import AbstractApiUnitTest
from common.test.api_client import api_client
from common.test.paper_types_api_test_data import (
    paper_types_table,
    paper_type_post_payload_ok,
    paper_type_put_payload_ok,
)
from paper_types_api.models import PaperType
from paper_types_api.api.serializers.paper_type_response_serializer import (
    PaperTypeResponseSerializer,
)


@pytest.mark.django_db
class TestPaperTypesAPI(AbstractApiUnitTest):
    def test_get_all_paper_types_returns_200_ok_data(self, api_client, paper_types_table):
        self.permission(granted=True)
        response = api_client.get(self.__get_url())

        original = PaperTypeResponseSerializer(paper_types_table, many=True)

        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.retrieved_successfully()
        assert response.json()['errors'] == None
        assert len(response.json()['data']) == len(original.data)
        assert response.json()['data'] == original.data
        assert response.status_code == status.HTTP_200_OK

    def test_get_all_paper_types_returns_200_ok_no_data(self, api_client):
        self.permission(granted=True)
        response = api_client.get(self.__get_url())

        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.retrieved_successfully()
        assert response.json()['errors'] == None
        assert len(response.json()['data']) == 0
        assert response.status_code == status.HTTP_200_OK

    def test_get_all_paper_types_returns_403_invalid_key(self, api_client):
        self.permission(granted=False, message=Messages.APIKey.invalid_key())
        response = api_client.get(self.__get_url())

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.APIKey.invalid_key()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_all_paper_types_returns_403_invalid_user(self, api_client):
        self.permission(granted=False, message=Messages.APIKey.invalid_user())
        response = api_client.get(self.__get_url())

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.APIKey.invalid_user()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_all_paper_types_returns_500_database_error_connection_lost(self, api_client):
        self.permission(granted=True)
        self.connection_lost(PaperType, self.GET_ALL)
        response = api_client.get(self.__get_url())

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Database.connection_lost()
        assert response.json()['errors'][0]['code'] == Messages.Code.connection_lost()
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_post_paper_type_returns_201_created(self, api_client, paper_type_post_payload_ok):
        self.permission(granted=True)
        response = api_client.post(self.__get_url(), paper_type_post_payload_ok, format='json')

        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.created_successfully()
        assert response.json()['errors'] == None
        assert response.json()['data']['name'] == paper_type_post_payload_ok["name"]
        assert response.status_code == status.HTTP_201_CREATED

    def test_post_paper_type_returns_400_missing_field(self, api_client, paper_type_post_payload_ok):
        self.permission(granted=True)
        del paper_type_post_payload_ok["name"]
        response = api_client.post(self.__get_url(), paper_type_post_payload_ok, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == "name"
        assert response.json()['errors'][0]['message'] == Messages.field_required()
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_post_paper_type_returns_400_invalid_field(self, api_client, paper_type_post_payload_ok):
        self.permission(granted=True)
        paper_type_post_payload_ok["new_field"] = "new_value"
        response = api_client.post(self.__get_url(), paper_type_post_payload_ok, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == "new_field"
        assert response.json()['errors'][0]['message'] == Messages.field_not_allowed()
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_post_paper_type_returns_403_invalid_key(self, api_client, paper_type_post_payload_ok):
        self.permission(granted=False, message=Messages.APIKey.invalid_key())
        response = api_client.post(self.__get_url(), paper_type_post_payload_ok, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.APIKey.invalid_key()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_post_paper_type_returns_403_invalid_user(self, api_client, paper_type_post_payload_ok):
        self.permission(granted=False, message=Messages.APIKey.invalid_user())
        response = api_client.post(self.__get_url(), paper_type_post_payload_ok, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.APIKey.invalid_user()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_post_paper_type_returns_500_database_error_connection_lost(self, api_client, paper_type_post_payload_ok):
        self.permission(granted=True)
        self.connection_lost(PaperType, self.POST)
        response = api_client.post(self.__get_url(), paper_type_post_payload_ok, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Database.connection_lost()
        assert response.json()['errors'][0]['code'] == Messages.Code.connection_lost()
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_get_one_paper_type_returns_200_ok(self, api_client, paper_types_table):
        self.permission(granted=True)
        paper_type_id = paper_types_table[0].id
        response = api_client.get(f"{self.__get_url()}{paper_type_id}")

        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.retrieved_successfully()
        assert response.json()['errors'] == None
        assert response.json()['data']['name'] == paper_types_table[0].name
        assert response.status_code == status.HTTP_200_OK

    def test_get_one_paper_type_returns_403_invalid_key(self, api_client, paper_types_table):
        self.permission(granted=False, message=Messages.APIKey.invalid_key())
        paper_type_id = paper_types_table[0].id
        response = api_client.get(f"{self.__get_url()}{paper_type_id}")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.APIKey.invalid_key()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_one_paper_type_returns_403_invalid_user(self, api_client, paper_types_table):
        self.permission(granted=False, message=Messages.APIKey.invalid_user())
        paper_type_id = paper_types_table[0].id
        response = api_client.get(f"{self.__get_url()}{paper_type_id}")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.APIKey.invalid_user()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_one_paper_type_returns_404_not_found(self, api_client):
        self.permission(granted=True)
        response = api_client.get(f"{self.__get_url()}999")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['message'] == Messages.Get.not_found("paper type", "999")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_one_paper_type_returns_500_database_error_connection_lost(self, api_client, paper_types_table):
        self.permission(granted=True)
        self.connection_lost(PaperType, self.GET_ONE)
        paper_type_id = paper_types_table[0].id
        response = api_client.get(f"{self.__get_url()}{paper_type_id}")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Database.connection_lost()
        assert response.json()['errors'][0]['code'] == Messages.Code.connection_lost()
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_put_paper_type_returns_200_ok(self, api_client, paper_types_table, paper_type_put_payload_ok):
        self.permission(granted=True)
        paper_type_id = paper_types_table[0].id
        response = api_client.put(f"{self.__get_url()}{paper_type_id}", paper_type_put_payload_ok, format='json')

        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.updated_successfully()
        assert response.json()['errors'] == None
        assert response.json()['data']['name'] == paper_type_put_payload_ok["name"]
        assert response.status_code == status.HTTP_200_OK

    def test_put_paper_type_returns_400_invalid_field(self, api_client, paper_types_table, paper_type_put_payload_ok):
        self.permission(granted=True)
        paper_type_id = paper_types_table[0].id
        paper_type_put_payload_ok["new_field"] = "new_value"
        response = api_client.put(f"{self.__get_url()}{paper_type_id}", paper_type_put_payload_ok, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == "new_field"
        assert response.json()['errors'][0]['message'] == Messages.field_not_allowed()
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_put_paper_type_returns_403_invalid_key(self, api_client, paper_types_table, paper_type_put_payload_ok):
        self.permission(granted=False, message=Messages.APIKey.invalid_key())
        paper_type_id = paper_types_table[0].id
        response = api_client.put(f"{self.__get_url()}{paper_type_id}", paper_type_put_payload_ok, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.APIKey.invalid_key()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_put_paper_type_returns_403_invalid_user(self, api_client, paper_types_table, paper_type_put_payload_ok):
        self.permission(granted=False, message=Messages.APIKey.invalid_user())
        paper_type_id = paper_types_table[0].id
        response = api_client.put(f"{self.__get_url()}{paper_type_id}", paper_type_put_payload_ok, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.APIKey.invalid_user()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_put_paper_type_returns_404_not_found(self, api_client, paper_type_put_payload_ok):
        self.permission(granted=True)
        response = api_client.put(f"{self.__get_url()}999", paper_type_put_payload_ok, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['message'] == Messages.Put.not_found("paper type", "999")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_put_paper_type_returns_500_database_error_connection_lost(self, api_client, paper_types_table, paper_type_put_payload_ok):
        self.permission(granted=True)
        self.connection_lost(PaperType, self.PUT)
        paper_type_id = paper_types_table[0].id
        response = api_client.put(f"{self.__get_url()}{paper_type_id}", paper_type_put_payload_ok, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Database.connection_lost()
        assert response.json()['errors'][0]['code'] == Messages.Code.connection_lost()
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_delete_paper_type_returns_200_ok(self, api_client, paper_types_table):
        self.permission(granted=True)
        paper_type_id = paper_types_table[0].id
        response = api_client.delete(f"{self.__get_url()}{paper_type_id}")

        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.deleted_successfully()
        assert response.json()['errors'] == None
        assert response.json()['data']['message'] == Messages.Delete.deleted_one("paper type", str(paper_type_id))
        assert response.status_code == status.HTTP_200_OK

    def test_delete_paper_type_returns_403_invalid_key(self, api_client, paper_types_table):
        self.permission(granted=False, message=Messages.APIKey.invalid_key())
        paper_type_id = paper_types_table[0].id
        response = api_client.delete(f"{self.__get_url()}{paper_type_id}")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.APIKey.invalid_key()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_paper_type_returns_403_invalid_user(self, api_client, paper_types_table):
        self.permission(granted=False, message=Messages.APIKey.invalid_user())
        paper_type_id = paper_types_table[0].id
        response = api_client.delete(f"{self.__get_url()}{paper_type_id}")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.APIKey.invalid_user()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_paper_type_returns_404_not_found(self, api_client):
        self.permission(granted=True)
        response = api_client.delete(f"{self.__get_url()}999")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['message'] == Messages.Delete.not_found("paper type", "999")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_paper_type_returns_500_database_error_connection_lost(self, api_client, paper_types_table):
        self.permission(granted=True)
        self.connection_lost(PaperType, self.DELETE)
        paper_type_id = paper_types_table[0].id
        response = api_client.delete(f"{self.__get_url()}{paper_type_id}")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Database.connection_lost()
        assert response.json()['errors'][0]['code'] == Messages.Code.connection_lost()
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_paper_type_model_str_representation(self):
        test_name = "test_paper_type"
        paper_type = PaperType.objects.create(name=test_name)

        assert str(paper_type) == test_name

    def __get_url(self):
        return f"/{PAPER_TYPES_URL_V1}"
