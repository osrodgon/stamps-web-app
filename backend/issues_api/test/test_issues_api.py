import pytest
from _backend.settings import ISSUES_URL_V1, ISSUES_COLLECTIONS_ENDPOINT
from stamps_api.models import Stamp
from common.api.messages import Messages
from common.test.abstract_api_unit_test import AbstractApiUnitTest
from common.test.api_client import api_client
from common.test.countries_api_test_data import countries_table
from common.test.issues_api_test_data import (
    issue_post_payload_ok,
    issue_put_payload_ok,
    issues_table,
    issue_collection_post_payload_ok,
    issue_collection_post_payload_minimal,
    issue_collection_post_payload_with_defaults,
    issue_collection_post_payload_invalid_required,
    issue_collection_post_payload_invalid_negative,
)
from common.test.locations_api_test_data import locations_table
from common.test.print_types_api_test_data import print_types_table
from common.test.stamp_types_api_test_data import stamp_types_table
from common.test.year_api_test_data import years_table
from django.db import connection
from rest_framework import status

from issues_api.api.serializers.issue_paginated_response_serializer import IssuePaginatedResponseSerializer
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
        assert len(response.json()['data']['issues']) == len(original.data)
        assert response.json()['data']['issues'] == original.data
        assert response.status_code == status.HTTP_200_OK
        
    def test_get_all_issues_returns_200_ok_no_data(self, api_client):
        self.permission(granted=True)
        response = api_client.get(self.__get_url())

        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.retrieved_successfully()
        assert response.json()['errors'] == None
        assert len(response.json()['data']['issues']) == 0
        assert response.status_code == status.HTTP_200_OK
        
    def test_get_all_issues_returns_403_header_missing(self, api_client):
        response = api_client.get(self.__get_url())

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.header_missing()
        assert response.json()['errors'][0]['code'] == Messages.Code.authentication_failed()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_all_issues_returns_403_invalid_format(self, api_client):
        self.permission(granted=False, message=Messages.Auth.invalid_format())
        response = api_client.get(self.__get_url())

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.invalid_format()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_all_issues_returns_403_auth_type_not_supported(self, api_client):
        self.permission(granted=False, message=Messages.Auth.not_supported())
        response = api_client.get(self.__get_url())

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.not_supported()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_all_issues_returns_403_invalid_api_key(self, api_client):
        self.permission(granted=False, message=Messages.Auth.invalid_api_key())
        response = api_client.get(self.__get_url())

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == "detail"
        assert response.json()['errors'][0]['message'] == Messages.Auth.invalid_api_key()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_all_issues_returns_403_not_enough_rights(self, api_client):
        self.permission(granted=False, message=Messages.Auth.not_enough_rights())
        response = api_client.get(self.__get_url())

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == "detail"
        assert response.json()['errors'][0]['message'] == Messages.Auth.not_enough_rights()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_all_issues_returns_403_basic_auth_user_or_password_invalid(self, api_client):
        self.permission(granted=False, message=Messages.Auth.user_or_password_invalid())
        response = api_client.get(self.__get_url())

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.user_or_password_invalid()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_all_issues_returns_403_basic_auth_user_not_found(self, api_client):
        self.permission(granted=False, message=Messages.Auth.user_not_found())
        response = api_client.get(self.__get_url())

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.user_not_found()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
    def test_get_all_issues_with_year_filter_returns_200_ok_data(self, api_client, issues_table):
        self.permission(granted=True)
        year_to_filter = issues_table[0].year.year
        url = f"{self.__get_url()}?year={year_to_filter}"
        response = api_client.get(url)
        
        issues = Issue.objects.filter(year__year=year_to_filter)
        original = IssueResponseSerializer(issues, many=True)

        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.retrieved_successfully()
        assert response.json()['errors'] == None
        assert len(response.json()['data']['issues']) == len(original.data)
        assert response.json()['data']['issues'] == original.data
        assert response.status_code == status.HTTP_200_OK
        
    def test_get_all_issues_with_year_range_filter_returns_200_ok_data(self, api_client, issues_table):
        self.permission(granted=True)    

        start_year = 2000
        end_year = 2022
        
        url = f"{self.__get_url()}?year={start_year}-{end_year}"
        response = api_client.get(url)
        
        issues = Issue.objects.filter(year__year__range=(start_year, end_year))
        original = IssueResponseSerializer(issues, many=True)

        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.retrieved_successfully()
        assert response.json()['errors'] == None
        assert len(response.json()['data']['issues']) == len(original.data)
        assert response.json()['data']['issues'] == original.data
        assert response.status_code == status.HTTP_200_OK

    def test_get_all_issues_with_invalid_year_filter_returns_200_ok_no_data(self, api_client, issues_table):
        self.permission(granted=True)
        url = f"{self.__get_url()}?year=192"
        response = api_client.get(url)

        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.retrieved_successfully()
        assert response.json()['errors'] == None
        assert len(response.json()['data']['issues']) == 0
        assert response.status_code == status.HTTP_200_OK
        
    def test_get_all_issues_with_name_filter_returns_200_ok_data(self, api_client, issues_table):
        self.permission(granted=True)
        name_to_filter = issues_table[0].name
        url = f"{self.__get_url()}?name={name_to_filter}"
        response = api_client.get(url)
        
        if connection.vendor == 'postgresql':
            issues = Issue.objects.filter(name__unaccent__icontains=name_to_filter)
        else:
            issues = Issue.objects.filter(name__icontains=name_to_filter)
        original = IssueResponseSerializer(issues, many=True)

        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.retrieved_successfully()
        assert response.json()['errors'] == None
        assert len(response.json()['data']['issues']) == len(original.data)
        assert response.json()['data']['issues'] == original.data
        assert response.status_code == status.HTTP_200_OK

    def test_get_all_issues_with_non_existing_name_filter_returns_200_ok_no_data(self, api_client, issues_table):
        self.permission(granted=True)
        url = f"{self.__get_url()}?name=non_existing_name"
        response = api_client.get(url)

        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.retrieved_successfully()
        assert response.json()['errors'] == None
        assert len(response.json()['data']['issues']) == 0
        assert response.status_code == status.HTTP_200_OK

    # @pytest.mark.skipif(connection.vendor != 'postgresql', reason='unaccent is a PostgreSQL feature')
    def test_get_all_issues_with_year_and_name_filter_returns_200_ok_data(self, api_client, issues_table):
        self.permission(granted=True)
        year_to_filter = issues_table[0].year.year
        name_to_filter = issues_table[0].name
        url = f"{self.__get_url()}?year={year_to_filter}&name={name_to_filter}"
        response = api_client.get(url)

        if connection.vendor == 'postgresql':
            issues = Issue.objects.filter(year__year=year_to_filter, name__unaccent__icontains=name_to_filter)
        else:
            issues = Issue.objects.filter(year__year=year_to_filter, name__icontains=name_to_filter)
        original = IssueResponseSerializer(issues, many=True)

        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.retrieved_successfully()
        assert response.json()['errors'] == None
        assert len(response.json()['data']['issues']) == len(original.data)
        assert response.json()['data']['issues'] == original.data
        assert response.status_code == status.HTTP_200_OK
        
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

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'new_field'
        assert response.json()['errors'][0]['message'] == Messages.field_not_allowed()
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_post_issue_returns_403_header_missing(self, api_client):
        response = api_client.post(self.__get_url())

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.header_missing()
        assert response.json()['errors'][0]['code'] == Messages.Code.authentication_failed()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_post_issue_returns_403_invalid_format(self, api_client):
        self.permission(granted=False, message=Messages.Auth.invalid_format())
        response = api_client.post(self.__get_url())

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.invalid_format()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_post_issue_returns_403_auth_type_not_supported(self, api_client):
        self.permission(granted=False, message=Messages.Auth.not_supported())
        response = api_client.post(self.__get_url())

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.not_supported()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_post_issue_returns_403_invalid_api_key(self, api_client, issue_post_payload_ok):
        self.permission(granted=False, message=Messages.Auth.invalid_api_key())
        response = api_client.post(self.__get_url(), issue_post_payload_ok, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == "detail"
        assert response.json()['errors'][0]['message'] == Messages.Auth.invalid_api_key()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_post_issue_returns_403_not_enough_rights(self, api_client, issue_post_payload_ok):
        self.permission(granted=False, message=Messages.Auth.not_enough_rights())
        response = api_client.post(self.__get_url(), issue_post_payload_ok, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == "detail"
        assert response.json()['errors'][0]['message'] == Messages.Auth.not_enough_rights()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_post_issue_returns_403_basic_auth_user_or_password_invalid(self, api_client):
        self.permission(granted=False, message=Messages.Auth.user_or_password_invalid())
        response = api_client.post(self.__get_url())

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.user_or_password_invalid()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_post_issue_returns_403_basic_auth_user_not_found(self, api_client):
        self.permission(granted=False, message=Messages.Auth.user_not_found())
        response = api_client.post(self.__get_url())

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.user_not_found()
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
        
    def test_get_one_issue_returns_200_ok_data(self, api_client, issues_table):
        self.permission(granted=True)
        issue_id = issues_table[0].id
        response = api_client.get(f"{self.__get_url()}{issue_id}/")

        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.retrieved_successfully()
        assert response.json()['errors'] == None
        assert response.json()['data']['name'] == issues_table[0].name
        assert response.status_code == status.HTTP_200_OK
        
    def test_get_one_issue_returns_403_header_missing(self, api_client, issues_table):
        issue_id = issues_table[0].id
        response = api_client.get(f"{self.__get_url()}{issue_id}/")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.header_missing()
        assert response.json()['errors'][0]['code'] == Messages.Code.authentication_failed()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_one_issue_returns_403_invalid_format(self, api_client, issues_table):
        self.permission(granted=False, message=Messages.Auth.invalid_format())
        issue_id = issues_table[0].id
        response = api_client.get(f"{self.__get_url()}{issue_id}/")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.invalid_format()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_one_issue_returns_403_auth_type_not_supported(self, api_client, issues_table):
        self.permission(granted=False, message=Messages.Auth.not_supported())
        issue_id = issues_table[0].id
        response = api_client.get(f"{self.__get_url()}{issue_id}/")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.not_supported()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_one_issue_returns_403_invalid_api_key(self, api_client, issues_table):
        self.permission(granted=False, message=Messages.Auth.invalid_api_key())
        issue_id = issues_table[0].id
        response = api_client.get(f"{self.__get_url()}{issue_id}/")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == "detail"
        assert response.json()['errors'][0]['message'] == Messages.Auth.invalid_api_key()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_one_issue_returns_403_not_enough_rights(self, api_client, issues_table):
        self.permission(granted=False, message=Messages.Auth.not_enough_rights())
        issue_id = issues_table[0].id
        response = api_client.get(f"{self.__get_url()}{issue_id}/")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == "detail"
        assert response.json()['errors'][0]['message'] == Messages.Auth.not_enough_rights()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_one_issue_returns_403_basic_auth_user_or_password_invalid(self, api_client, issues_table):
        self.permission(granted=False, message=Messages.Auth.user_or_password_invalid())
        issue_id = issues_table[0].id
        response = api_client.get(f"{self.__get_url()}{issue_id}/")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.user_or_password_invalid()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_one_issue_returns_403_basic_auth_user_not_found(self, api_client, issues_table):
        self.permission(granted=False, message=Messages.Auth.user_not_found())
        issue_id = issues_table[0].id
        response = api_client.get(f"{self.__get_url()}{issue_id}/")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.user_not_found()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_get_issue_returns_404_not_found(self, api_client):
        self.permission(granted=True)
        response = api_client.get(f"{self.__get_url()}999/")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['message'] == Messages.Get.not_found("issue", 999)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
    def test_get_issue_returns_500_database_error_connection_lost(self, api_client, issues_table):
        self.permission(granted=True)
        self.connection_lost(Issue, self.GET_ONE)
        issue_id = issues_table[0].id
        response = api_client.get(f"{self.__get_url()}{issue_id}/")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Database.connection_lost()
        assert response.json()['errors'][0]['code'] == Messages.Code.connection_lost()
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        
    def test_put_issue_returns_200_ok(self, api_client, issues_table, issue_put_payload_ok):
        self.permission(granted=True)
        issue_id = issues_table[0].id
        response = api_client.put(f"{self.__get_url()}{issue_id}/", issue_put_payload_ok, format='json')

        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.updated_successfully()
        assert response.json()['errors'] == None
        assert response.json()['data']['name'] == issue_put_payload_ok["name"]
        assert response.status_code == status.HTTP_200_OK
        
    def test_put_issue_returns_400_bad_request_invalid_field(self, api_client, issues_table, issue_put_payload_ok):
        self.permission(granted=True)
        issue_id = issues_table[0].id
        issue_put_payload_ok["new_field"] = "new_value"
        response = api_client.put(f"{self.__get_url()}{issue_id}/", issue_put_payload_ok, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'new_field'
        assert response.json()['errors'][0]['message'] == Messages.field_not_allowed()
        assert response.json()['errors'][0]['code'] == Messages.Code.invalid()
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_put_issue_returns_403_header_missing(self, api_client, issues_table):
        issue_id = issues_table[0].id
        response = api_client.put(f"{self.__get_url()}{issue_id}/")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.header_missing()
        assert response.json()['errors'][0]['code'] == Messages.Code.authentication_failed()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_put_issue_returns_403_invalid_format(self, api_client, issues_table):
        self.permission(granted=False, message=Messages.Auth.invalid_format())
        issue_id = issues_table[0].id
        response = api_client.put(f"{self.__get_url()}{issue_id}/")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.invalid_format()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_put_issue_returns_403_auth_type_not_supported(self, api_client, issues_table):
        self.permission(granted=False, message=Messages.Auth.not_supported())
        issue_id = issues_table[0].id
        response = api_client.put(f"{self.__get_url()}{issue_id}/")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.not_supported()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_put_issue_returns_403_invalid_api_key(self, api_client, issues_table, issue_put_payload_ok):
        self.permission(granted=False, message=Messages.Auth.invalid_api_key())
        issue_id = issues_table[0].id
        response = api_client.put(f"{self.__get_url()}{issue_id}/", issue_put_payload_ok)

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == "detail"
        assert response.json()['errors'][0]['message'] == Messages.Auth.invalid_api_key()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_put_issue_returns_403_not_enough_rights(self, api_client, issues_table, issue_put_payload_ok):
        self.permission(granted=False, message=Messages.Auth.not_enough_rights())
        issue_id = issues_table[0].id
        response = api_client.put(f"{self.__get_url()}{issue_id}/", issue_put_payload_ok)

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == "detail"
        assert response.json()['errors'][0]['message'] == Messages.Auth.not_enough_rights()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_put_issue_returns_403_basic_auth_user_or_password_invalid(self, api_client, issues_table):
        self.permission(granted=False, message=Messages.Auth.user_or_password_invalid())
        issue_id = issues_table[0].id
        response = api_client.put(f"{self.__get_url()}{issue_id}/")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.user_or_password_invalid()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_put_issue_returns_403_basic_auth_user_not_found(self, api_client, issues_table):
        self.permission(granted=False, message=Messages.Auth.user_not_found())
        issue_id = issues_table[0].id
        response = api_client.put(f"{self.__get_url()}{issue_id}/")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.user_not_found()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
    def test_put_issue_returns_404_not_found(self, api_client, issue_put_payload_ok):
        self.permission(granted=True)
        response = api_client.put(f"{self.__get_url()}999/", issue_put_payload_ok, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == None
        assert response.json()['errors'][0]['message'] == Messages.Put.not_found("issue", 999)
        assert response.json()['errors'][0]['code'] == Messages.Code.other()
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
    def test_put_issue_returns_500_database_error_connection_lost(self, api_client, issues_table, issue_put_payload_ok):
        self.permission(granted=True)
        self.connection_lost(Issue, self.PUT)
        issue_id = issues_table[0].id
        response = api_client.put(f"{self.__get_url()}{issue_id}/", issue_put_payload_ok, format='json')
        
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Database.connection_lost()
        assert response.json()['errors'][0]['code'] == Messages.Code.connection_lost()
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        
    def test_delete_issue_returns_200_ok(self, api_client, issues_table):
        self.permission(granted=True)
        issue_id = issues_table[0].id
        response = api_client.delete(f"{self.__get_url()}{issue_id}/")

        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.deleted_successfully()
        assert response.json()['errors'] == None
        assert response.json()['data']['message'] == Messages.Delete.deleted_one("issue", issue_id)
        assert response.status_code == status.HTTP_200_OK
        
    def test_delete_issue_returns_403_header_missing(self, api_client, issues_table):
        issue_id = issues_table[0].id
        response = api_client.delete(f"{self.__get_url()}{issue_id}/")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.header_missing()
        assert response.json()['errors'][0]['code'] == Messages.Code.authentication_failed()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_issue_returns_403_invalid_format(self, api_client, issues_table):
        self.permission(granted=False, message=Messages.Auth.invalid_format())
        issue_id = issues_table[0].id
        response = api_client.delete(f"{self.__get_url()}{issue_id}/")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.invalid_format()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_issue_returns_403_auth_type_not_supported(self, api_client, issues_table):
        self.permission(granted=False, message=Messages.Auth.not_supported())
        issue_id = issues_table[0].id
        response = api_client.delete(f"{self.__get_url()}{issue_id}/")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.not_supported()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_issue_returns_403_invalid_api_key(self, api_client, issues_table):
        self.permission(granted=False, message=Messages.Auth.invalid_api_key())
        issue_id = issues_table[0].id
        response = api_client.delete(f"{self.__get_url()}{issue_id}/")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == "detail"
        assert response.json()['errors'][0]['message'] == Messages.Auth.invalid_api_key()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_issue_returns_403_not_enough_rights(self, api_client, issues_table):
        self.permission(granted=False, message=Messages.Auth.not_enough_rights())
        issue_id = issues_table[0].id
        response = api_client.delete(f"{self.__get_url()}{issue_id}/")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == "detail"
        assert response.json()['errors'][0]['message'] == Messages.Auth.not_enough_rights()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_issue_returns_403_basic_auth_user_or_password_invalid(self, api_client, issues_table):
        self.permission(granted=False, message=Messages.Auth.user_or_password_invalid())
        issue_id = issues_table[0].id
        response = api_client.delete(f"{self.__get_url()}{issue_id}/")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.user_or_password_invalid()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_issue_returns_403_basic_auth_user_not_found(self, api_client, issues_table):
        self.permission(granted=False, message=Messages.Auth.user_not_found())
        issue_id = issues_table[0].id
        response = api_client.delete(f"{self.__get_url()}{issue_id}/")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.user_not_found()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
    def test_delete_issue_returns_404_not_found(self, api_client):
        self.permission(granted=True)
        response = api_client.delete(f"{self.__get_url()}999/")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == None
        assert response.json()['errors'][0]['message'] == Messages.Delete.not_found("issue", 999)
        assert response.json()['errors'][0]['code'] == Messages.Code.other()
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
    def test_delete_issue_returns_500_database_error_connection_lost(self, api_client, issues_table):
        self.permission(granted=True)
        self.connection_lost(Issue, self.DELETE)
        issue_id = issues_table[0].id
        response = api_client.delete(f"{self.__get_url()}{issue_id}/")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Database.connection_lost()
        assert response.json()['errors'][0]['code'] == Messages.Code.connection_lost()
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        
    def test_issue_model_str_representation(self, issues_table):
        issue = issues_table[0]
        assert str(issue) == f"{issue.name} ({issue.year.year})"
        
    # Tests for IssuesCollectionsView (POST /issues/collections/)
    def test_post_issue_collection_returns_201_created(self, api_client, issue_collection_post_payload_ok):
        """Test successful creation of issue collection with all related entities."""
        self.permission(granted=True)
        response = api_client.post(f"{self.__get_url()}{ISSUES_COLLECTIONS_ENDPOINT}", issue_collection_post_payload_ok, format='json')

        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.created_successfully()
        assert response.json()['errors'] == None
        assert response.json()['data']['issue_name'] == issue_collection_post_payload_ok["issue_name"]
        assert response.json()['data']['issue_date'] == issue_collection_post_payload_ok["issue_date"]
        assert response.status_code == status.HTTP_201_CREATED
        
    def test_post_issue_collection_returns_201_created_minimal(self, api_client, issue_collection_post_payload_minimal):
        """Test successful creation of issue collection with minimal required data."""
        self.permission(granted=True)
        response = api_client.post(f"{self.__get_url()}{ISSUES_COLLECTIONS_ENDPOINT}", issue_collection_post_payload_minimal, format='json')

        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.created_successfully()
        assert response.json()['errors'] == None
        assert response.json()['data']['issue_name'] == issue_collection_post_payload_minimal["issue_name"]
        assert response.status_code == status.HTTP_201_CREATED
        
    def test_post_issue_collection_returns_201_created_with_defaults(self, api_client, issue_collection_post_payload_with_defaults):
        """Test successful creation of issue collection using default values."""
        self.permission(granted=True)
        response = api_client.post(f"{self.__get_url()}{ISSUES_COLLECTIONS_ENDPOINT}", issue_collection_post_payload_with_defaults, format='json')

        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.created_successfully()
        assert response.json()['errors'] == None
        assert response.json()['data']['issue_name'] == issue_collection_post_payload_with_defaults["issue_name"]
        assert response.status_code == status.HTTP_201_CREATED
        
    def test_post_issue_collection_returns_400_bad_request_missing_issue_name(self, api_client, issue_collection_post_payload_invalid_required):
        """Test validation error when issue_name is missing."""
        self.permission(granted=True)
        response = api_client.post(f"{self.__get_url()}{ISSUES_COLLECTIONS_ENDPOINT}", issue_collection_post_payload_invalid_required, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'issue_name'
        assert response.json()['errors'][0]['message'] == Messages.field_required()
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
    def test_post_issue_collection_returns_400_bad_request_missing_issue_date(self, api_client, issue_collection_post_payload_ok):
        """Test validation error when issue_date is missing."""
        self.permission(granted=True)
        payload = issue_collection_post_payload_ok.copy()
        del payload["issue_date"]
        response = api_client.post(f"{self.__get_url()}{ISSUES_COLLECTIONS_ENDPOINT}", payload, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] is None
        assert response.json()['errors'][0]['message'] == "issue_date is required to create a Year record"
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
    def test_post_issue_collection_returns_400_bad_request_missing_stamps(self, api_client, issue_collection_post_payload_ok):
        """Test validation error when stamps list is missing."""
        self.permission(granted=True)
        payload = issue_collection_post_payload_ok.copy()
        del payload["stamps"]
        response = api_client.post(f"{self.__get_url()}{ISSUES_COLLECTIONS_ENDPOINT}", payload, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'stamps'
        assert response.json()['errors'][0]['message'] == Messages.field_required()
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
    def test_post_issue_collection_returns_400_bad_request_invalid_negative_values(self, api_client, issue_collection_post_payload_invalid_negative):
        """Test validation error when negative values are provided for numeric fields."""
        self.permission(granted=True)
        response = api_client.post(f"{self.__get_url()}{ISSUES_COLLECTIONS_ENDPOINT}", issue_collection_post_payload_invalid_negative, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == None
        assert response.json()['errors'][0]['message'] == "['total_printed']"
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
    def test_post_issue_collection_returns_400_bad_request_invalid_stamp_negative_values(self, api_client, issue_collection_post_payload_ok):
        """Test validation error when negative values are provided for stamp numeric fields."""
        self.permission(granted=True)
        payload = issue_collection_post_payload_ok.copy()
        payload['stamps'][0]['amount_printed'] = -100
        response = api_client.post(f"{self.__get_url()}{ISSUES_COLLECTIONS_ENDPOINT}", payload, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == None
        assert response.json()['errors'][0]['message'] == "['amount_printed']"
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
    def test_post_issue_collection_returns_400_bad_request_invalid_field(self, api_client, issue_collection_post_payload_ok):
        """Test validation error when invalid field is provided."""
        self.permission(granted=True)
        payload = issue_collection_post_payload_ok.copy()
        payload['invalid_field'] = 'invalid_value'
        response = api_client.post(f"{self.__get_url()}{ISSUES_COLLECTIONS_ENDPOINT}", payload, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'invalid_field'
        assert response.json()['errors'][0]['message'] == Messages.field_not_allowed()
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_post_issue_collection_returns_403_header_missing(self, api_client):
        """Test authentication error when API key header is missing."""
        response = api_client.post(f"{self.__get_url()}{ISSUES_COLLECTIONS_ENDPOINT}")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.header_missing()
        assert response.json()['errors'][0]['code'] == Messages.Code.authentication_failed()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_post_issue_collection_returns_403_invalid_format(self, api_client):
        """Test authentication error when API key format is invalid."""
        self.permission(granted=False, message=Messages.Auth.invalid_format())
        response = api_client.post(f"{self.__get_url()}{ISSUES_COLLECTIONS_ENDPOINT}")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.invalid_format()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_post_issue_collection_returns_403_auth_type_not_supported(self, api_client):
        """Test authentication error when auth type is not supported."""
        self.permission(granted=False, message=Messages.Auth.not_supported())
        response = api_client.post(f"{self.__get_url()}{ISSUES_COLLECTIONS_ENDPOINT}")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.not_supported()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_post_issue_collection_returns_403_invalid_api_key(self, api_client, issue_collection_post_payload_ok):
        """Test authentication error when API key is invalid."""
        self.permission(granted=False, message=Messages.Auth.invalid_api_key())
        response = api_client.post(f"{self.__get_url()}{ISSUES_COLLECTIONS_ENDPOINT}", issue_collection_post_payload_ok, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == "detail"
        assert response.json()['errors'][0]['message'] == Messages.Auth.invalid_api_key()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_post_issue_collection_returns_403_not_enough_rights(self, api_client, issue_collection_post_payload_ok):
        """Test authentication error when user doesn't have enough rights."""
        self.permission(granted=False, message=Messages.Auth.not_enough_rights())
        response = api_client.post(f"{self.__get_url()}{ISSUES_COLLECTIONS_ENDPOINT}", issue_collection_post_payload_ok, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == "detail"
        assert response.json()['errors'][0]['message'] == Messages.Auth.not_enough_rights()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_post_issue_collection_returns_403_basic_auth_user_or_password_invalid(self, api_client):
        """Test authentication error when basic auth user or password is invalid."""
        self.permission(granted=False, message=Messages.Auth.user_or_password_invalid())
        response = api_client.post(f"{self.__get_url()}{ISSUES_COLLECTIONS_ENDPOINT}")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.user_or_password_invalid()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_post_issue_collection_returns_403_basic_auth_user_not_found(self, api_client):
        """Test authentication error when basic auth user is not found."""
        self.permission(granted=False, message=Messages.Auth.user_not_found())
        response = api_client.post(f"{self.__get_url()}{ISSUES_COLLECTIONS_ENDPOINT}")

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.user_not_found()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN 
        
    def test_post_issue_collection_returns_500_database_error_connection_lost(self, api_client, issue_collection_post_payload_ok):
        """Test database error handling when connection is lost."""
        self.permission(granted=True)
        self.connection_lost(Stamp, self.POST)
        
        response = api_client.post(f"{self.__get_url()}{ISSUES_COLLECTIONS_ENDPOINT}", issue_collection_post_payload_ok, format='json')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Database.connection_lost()
        assert response.json()['errors'][0]['code'] == Messages.Code.connection_lost()
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            
    def test_post_issue_collection_creates_related_entities(self, api_client, issue_collection_post_payload_ok):
        """Test that all related entities are created correctly."""
        self.permission(granted=True)
        
        # Count entities before
        from years_api.models import Year
        from countries_api.models import Country
        from stamp_types_api.models import StampType
        from print_types_api.models import PrintType
        from artists_api.models import Artist
        from printers_api.models import Printer
        from paper_types_api.models import PaperType
        from stamps_api.models import Stamp
        from colors_api.models import Color
        from issues_api.models import Issue
        
        initial_years = Year.objects.count()
        initial_countries = Country.objects.count()
        initial_stamp_types = StampType.objects.count()
        initial_print_types = PrintType.objects.count()
        initial_artists = Artist.objects.count()
        initial_printers = Printer.objects.count()
        initial_paper_types = PaperType.objects.count()
        initial_issues = Issue.objects.count()
        initial_stamps = Stamp.objects.count()
        initial_colors = Color.objects.count()
        
        response = api_client.post(f"{self.__get_url()}{ISSUES_COLLECTIONS_ENDPOINT}", issue_collection_post_payload_ok, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        
        # Verify entities were created
        assert Year.objects.count() == initial_years + 1
        assert Country.objects.count() == initial_countries + 1
        assert StampType.objects.count() == initial_stamp_types + 1
        assert PrintType.objects.count() == initial_print_types + 1
        assert Artist.objects.count() == initial_artists + 1
        assert Printer.objects.count() == initial_printers + 1
        assert PaperType.objects.count() == initial_paper_types + 1
        assert Issue.objects.count() == initial_issues + 1
        assert Stamp.objects.count() == initial_stamps + 3  # 3 stamps in payload
        assert Color.objects.count() == initial_colors + 4  # 4 unique colors in payload (Rojo, Azul, Verde, Amarillo)
        
    def test_post_issue_collection_handles_entity_deduplication(self, api_client, issue_collection_post_payload_ok):
        """Test that existing entities are not duplicated."""
        self.permission(granted=True)
        
        # Create the same collection twice
        response1 = api_client.post(f"{self.__get_url()}{ISSUES_COLLECTIONS_ENDPOINT}", issue_collection_post_payload_ok, format='json')
        response2 = api_client.post(f"{self.__get_url()}{ISSUES_COLLECTIONS_ENDPOINT}", issue_collection_post_payload_ok, format='json')
        
        assert response1.status_code == status.HTTP_201_CREATED
        assert response2.status_code == status.HTTP_201_CREATED
        
        # Verify only one of each entity was created
        from years_api.models import Year
        from countries_api.models import Country
        from stamp_types_api.models import StampType
        from print_types_api.models import PrintType
        
        assert Year.objects.filter(year=1992).count() == 1
        assert Country.objects.filter(name="España").count() == 1
        assert StampType.objects.filter(name="Definitiva").count() == 1
        assert PrintType.objects.filter(name="Offset").count() == 1
        
    def test_post_issue_collection_handles_color_parsing(self, api_client, issue_collection_post_payload_ok):
        """Test that color strings are parsed correctly."""
        self.permission(granted=True)
        
        response = api_client.post(f"{self.__get_url()}{ISSUES_COLLECTIONS_ENDPOINT}", issue_collection_post_payload_ok, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        
        # Verify colors were created and associated correctly
        from colors_api.models import Color
        from stamps_api.models import Stamp
        
        # Check that colors were created with proper capitalization
        assert Color.objects.filter(name="Rojo").exists()
        assert Color.objects.filter(name="Azul").exists()
        assert Color.objects.filter(name="Verde").exists()
        assert Color.objects.filter(name="Amarillo").exists()
        
        # Check that stamps have correct color associations
        stamps = Stamp.objects.filter(edifil_code__in=['1234', '1235', '1236'])
        assert stamps.count() == 3
        
        # First stamp should have 1 color (rojo)
        stamp1 = stamps.get(edifil_code='1234')
        assert stamp1.colors.count() == 1
        assert stamp1.colors.first().name == "Rojo"
        
        # Second stamp should have 2 colors (azul, verde)
        stamp2 = stamps.get(edifil_code='1235')
        assert stamp2.colors.count() == 2
        colors2 = set(stamp2.colors.values_list('name', flat=True))
        assert colors2 == {"Azul", "Verde"}
        
        # Third stamp should have 3 colors (rojo, amarillo, azul)
        stamp3 = stamps.get(edifil_code='1236')
        assert stamp3.colors.count() == 3
        colors3 = set(stamp3.colors.values_list('name', flat=True))
        assert colors3 == {"Rojo", "Amarillo", "Azul"}
        
    def test_post_issue_collection_handles_image_path_generation(self, api_client, issue_collection_post_payload_ok):
        """Test that image paths are generated correctly for stamps."""
        self.permission(granted=True)
        
        response = api_client.post(f"{self.__get_url()}{ISSUES_COLLECTIONS_ENDPOINT}", issue_collection_post_payload_ok, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        
        # Verify image paths were generated correctly
        from stamps_api.models import Stamp
        
        stamp1 = Stamp.objects.get(edifil_code='1234')
        assert stamp1.image == "1992/1234.webp"
        
        stamp2 = Stamp.objects.get(edifil_code='1235')
        assert stamp2.image == "1992/1235.webp"
        
        stamp3 = Stamp.objects.get(edifil_code='1236')
        assert stamp3.image == "1992/1236.webp"
        
    def test_post_issue_collection_rollback_on_error(self, api_client, issue_collection_post_payload_ok):
        """Test that database transaction is rolled back on error."""
        self.permission(granted=True)
        
        # Modify payload to cause validation error in service
        payload = issue_collection_post_payload_ok.copy()
        payload['issue_name'] = ""  # Empty name should cause error
        
        response = api_client.post(f"{self.__get_url()}{ISSUES_COLLECTIONS_ENDPOINT}", payload, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        # Verify no entities were created
        from issues_api.models import Issue
        from stamps_api.models import Stamp
        
        assert Issue.objects.filter(name="").count() == 0
        assert Stamp.objects.count() == 0
        
    def __get_url(self):
        return f"/{ISSUES_URL_V1}"
        