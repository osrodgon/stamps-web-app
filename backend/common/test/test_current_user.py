"""Tests for `CurrentUser`, the class that reads the JWT (plan step A1).

It is the only place that turns a token into a `UserCollection`, so these tests
cover the three ways it says no: no header, a header that is not a JWT, and a
token that does not validate.
"""

import pytest
from rest_framework.exceptions import PermissionDenied
from rest_framework.test import APIRequestFactory

from common.api.messages import Messages
from common.core.current_user import CurrentUser
from common.core.jwt_token import JwtToken
from common.test.users_api_test_data import users_table
from users_api.models import UserCollection, UserToken


pytestmark = pytest.mark.django_db


class Requests:
    """Requests for these tests, built in one place."""

    @staticmethod
    def with_header(header: str = None):
        """A request carrying `header` as its Authorization value."""
        extra = {"HTTP_AUTHORIZATION": header} if header is not None else {}
        return APIRequestFactory().get("/", **extra)


class TestValidToken:
    """A token the login issued names its user."""

    def test_it_returns_the_user_of_the_token(self, users_table):
        token = JwtToken().create(users_table[0])["token"]

        user = CurrentUser(Requests.with_header(f"JWT {token}")).get()

        assert user.pk == users_table[0].pk
        assert user.username == users_table[0].username

    def test_the_scheme_is_case_insensitive(self, users_table):
        token = JwtToken().create(users_table[0])["token"]

        user = CurrentUser(Requests.with_header(f"jwt {token}")).get()

        assert user.pk == users_table[0].pk


class TestRefusals:
    """Everything that is not a valid JWT is a 403 with a reason."""

    def test_no_header_is_refused(self):
        with pytest.raises(PermissionDenied) as error:
            CurrentUser(Requests.with_header()).get()

        assert Messages.Auth.header_missing() in str(error.value)

    def test_a_header_that_is_not_a_jwt_is_refused(self, users_table):
        with pytest.raises(PermissionDenied) as error:
            CurrentUser(Requests.with_header("API-KEY master")).get()

        assert Messages.Auth.invalid_format() in str(error.value)

    def test_a_two_part_header_is_required(self, users_table):
        with pytest.raises(PermissionDenied) as error:
            CurrentUser(Requests.with_header("JWT")).get()

        assert Messages.Auth.invalid_format() in str(error.value)

    def test_an_invalid_token_is_refused(self):
        with pytest.raises(PermissionDenied) as error:
            CurrentUser(Requests.with_header("JWT not-a-token")).get()

        assert Messages.Auth.invalid_jwt() in str(error.value)

    def test_a_token_without_its_row_is_refused(self, users_table):
        token = JwtToken().create(users_table[0])["token"]
        UserToken.objects.all().delete()

        with pytest.raises(PermissionDenied) as error:
            CurrentUser(Requests.with_header(f"JWT {token}")).get()

        assert Messages.Auth.invalid_jwt() in str(error.value)

    def test_a_token_of_a_missing_user_is_refused(self, users_table, mocker):
        token = JwtToken().create(users_table[0])["token"]
        mocker.patch(
            "common.core.current_user.UserCollection.objects.get",
            side_effect=UserCollection.DoesNotExist,
        )

        with pytest.raises(PermissionDenied) as error:
            CurrentUser(Requests.with_header(f"JWT {token}")).get()

        assert Messages.Auth.user_not_found() in str(error.value)
