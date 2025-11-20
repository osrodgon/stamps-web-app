import pytest
from rest_framework import status
from _backend.settings import LOGIN_URL_V1
from common.api.messages import Messages
from common.test.abstract_api_unit_test import AbstractApiUnitTest
from common.test.api_client import api_client
from common.test.users_api_test_data import users_table
from common.test.login_api_test_data import login_api_payload_ok, login_api_response_ok
from users_api.models import UserCollection

@pytest.mark.django_db
class TestLoginAPI(AbstractApiUnitTest):
    def test_login_returns_200_ok(self, api_client, login_api_payload_ok, users_table ):
        self.validate_password_user_found()
        self.validate_password_match()
        self.create_jwt_token(success=True)
        
        response = api_client.post(self.__get_url(), login_api_payload_ok, format='json')
        
        assert response.json()['success'] == True
        assert response.json()['message'] == Messages.success()
        assert response.json()['errors'] == None
        assert response.json()['data'] == login_api_response_ok()
        assert response.status_code == status.HTTP_200_OK
        
    def test_login_returns_400_bad_request_missing_field(self, api_client, login_api_payload_ok):
        self.validate_password_user_found()
        self.validate_password_match()
        self.create_jwt_token(success=True)
        del(login_api_payload_ok["username"])
        
        response = api_client.post(self.__get_url(), login_api_payload_ok, format='json')
        
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == "username"
        assert response.json()['errors'][0]['message'] == Messages.field_required()
        assert response.json()['errors'][0]['code'] == Messages.Code.required()
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
    def test_login_returns_400_bad_request_invalid_field(self, api_client, login_api_payload_ok):
        self.validate_password_user_found()
        self.validate_password_match()
        self.create_jwt_token(success=True)
        login_api_payload_ok["new_field"] = "new value"
        
        response = api_client.post(self.__get_url(), login_api_payload_ok, format='json')
        
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == "new_field"
        assert response.json()['errors'][0]['message'] == Messages.field_not_allowed()
        assert response.json()['errors'][0]['code'] == Messages.Code.invalid()
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_returns_401_unauthorized_user_not_found(self, api_client, login_api_payload_ok ):
        self.validate_password_user_not_found()
        self.create_jwt_token(success=True)
        
        response = api_client.post(self.__get_url(), login_api_payload_ok, format='json')
        
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == None
        assert response.json()['errors'][0]['message'] == Messages.Post.login_failed()
        assert response.json()['errors'][0]['code'] == Messages.Code.other()
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
    def test_login_returns_401_unauthorized_password_do_not_match(self, api_client, login_api_payload_ok):
        self.validate_password_user_found()
        self.validate_password_match(match=False)
        response = api_client.post(self.__get_url(), login_api_payload_ok, format='json')
        
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['data'] == None
        assert response.json()['errors'][0]['field'] == None
        assert response.json()['errors'][0]['message'] == Messages.Post.login_failed()
        assert response.json()['errors'][0]['code'] == Messages.Code.other()
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
    def test_login_returns_500_internal_server_error(self, api_client, login_api_payload_ok):
        self.validate_password_user_found()
        self.validate_password_match()
        self.create_jwt_token(success=True)
        self.connection_lost(UserCollection, self.GET_ONE)
        response = api_client.post(self.__get_url(), login_api_payload_ok, format='json')
        
        assert response.json()['success'] == False
        assert response.json()['message'] == Messages.failed()
        assert response.json()['errors'][0]['field'] == 'detail'
        assert response.json()['errors'][0]['message'] == Messages.Database.connection_lost()
        assert response.json()['errors'][0]['code'] == Messages.Code.connection_lost()
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        
    def __get_url(self):
        return f"/{LOGIN_URL_V1}"