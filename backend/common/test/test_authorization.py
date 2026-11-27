"""Tests for `Authorization`, the one parser of the auth header.

Both `HasSpecificKeyName` and `CurrentUser` read the same header, so the parsing
and the messages live here and are tested once.
"""

import pytest
from rest_framework.exceptions import PermissionDenied
from rest_framework.test import APIRequestFactory

from common.api.messages import Messages
from common.core.authorization import Authorization


class Requests:
    """Requests for these tests, built in one place."""

    @staticmethod
    def with_header(header: str = None):
        """A request carrying `header` as its Authorization value."""
        extra = {"HTTP_AUTHORIZATION": header} if header is not None else {}
        return APIRequestFactory().get("/", **extra)


class TestParsing:
    """A header with two words is a scheme and its credentials."""

    def test_it_splits_the_scheme_and_the_credentials(self):
        authorization = Authorization.from_request(Requests.with_header("JWT abc.def"))

        assert authorization.scheme == "JWT"
        assert authorization.credentials == "abc.def"

    def test_the_scheme_is_upper_case(self):
        authorization = Authorization.from_request(Requests.with_header("api-key secret"))

        assert authorization.scheme == "API-KEY"


class TestRefusals:
    """A header that is not two words says why."""

    def test_a_missing_header(self):
        with pytest.raises(PermissionDenied) as error:
            Authorization.from_request(Requests.with_header())

        assert Messages.Auth.header_missing() in str(error.value)

    def test_an_empty_header(self):
        with pytest.raises(PermissionDenied) as error:
            Authorization.from_request(Requests.with_header(""))

        assert Messages.Auth.header_missing() in str(error.value)

    def test_a_header_without_credentials(self):
        with pytest.raises(PermissionDenied) as error:
            Authorization.from_request(Requests.with_header("JWT"))

        assert Messages.Auth.invalid_format() in str(error.value)

    def test_a_header_with_more_than_two_words(self):
        with pytest.raises(PermissionDenied) as error:
            Authorization.from_request(Requests.with_header("Basic user password"))

        assert Messages.Auth.invalid_format() in str(error.value)
