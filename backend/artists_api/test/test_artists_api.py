from unittest.mock import patch
import pytest
from rest_framework import status

# Assuming a similar serializer structure as in other apps
from _backend.settings import ARTISTS_URL_V1
from artists_api.api.serializers.artist_response_serializer import ArtistResponseSerializer
from common.api.messages import Messages
from common.test.abstract_api_unit_test import AbstractApiUnitTest
from common.test.api_client import api_client
from common.test.artists_api_test_data import (
    artists_table,
    artist_post_payload_ok,
    artist_put_payload_ok,
)
from artists_api.models import Artist


@pytest.mark.django_db
class TestArtistsAPI(AbstractApiUnitTest):
    def test_get_all_artists_returns_200_ok_data(self, api_client, artists_table):
        self.permission(granted=True)
        response = api_client.get(self.__get_url())
        
        original = ArtistResponseSerializer(artists_table, many=True)
        
        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.retrieved_successfully()
        assert response.json()['errors'] == None
        assert len(response.json()['data']) == len(artists_table)
        assert response.json()['data'] == original.data
        assert response.status_code == status.HTTP_200_OK
        
    def test_get_all_artists_returns_200_ok_no_data(self, api_client):
        self.permission(granted=True)
        response = api_client.get(self.__get_url())
        
        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.retrieved_successfully()
        assert response.json()['errors'] == None
        assert len(response.json()['data']) == 0
        assert response.status_code == status.HTTP_200_OK
        
    def test_get_all_artists_returns_403_header_missing(self, api_client):
        response = api_client.get(self.__get_url())
        
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.header_missing()
        assert response.json()['errors'][0]['code'] == Messages.Code.authentication_failed()
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
    def test_get_all_artists_returns_403_invalid_format(self, api_client):
        self.permission(granted=False, message=Messages.Auth.invalid_format())
        response = api_client.get(self.__get_url())
        
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.invalid_format()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
    def test_get_all_artists_returns_403_auth_type_not_supported(self, api_client):
        self.permission(granted=False, message=Messages.Auth.not_supported())
        response = api_client.get(self.__get_url())
        
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.not_supported()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
    def test_get_all_artists_returns_403_invalid_api_key(self, api_client):
        self.permission(granted=False, message=Messages.Auth.invalid_api_key())
        response = api_client.get(self.__get_url())
        
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.invalid_api_key()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
    def test_get_all_artists_returns_403_not_enough_rights(self, api_client):
        self.permission(granted=False, message=Messages.Auth.not_enough_rights())
        response = api_client.get(self.__get_url())
        
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.not_enough_rights()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
    def test_get_all_artists_returns_403_basic_auth_user_or_password_invalid(self, api_client):
        self.permission(granted=False, message=Messages.Auth.user_or_password_invalid())
        response = api_client.get(self.__get_url())
        
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.user_or_password_invalid()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
    def test_get_all_artists_returns_403_basic_auth_user_not_found(self, api_client):
        self.permission(granted=False, message=Messages.Auth.user_not_found())
        response = api_client.get(self.__get_url())
        
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.user_not_found()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
    def test_get_all_artists_returns_500_database_error_connection_lost(self, api_client):
        self.permission(granted=True)
        self.connection_lost(Artist, self.GET_ALL)
        response = api_client.get(self.__get_url())

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Database.connection_lost()
        assert response.json()['errors'][0]['code'] == Messages.Code.connection_lost()
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_post_artist_returns_201_created(self, api_client, artist_post_payload_ok):
        self.permission(granted=True)
        response = api_client.post(self.__get_url(), artist_post_payload_ok)
        
        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.created_successfully()
        assert response.json()['errors'] == None
        assert response.json()['data']['name'] == artist_post_payload_ok['name']
        assert response.status_code == status.HTTP_201_CREATED

    def test_post_artist_returns_400_bad_request_invalid_payload_missing_name(self, api_client):
        self.permission(granted=True)
        response = api_client.post(self.__get_url(), {})
        
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == "name"
        assert response.json()['errors'][0]['message'] == Messages.field_required()
        assert response.json()['errors'][0]['code'] == Messages.Code.required()
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
    def test_post_artist_returns_400_bad_request_invalid_payload_field_not_allowed(self, api_client, artist_post_payload_ok):
        self.permission(granted=True)
        artist_post_payload_ok['invalid_field'] = 'value'
        response = api_client.post(self.__get_url(), artist_post_payload_ok)
        
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == "invalid_field"
        assert response.json()['errors'][0]['message'] == Messages.field_not_allowed()
        assert response.json()['errors'][0]['code'] == Messages.Code.invalid()
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_post_artist_returns_400_bad_request_duplicate_name(self, api_client, artists_table):
        self.permission(granted=True)
        response = api_client.post(self.__get_url(), {'name': artists_table[0].name})
        
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == "name"
        assert response.json()['errors'][0]['message'] == Messages.Post.already_exists("artist", 'name')  
        assert response.json()['errors'][0]['code'] == Messages.Code.unique()
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
    def test_post_artist_returns_403_header_missing(self, api_client):
        response = api_client.get(self.__get_url())
        
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.header_missing()
        assert response.json()['errors'][0]['code'] == Messages.Code.authentication_failed()
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
    def test_post_artist_returns_403_invalid_format(self, api_client):
        self.permission(granted=False, message=Messages.Auth.invalid_format())
        response = api_client.get(self.__get_url())
        
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.invalid_format()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
    def test_post_artist_returns_403_auth_type_not_supported(self, api_client):
        self.permission(granted=False, message=Messages.Auth.not_supported())
        response = api_client.get(self.__get_url())
        
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.not_supported()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
    def test_post_artist_returns_403_invalid_api_key(self, api_client):
        self.permission(granted=False, message=Messages.Auth.invalid_api_key())
        response = api_client.get(self.__get_url())
        
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.invalid_api_key()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
    def test_post_artist_returns_403_not_enough_rights(self, api_client):
        self.permission(granted=False, message=Messages.Auth.not_enough_rights())
        response = api_client.get(self.__get_url())
        
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.not_enough_rights()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
    def test_post_artist_returns_403_basic_auth_user_or_password_invalid(self, api_client):
        self.permission(granted=False, message=Messages.Auth.user_or_password_invalid())
        response = api_client.get(self.__get_url())
        
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.user_or_password_invalid()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
    def test_post_artist_returns_403_basic_auth_user_not_found(self, api_client):
        self.permission(granted=False, message=Messages.Auth.user_not_found())
        response = api_client.get(self.__get_url())
        
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.user_not_found()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
    def test_post_artist_returns_500_database_error_connection_lost(self, api_client, artist_post_payload_ok):
        self.permission(granted=True)
        self.connection_lost(Artist, self.POST)
        response = api_client.post(self.__get_url(), artist_post_payload_ok)

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Database.connection_lost()
        assert response.json()['errors'][0]['code'] == Messages.Code.connection_lost()
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_get_one_artist_returns_200_ok_data(self, api_client, artists_table):
        self.permission(granted=True)
        id = str(artists_table[0].id)
        response = api_client.get(self.__get_url() + id)

        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.retrieved_successfully()
        assert response.json()['errors'] == None
        assert response.json()['data']['name'] == artists_table[0].name
        assert response.status_code == status.HTTP_200_OK
        
    def test_get_one_artist_returns_403_header_missing(self, api_client):
        response = api_client.get(self.__get_url())
        
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.header_missing()
        assert response.json()['errors'][0]['code'] == Messages.Code.authentication_failed()
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
    def test_get_one_artist_returns_403_invalid_format(self, api_client):
        self.permission(granted=False, message=Messages.Auth.invalid_format())
        response = api_client.get(self.__get_url())
        
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.invalid_format()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
    def test_get_one_artist_returns_403_auth_type_not_supported(self, api_client):
        self.permission(granted=False, message=Messages.Auth.not_supported())
        response = api_client.get(self.__get_url())
        
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.not_supported()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
    def test_get_one_artist_returns_403_invalid_api_key(self, api_client):
        self.permission(granted=False, message=Messages.Auth.invalid_api_key())
        response = api_client.get(self.__get_url())
        
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.invalid_api_key()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
    def test_get_one_artist_returns_403_not_enough_rights(self, api_client):
        self.permission(granted=False, message=Messages.Auth.not_enough_rights())
        response = api_client.get(self.__get_url())
        
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.not_enough_rights()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
    def test_get_one_artist_returns_403_basic_auth_user_or_password_invalid(self, api_client):
        self.permission(granted=False, message=Messages.Auth.user_or_password_invalid())
        response = api_client.get(self.__get_url())
        
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.user_or_password_invalid()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
    def test_get_one_artist_returns_403_basic_auth_user_not_found(self, api_client):
        self.permission(granted=False, message=Messages.Auth.user_not_found())
        response = api_client.get(self.__get_url())
        
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.user_not_found()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_one_artist_returns_404_not_found(self, api_client):
        self.permission(granted=True)
        response = api_client.get(self.__get_url() + "999")
        
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == None
        assert response.json()['errors'][0]['message'] == Messages.Get.not_found("artist", "999")
        assert response.json()['errors'][0]['code'] == Messages.Code.other()
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
    def test_get_one_artist_returns_500_database_error_connection_lost(self, api_client, artists_table):
        self.permission(granted=True)
        self.connection_lost(Artist, self.GET_ONE)
        id = str(artists_table[0].id)
        response = api_client.get(self.__get_url() + id)

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Database.connection_lost()
        assert response.json()['errors'][0]['code'] == Messages.Code.connection_lost()
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_put_artist_returns_200_ok(self, api_client, artists_table,  artist_put_payload_ok):
        self.permission(granted=True)
        id = str(artists_table[0].id)
        response = api_client.put(self.__get_url() + id, artist_put_payload_ok)
        
        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.updated_successfully()
        assert response.json()['errors'] == None
        assert response.json()['data']['name'] == artist_put_payload_ok['name']
        assert response.status_code == status.HTTP_200_OK

    def test_put_artist_returns_400_bad_request_duplicate_name(self, api_client, artists_table):
        self.permission(granted=True)
        id = str(artists_table[0].id)
        response = api_client.put(self.__get_url() + id, {'name': artists_table[1].name})
        
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == "name"
        assert response.json()['errors'][0]['message'] == Messages.Put.already_exists("artist", artists_table[1].name) 
        assert response.json()['errors'][0]['code'] == Messages.Code.unique()
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
    def test_put_artist_returns_403_header_missing(self, api_client):
        response = api_client.get(self.__get_url())
        
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.header_missing()
        assert response.json()['errors'][0]['code'] == Messages.Code.authentication_failed()
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
    def test_put_artist_returns_403_invalid_format(self, api_client):
        self.permission(granted=False, message=Messages.Auth.invalid_format())
        response = api_client.get(self.__get_url())
        
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.invalid_format()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
    def test_put_artist_returns_403_auth_type_not_supported(self, api_client):
        self.permission(granted=False, message=Messages.Auth.not_supported())
        response = api_client.get(self.__get_url())
        
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.not_supported()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
    def test_put_artist_returns_403_invalid_api_key(self, api_client):
        self.permission(granted=False, message=Messages.Auth.invalid_api_key())
        response = api_client.get(self.__get_url())
        
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.invalid_api_key()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
    def test_put_artist_returns_403_not_enough_rights(self, api_client):
        self.permission(granted=False, message=Messages.Auth.not_enough_rights())
        response = api_client.get(self.__get_url())
        
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.not_enough_rights()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
    def test_put_artist_returns_403_basic_auth_user_or_password_invalid(self, api_client):
        self.permission(granted=False, message=Messages.Auth.user_or_password_invalid())
        response = api_client.get(self.__get_url())
        
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.user_or_password_invalid()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
    def test_put_artist_returns_403_basic_auth_user_not_found(self, api_client):
        self.permission(granted=False, message=Messages.Auth.user_not_found())
        response = api_client.get(self.__get_url())
        
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.user_not_found()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
    def test_put_artist_returns_404_not_found(self, api_client):
        self.permission(granted=True)
        response = api_client.put(self.__get_url() + "999", {'name': 'New Name'})
        
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == None
        assert response.json()['errors'][0]['message'] == Messages.Put.not_found("artist", "999")
        assert response.json()['errors'][0]['code'] == Messages.Code.other()
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
    def test_put_artist_returns_500_database_error_connection_lost(self, api_client, artists_table, artist_put_payload_ok):
        self.permission(granted=True)
        self.connection_lost(Artist, self.PUT)
        id = str(artists_table[0].id)
        response = api_client.put(self.__get_url() + id, artist_put_payload_ok)

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Database.connection_lost()
        assert response.json()['errors'][0]['code'] == Messages.Code.connection_lost()
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        
    def test_delete_artist_returns_200_ok(self, api_client, artists_table):
        self.permission(granted=True)
        id = str(artists_table[0].id)
        response = api_client.delete(self.__get_url() + id)
        
        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.deleted_successfully()
        assert response.json()['errors'] == None
        assert response.json()['data']['message'] == Messages.Delete.deleted_one("artist", "1")
        assert response.status_code == status.HTTP_200_OK
        
    def test_delete_artist_returns_403_header_missing(self, api_client):
        response = api_client.get(self.__get_url())
        
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.header_missing()
        assert response.json()['errors'][0]['code'] == Messages.Code.authentication_failed()
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
    def test_delete_artist_returns_403_invalid_format(self, api_client):
        self.permission(granted=False, message=Messages.Auth.invalid_format())
        response = api_client.get(self.__get_url())
        
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.invalid_format()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
    def test_delete_artist_returns_403_auth_type_not_supported(self, api_client):
        self.permission(granted=False, message=Messages.Auth.not_supported())
        response = api_client.get(self.__get_url())
        
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.not_supported()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
    def test_delete_artist_returns_403_invalid_api_key(self, api_client):
        self.permission(granted=False, message=Messages.Auth.invalid_api_key())
        response = api_client.get(self.__get_url())
        
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.invalid_api_key()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
    def test_delete_artist_returns_403_not_enough_rights(self, api_client):
        self.permission(granted=False, message=Messages.Auth.not_enough_rights())
        response = api_client.get(self.__get_url())
        
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.not_enough_rights()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
    def test_delete_artist_returns_403_basic_auth_user_or_password_invalid(self, api_client):
        self.permission(granted=False, message=Messages.Auth.user_or_password_invalid())
        response = api_client.get(self.__get_url())
        
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.user_or_password_invalid()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
    def test_delete_artist_returns_403_basic_auth_user_not_found(self, api_client):
        self.permission(granted=False, message=Messages.Auth.user_not_found())
        response = api_client.get(self.__get_url())
        
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Auth.user_not_found()
        assert response.json()['errors'][0]['code'] == Messages.Code.permission_denied()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_artist_returns_404_not_found(self, api_client):
        self.permission(granted=True)
        response = api_client.delete(self.__get_url() + "999")
        
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == None
        assert response.json()['errors'][0]['message'] == Messages.Delete.not_found("artist", "999")
        assert response.json()['errors'][0]['code'] == Messages.Code.other()
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
    def test_delete_artist_returns_500_database_error_connection_lost(self, api_client, artists_table):
        self.permission(granted=True)
        self.connection_lost(Artist, self.DELETE)
        id = str(artists_table[0].id)
        response = api_client.delete(self.__get_url() + id)

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Database.connection_lost()
        assert response.json()['errors'][0]['code'] == Messages.Code.connection_lost()
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_artist_model_str_representation(self):
        test_name = "test_name"
        artist = Artist.objects.create(
            name=test_name
        )
        
        assert str(artist) == test_name
        
    def __get_url(self):
        return f"/{ARTISTS_URL_V1}"