import pytest
from users_api.models import UserCollection
from django.contrib.auth.hashers import make_password

@pytest.fixture
def users_table(db):
    users = [
        UserCollection.objects.create(
            username="testuser1",
            email="test1@example.com",
            password_hash=make_password("password123"),
            first_name="Test",
            last_name="UserOne"
        ),
        UserCollection.objects.create(
            username="testuser2",
            email="test2@example.com",
            password_hash=make_password("password123"),
            first_name="Test",
            last_name="UserTwo"
        ),
    ]
    return users

@pytest.fixture
def user_post_payload_ok(db):
    return {
        "username": "newuser",
        "email": "new@example.com",
        "password": "newpassword123",
        "first_name": "New",
        "last_name": "User"
    }

@pytest.fixture
def user_put_payload_ok(db):
    return {
        "username": "updateduser",
        "email": "updated@example.com",
        "password": "updatedpassword123",
        "first_name": "Updated",
        "last_name": "User"
    }