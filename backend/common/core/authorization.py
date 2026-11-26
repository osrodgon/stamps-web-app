"""The `Authorization` header, parsed once for everyone who needs it.

Two places read it: `HasSpecificKeyName.has_permission` (who is allowed in) and
`CurrentUser` (which user is asking). They were splitting the string and deciding
what a malformed header means in their own way, so this class is the one
implementation, and the messages stay the same for both.
"""

from __future__ import annotations

from dataclasses import dataclass

from rest_framework.exceptions import PermissionDenied
from rest_framework.request import Request

from common.api.messages import Messages


@dataclass(frozen=True)
class Authorization:
    """The scheme and the credentials of a request's `Authorization` header."""

    scheme: str
    credentials: str

    @classmethod
    def from_request(cls, request: Request) -> "Authorization":
        """Read the header of `request` as an `Authorization`.

        Args:
            request: the incoming request.

        Returns:
            The scheme in upper case and its credentials.

        Raises:
            PermissionDenied: when the header is missing or is not two words.
        """
        header = request.META.get("HTTP_AUTHORIZATION", "")
        if not header:
            raise PermissionDenied(Messages.Auth.header_missing())

        parts = header.split()
        if len(parts) != 2:
            raise PermissionDenied(Messages.Auth.invalid_format())

        return cls(parts[0].upper(), parts[1])
