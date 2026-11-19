"""The envelope and the base view the DataDesk JSON endpoints share.

Every JSON endpoint answers the same shape — ``success``, ``message``,
``errors``, and the operation's own keys — and every one of them is a plain
Django view: this is not the public API, it is the maintenance UI talking to its
own server, so nothing here goes near DRF's view layer or ``/api/v1/``.

Keeping the envelope in one place is what lets the workspace and the lookups
screen trust the same contract, and lets a refusal carry the extra keys its
screen needs (the duplicate name's id, the usage count of a row still in use)
without inventing a second format.
"""
import json
import uuid
from typing import Any

from django.http import HttpRequest, JsonResponse
from django.views import View

from datadesk.mixins import DataDeskAccessMixin
from datadesk.write import WriteError


class JsonPostView(DataDeskAccessMixin, View):
    """Base for the JSON endpoints: gate, body, envelope.

    The staff gate comes with it: an endpoint that writes must be as protected
    as the screens it belongs to, and forgetting the mixin is the kind of
    mistake that only shows up in production.
    """

    def post(self, request: HttpRequest, *args, **kwargs) -> JsonResponse:
        """Parses the JSON body and turns a ``WriteError`` into its response."""
        try:
            payload = read_json(request)
            return self.handle(payload, request, *args, **kwargs)
        except WriteError as error:
            return failure(error)

    def handle(
        self, payload: dict[str, Any], request: HttpRequest, *args, **kwargs
    ) -> JsonResponse:
        """Writes what the payload asks for. Implemented by every endpoint."""
        raise NotImplementedError


def read_json(request: HttpRequest) -> dict[str, Any]:
    """Parses the request body, refusing anything that is not a JSON object."""
    try:
        payload = json.loads(request.body or b"{}")
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise WriteError("The body is not valid JSON.") from error

    if not isinstance(payload, dict):
        raise WriteError("The request body must be a JSON object.")
    return payload


def written(
    message: str,
    body: dict[str, Any],
    *,
    commit_id: uuid.UUID | None = None,
    success: bool = True,
) -> JsonResponse:
    """Builds the envelope of a processed request."""
    envelope: dict[str, Any] = {
        "success": success,
        "message": message,
        "errors": {},
    }
    if commit_id is not None:
        envelope["commit_id"] = str(commit_id)
    envelope.update(body)
    return JsonResponse(envelope)


def failure(error: WriteError) -> JsonResponse:
    """Builds the envelope of a refused request."""
    body: dict[str, Any] = {
        "success": False,
        "message": error.message,
        "errors": error.errors,
        "data": None,
    }
    body.update(error.extra)
    return JsonResponse(body, status=error.status)
