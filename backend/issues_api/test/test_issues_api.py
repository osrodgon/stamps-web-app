import os
from unittest.mock import patch
from urllib import response
import pytest
from rest_framework import status

from _backend.settings import ISSUES_URL_V1
from common.api.messages import Messages
from common.test.abstract_api_unit_test import AbstractApiUnitTest
from common.test.api_client import api_client
from common.test.issues_api_test_data import (
    issues_table,
    issue_post_payload_ok,
    issue_put_payload_ok
)
from common.test.year_api_test_data import years_table
from common.test.countries_api_test_data import countries_table
from common.test.stamp_types_api_test_data import stamp_types_table
from common.test.paper_types_api_test_data import paper_types_table
from common.test.locations_api_test_data import locations_table

from issues_api.api.serializers.issue_response_serializer import IssueResponseSerializer
from issues_api.models import Issue


@pytest.mark.django_db
class TestIssuesAPI(AbstractApiUnitTest):
    def test_get_all_issues_returns_200_ok_data(self, api_client, issues_table):
        self.permission(granted=True)
        response = api_client.get(self.__get_url())

        original = IssueResponseSerializer(issues_table, many=True)

        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.retrieved_successfully()
        assert response.json()['errors'] == None
        assert len(response.json()['data']) == len(original.data)
        assert response.json()['data'] == original.data
        assert response.status_code == status.HTTP_200_OK
        
    def test_get_all_issues_returns_200_ok_no_data(self, api_client):
        self.permission(granted=True)
        response = api_client.get(self.__get_url())

        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.retrieved_successfully()
        assert response.json()['errors'] == None
        assert len(response.json()['data']) == 0
        assert response.status_code == status.HTTP_200_OK
        
    def test_get_all_issues_returns_403_invalid_key(self, api_client, issues_table):
        self.permission(granted=False, message=Messages.APIKey.invalid_key())
        response = api_client.get(self.__get_url())

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.APIKey.invalid_key()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
    def test_get_all_issues_returns_403_invalid_user(self, api_client, issues_table):
        self.permission(granted=False, message=Messages.APIKey.invalid_user())
        response = api_client.get(self.__get_url())

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.APIKey.invalid_user()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
    def test_get_all_issues_returns_500_database_error_connection_lost(self, api_client, issues_table):
        self.permission(granted=True)
        self.connection_lost(Issue, self.GET_ALL)
        response = api_client.get(self.__get_url())

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Database.connection_lost()
        assert response.json()['errors'][0]['code'] == Messages.Code.connection_lost()
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        
    def test_post_issue_returns_201_created(self, api_client, issue_post_payload_ok):
        self.permission(granted=True)
        response = api_client.post(self.__get_url(), issue_post_payload_ok, format='json')

        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.created_successfully()
        assert response.json()['errors'] == None
        assert response.json()['data']['name'] == issue_post_payload_ok["name"]
        assert response.status_code == status.HTTP_201_CREATED
        
    def test_post_issue_returns_400_bad_request_missing_name(self, api_client, issue_post_payload_ok):
        self.permission(granted=True)
        del issue_post_payload_ok["name"]
        response = api_client.post(self.__get_url(), issue_post_payload_ok, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'name'
        assert response.json()['errors'][0]['message'] == Messages.field_required()
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
    def test_post_issue_returns_400_bad_request_invalid_field(self, api_client, issue_post_payload_ok):
        self.permission(granted=True)
        issue_post_payload_ok['new_field'] = 'new_value'
        response = api_client.post(self.__get_url(), issue_post_payload_ok, format='json')

        assert response.json()['success'] is False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] is None
        assert response.json()['errors'][0]['field'] == 'new_field'
        assert response.json()['errors'][0]['message'] == Messages.field_not_allowed()
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    def test_post_issue_returns_403_invalid_key(self, api_client, issue_post_payload_ok):
        self.permission(granted=False, message=Messages.APIKey.invalid_key())
        response = api_client.post(self.__get_url(), issue_post_payload_ok, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.APIKey.invalid_key()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
    def test_post_issue_returns_403_invalid_user(self, api_client, issue_post_payload_ok):
        self.permission(granted=False, message=Messages.APIKey.invalid_user())
        response = api_client.post(self.__get_url(), issue_post_payload_ok, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.APIKey.invalid_user()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN 
        
    def test_post_issue_returns_500_database_error_connection_lost(self, api_client, issue_post_payload_ok):
        self.permission(granted=True)
        self.connection_lost(Issue, self.POST)
        response = api_client.post(self.__get_url(), issue_post_payload_ok, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Database.connection_lost()
        assert response.json()['errors'][0]['code'] == Messages.Code.connection_lost()
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        
    def test_get_issue_returns_data_200_ok(self, api_client, issues_table):
        issue_id = issues_table[0].id
        response = api_client.get(f"{self.__get_url()}{issue_id}/")

        assert response.json()['success'] is True
        assert response.json()['message'] == Messages.retrieved_successfully()
        assert response.json()['errors'] is None
        assert response.json()['data']['name'] == issues_table[0].name
        assert response.status_code == status.HTTP_200_OK
    
    def test_get_issue_returns_no_data_404_not_found(self, api_client):
        response = api_client.get(f"{self.__get_url()}999/")

        assert response.json()['success'] is False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] is None
        assert response.json()['errors'][0]['message'] == Messages.Get.not_found("issue", 999)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
    def test_put_issue_updates_record_200_ok(self, api_client, issues_table, issue_put_payload_ok):
        issue_id = issues_table[0].id
        response = api_client.put(f"{self.__get_url()}{issue_id}/", issue_put_payload_ok, format='json')

        assert response.json()['success'] is True
        assert response.json()['message'] == Messages.updated_successfully()
        assert response.json()['errors'] is None
        assert response.json()['data']['name'] == issue_put_payload_ok["name"]
        assert response.status_code == status.HTTP_200_OK
        
    def test_put_issue_updates_record_404_not_found(self, api_client, issue_put_payload_ok):
        response = api_client.put(f"{self.__get_url()}999/", issue_put_payload_ok, format='json')

        assert response.json()['success'] is False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] is None
        assert response.json()['errors'][0]['message'] == Messages.Put.not_found("issue", 999)
        assert response.status_code == status.HTTP_404_NOT_FOUND
       
    def test_put_issue_updates_record_400_bad_request(self, api_client, issues_table, issue_put_payload_ok):
        issue_id = issues_table[0].id
        issue_put_payload_ok["new_field"] = "new_value"
        response = api_client.put(f"{self.__get_url()}{issue_id}/", issue_put_payload_ok, format='json')

        assert response.json()['success'] is False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] is None
        assert response.json()['errors'][0]['field'] == 'new_field'
        assert response.json()['errors'][0]['message'] == Messages.field_not_allowed()
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
    def test_delete_issue_deletes_record_200_ok(self, api_client, issues_table):
        issue_id = issues_table[0].id
        response = api_client.delete(f"{self.__get_url()}{issue_id}/")

        assert response.json()['success'] is True
        assert response.json()['message'] == Messages.deleted_successfully()
        assert response.json()['errors'] is None
        assert response.json()['data']['message'] == Messages.Delete.deleted_one("issue", issue_id)
        assert response.status_code == status.HTTP_200_OK
        
    def test_delete_issue_deletes_record_404_not_found(self, api_client):
        response = api_client.delete(f"{self.__get_url()}999/")

        assert response.json()['success'] is False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] is None
        assert response.json()['errors'][0]['message'] == Messages.Delete.not_found("issue", 999)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
    @patch('issues_api.api.views.issues_by_id_view.Issue.objects.get')
    def test_delete_issue_deletes_record_database_error(self, mock_get, api_client, issues_table):
        issue_id = issues_table[0].id
        mock_get.side_effect = Exception("Database connection lost")
        response = api_client.delete(f"{self.__get_url()}{issue_id}/")

        assert response.json()['success'] is False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['errors'][0]['message'] == Messages.server_error()
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        
    def test_issue_model_str_representation(self, issues_table):
        issue = issues_table[0]
        assert str(issue) == f"{issue.name} ({issue.year.year})"
        
    def __get_url(self):
        return f"/{ISSUES_URL_V1}"
        