"""JSON write endpoints of DataDesk.

Plain Django views, like the grid endpoint: this is not the public API, it is
the maintenance UI talking to its own server, so nothing here goes near DRF's
view layer or ``/api/v1/``. The DRF serializers are used for validation only.

Every view answers with the same envelope — ``success``, ``message``, ``errors``,
``commit_id`` and the operation's own keys. Status codes are reserved for what
the client cannot decide from the body: 400 for an unusable request, 401/403 for
the staff gate, 409 for a delete, which needs S17's dependency preview first.
"""

import json
import uuid
from typing import Any

from django.http import HttpRequest, JsonResponse
from django.views import View

from datadesk.mixins import DataDeskAccessMixin
from datadesk.write import (
    ApplyResult,
    CreatedSeries,
    LookupResult,
    WriteError,
    apply_changes,
    create_lookup,
    create_series,
)


class JsonPostView(DataDeskAccessMixin, View):
    """Base for the write endpoints: parses the body, then hands it over."""

    def post(self, request: HttpRequest, *args, **kwargs) -> JsonResponse:
        """Parses the JSON body and turns a ``WriteError`` into its response."""
        try:
            payload = _read_json(request)
            return self.handle(payload, request, *args, **kwargs)
        except WriteError as error:
            return _failure(error)

    def handle(
        self, payload: dict[str, Any], request: HttpRequest, *args, **kwargs
    ) -> JsonResponse:
        """Writes what the payload asks for. Implemented by every endpoint."""
        raise NotImplementedError


class IssueCreateJsonView(JsonPostView):
    """Creates one series with its stamps, all or nothing."""

    def handle(
        self, payload: dict[str, Any], request: HttpRequest, *args, **kwargs
    ) -> JsonResponse:
        """Writes the series and answers with the ids the client needs."""
        series: CreatedSeries = create_series(payload, request.user)
        return _written("The series was created.", series.commit_id, series.as_dict())


class ApplyJsonView(JsonPostView):
    """Applies a batch of edits to existing rows, one savepoint each."""

    def handle(
        self, payload: dict[str, Any], request: HttpRequest, *args, **kwargs
    ) -> JsonResponse:
        """Applies the change set and reports what was refused."""
        result: ApplyResult = apply_changes(payload.get("changes"), request.user)
        return _written(
            _batch_message(result),
            result.commit_id,
            result.as_dict(),
            success=result.success,
        )


class LookupCreateJsonView(JsonPostView):
    """Returns a lookup row, creating it when the name is new."""

    def handle(
        self, payload: dict[str, Any], request: HttpRequest, *args, **kwargs
    ) -> JsonResponse:
        """Creates or reuses the lookup and answers with its id and name."""
        result: LookupResult = create_lookup(
            kwargs["key"], payload.get("value"), request.user
        )
        message = "Created." if result.created else "Already exists."
        return _written(message, result.commit_id, result.as_dict())


def _batch_message(result: ApplyResult) -> str:
    """Describes the outcome of a change set in one line."""
    total = result.applied + len(result.rejected)
    if result.success:
        return f"Applied {result.applied} changes."
    return f"Applied {result.applied} of {total} changes."


def _read_json(request: HttpRequest) -> dict[str, Any]:
    """Parses the request body, refusing anything that is not a JSON object."""
    try:
        payload = json.loads(request.body or b"{}")
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise WriteError("The body is not valid JSON.") from error

    if not isinstance(payload, dict):
        raise WriteError("The request body must be a JSON object.")
    return payload


def _written(
    message: str,
    commit_id: uuid.UUID,
    body: dict[str, Any],
    *,
    success: bool = True,
) -> JsonResponse:
    """Builds the envelope of a processed request."""
    return JsonResponse(
        {
            "success": success,
            "message": message,
            "errors": {},
            "commit_id": str(commit_id),
            **body,
        }
    )


def _failure(error: WriteError) -> JsonResponse:
    """Builds the envelope of a refused request."""
    body = {
        "success": False,
        "message": error.message,
        "errors": error.errors,
        "data": None,
    }
    body.update(error.extra)
    return JsonResponse(body, status=error.status)
