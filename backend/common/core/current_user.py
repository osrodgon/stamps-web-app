"""Who is asking, taken from the JWT the login returns (plan step A1).

The public API authenticates with a key, not with a user: `HasSpecificKeyName`
returns a boolean and `request.user` stays `None`. The collections screens need
the person behind the request, and the login already gives them a token that says
it — this class turns that token into the `UserCollection` the views scope by.

A request without a JWT is not "somebody else": it is nobody, and these views
answer 403. The 401 for a missing header never reaches here — DRF's
authentication class refuses it first.
"""

from __future__ import annotations

from rest_framework.exceptions import PermissionDenied
from rest_framework.request import Request

from common.api.messages import Messages
from common.core.authorization import Authorization
from common.core.jwt_token import JwtToken
from users_api.models import UserCollection


class CurrentUser:
    """The user named by a request's `Authorization: JWT <token>`.

    Usage:
        user = CurrentUser(request).get()
    """

    def __init__(self, request: Request) -> None:
        """Take the request; nothing is read until `get()` is called."""
        self._request = request

    def get(self) -> UserCollection:
        """Return the user the token belongs to.

        Returns:
            The `UserCollection` named by the token.

        Raises:
            PermissionDenied: when the header is missing or is not a JWT, when the
                token is invalid or expired, or when its user no longer exists.
        """
        authorization = Authorization.from_request(self._request)
        if authorization.scheme != "JWT":
            raise PermissionDenied(Messages.Auth.invalid_format())

        payload = JwtToken().validate(authorization.credentials)
        if payload is None:
            raise PermissionDenied(Messages.Auth.invalid_jwt())

        try:
            return UserCollection.objects.get(pk=payload["user_id"])
        except UserCollection.DoesNotExist:
            raise PermissionDenied(Messages.Auth.user_not_found())
