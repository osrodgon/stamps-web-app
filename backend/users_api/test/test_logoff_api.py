from email import header
from urllib import response
import pytest
from rest_framework import status
from _backend.settings import LOGOFF_URL_V1
from common.api.messages import Messages
from common.test.abstract_api_unit_test import AbstractApiUnitTest
from common.test.api_client import api_client
from users_api.models import UserToken

@pytest.mark.django_db
class TestLogoffAPI(AbstractApiUnitTest):
    def test_logoff_returns_200_ok(self, api_client):
        self.validate_password_user_found()
        self.validate_password_match(match=True)
        self.validate_jwt_token(valid=True)
        self.get_user_token(exist=True)
        response = api_client.post(self.__get_url(), HTTP_AUTHORIZATION='jwt fake-jwt-token')
        self.delete_user_token()
        
        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.success()
        assert response.json()['data'] == Messages.Post.logoff()
        assert response.json()['errors'] == None
        assert response.status_code == status.HTTP_200_OK
        
    def test_logoff_returns_400_bad_request_header_missing(self, api_client):
        response = api_client.post(self.__get_url())

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == None
        assert response.json()['errors'][0]['message'] == Messages.Auth.header_missing()
        assert response.json()['errors'][0]['code'] == Messages.Code.other()
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
    def test_logoff_returns_400_bad_request_invalid_format(self, api_client):
        response = api_client.post(self.__get_url(), HTTP_AUTHORIZATION='a-fake-auth-header')
        
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == None
        assert response.json()['errors'][0]['message'] == Messages.Auth.invalid_format()
        assert response.json()['errors'][0]['code'] == Messages.Code.other()
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
    def test_logoff_returns_400_bad_request_not_supported(self, api_client):
        response = api_client.post(self.__get_url(), HTTP_AUTHORIZATION='basic fake-token')

        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == None
        assert response.json()['errors'][0]['message'] == Messages.Auth.not_supported()
        assert response.json()['errors'][0]['code'] == Messages.Code.other()
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        
    def test_logoff_returns_401_unauthorized_invalid_jwt(self, api_client):
        self.validate_password_user_found()
        self.validate_password_match(match=True)
        self.validate_jwt_token(valid=False)
        response = api_client.post(self.__get_url(), HTTP_AUTHORIZATION='jwt fake-jwt-token')
        
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == None
        assert response.json()['errors'][0]['message'] == Messages.Auth.invalid_jwt()
        assert response.json()['errors'][0]['code'] == Messages.Code.other()
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
    def test_logoff_returns_401_unauthorized_user_not_found(self, api_client):
        self.validate_password_user_found()
        self.validate_password_match(match=True)
        self.validate_jwt_token(valid=True)
        self.get_user_token(exist=False)
        response = api_client.post(self.__get_url(), HTTP_AUTHORIZATION='jwt fake-jwt-token')
        
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == None
        assert response.json()['errors'][0]['message'] == Messages.Auth.user_not_found()
        assert response.json()['errors'][0]['code'] == Messages.Code.other()
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
    def test_logoff_returns_500_internal_server_error(self, api_client):
        self.validate_password_user_found()
        self.validate_password_match(match=True)
        self.validate_jwt_token(valid=True)
        self.get_user_token(exist=True)
        self.connection_lost(UserToken, self.GET_ONE)
        response = api_client.post(self.__get_url(), HTTP_AUTHORIZATION='jwt fake-jwt-token')
        
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Database.connection_lost()
        assert response.json()['errors'][0]['code'] == Messages.Code.connection_lost()
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        
    def __get_url(self):
        return f"/{LOGOFF_URL_V1}"