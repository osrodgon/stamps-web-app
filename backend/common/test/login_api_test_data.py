import pytest

from common.test.users_api_test_data import users_table


@pytest.fixture
def login_api_payload_ok(users_table):
    return {
        'username': users_table[0].username,
        'password': '123'
    }
    
def login_api_response_ok():
    return {
        'token': 'test_token',
        'payload': {
            'user_id': '1',
            'username': 'username',
            'first_name': 'first_name',
            'last_name': 'last_name',
            'jti': 'abcde',
            'exp': 'exp_time',
            'iat': 'cre_time'
        } 
    }