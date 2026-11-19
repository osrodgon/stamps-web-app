"""JSON write endpoints of DataDesk.

Plain Django views, like the grid endpoint: this is not the public API, it is
the maintenance UI talking to its own server, so nothing here goes near DRF's
view layer or ``/api/v1/``. The DRF serializers are used for validation only.

Every view answers with the same envelope — ``success``, ``message``, ``errors``,
``commit_id`` and the operation's own keys. Status codes are reserved for what
the client cannot decide from the body: 400 for an unusable request, 401/403 for
the staff gate, 404 for a row that no longer exists.

Deleting a series is the one operation with a preview in front of it, so the
read that feeds that preview lives here too: the two are one decision and
splitting them across modules would hide that the delete endpoint recounts what
the preview reported.
"""

import json
import uuid
from datetime import datetime
from io import StringIO
from typing import Any

from django.conf import settings
from django.core.management import call_command
from django.http import HttpRequest, JsonResponse
from django.urls import reverse
from django.views import View

from datadesk.dependencies import dependency_warning, series_dependencies
from datadesk.mixins import DataDeskAccessMixin
from datadesk.service import issue_queryset
from datadesk.write import (
    ApplyResult,
    CreatedSeries,
    DeletedSeries,
    LookupResult,
    WriteError,
    apply_changes,
    clone_series,
    create_lookup,
    create_series,
    delete_series,
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


class IssueCloneJsonView(JsonPostView):
    """Copies a series with its stamps and answers where the copy lives."""

    def handle(
        self, payload: dict[str, Any], request: HttpRequest, *args, **kwargs
    ) -> JsonResponse:
        """Clones the series and returns the URL that opens the copy."""
        series: CreatedSeries = clone_series(
            int(kwargs["pk"]), _overrides(payload), request.user
        )
        body = series.as_dict()
        body["data"]["url"] = reverse(
            "datadesk:issue_workspace", args=[series.issue.pk]
        )
        return _written("The series was cloned.", series.commit_id, body)


class IssueDependenciesJsonView(DataDeskAccessMixin, View):
    """Reports what deleting a series would take with it.

    A GET because it reads, and separate from the delete endpoint because it
    runs before the user has decided. Both live in this module: the delete
    recounts inside its transaction instead of trusting these numbers.
    """

    def get(self, request: HttpRequest, *args, **kwargs) -> JsonResponse:
        """Returns the counts, the identity of the series and the warning."""
        issue = issue_queryset().filter(pk=kwargs["pk"]).first()
        if issue is None:
            return JsonResponse(
                {
                    "success": False,
                    "message": "The series does not exist.",
                    "errors": {},
                    "data": None,
                },
                status=404,
            )

        dependencies = series_dependencies(issue)
        return JsonResponse(
            {
                "success": True,
                "message": "Preview.",
                "errors": {},
                "data": {
                    "id": issue.pk,
                    "year": issue.year.year,
                    "name": issue.name,
                    "warning": dependency_warning(dependencies),
                    **dependencies.as_dict(),
                },
            }
        )


class IssueDeleteJsonView(JsonPostView):
    """Deletes a series once the typed year matches."""

    def handle(
        self, payload: dict[str, Any], request: HttpRequest, *args, **kwargs
    ) -> JsonResponse:
        """Deletes the series and reports what the cascade took with it."""
        result: DeletedSeries = delete_series(
            int(kwargs["pk"]), payload.get("confirm"), request.user
        )
        return _written("The series was deleted.", result.commit_id, result.as_dict())


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


class BackupJsonView(DataDeskAccessMixin, View):
    """Writes a dump of the stamps database before a large commit.

    The command already exists (``stamps_db_backup``) and is interactive, so it
    is called non-interactively with a generated name and the ``stamps`` mode.
    The panel offers this once the change set passes the threshold; it is never
    automatic, because writing a file is a side effect the user did not ask for.
    """

    def post(self, request: HttpRequest, *args, **kwargs) -> JsonResponse:
        """Runs the dump and answers with the file it wrote."""
        name = f"datadesk-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        try:
            call_command("stamps_db_backup", name, mode="stamps", stdout=StringIO())
        except Exception as error:  # noqa: BLE001 - the reason goes to the panel
            return JsonResponse(
                {
                    "success": False,
                    "message": f"The backup failed: {error}",
                    "errors": {},
                    "data": None,
                },
                status=500,
            )

        dump = settings.BASE_DIR / "backups" / f"{name}__stamps.json"
        if not dump.exists():
            return JsonResponse(
                {
                    "success": False,
                    "message": "The backup command did not write a file.",
                    "errors": {},
                    "data": None,
                },
                status=500,
            )

        return JsonResponse(
            {
                "success": True,
                "message": "Backup written.",
                "errors": {},
                "data": {"file": str(dump.relative_to(settings.BASE_DIR))},
            }
        )


def _overrides(payload: dict[str, Any]) -> dict[str, Any]:
    """Takes the values a clone may override, leaving out anything else.

    Absent and empty mean different things — no ``date`` key copies the origin's
    date, ``date: null`` clears it — so the keys are filtered, not read with
    ``get()``.
    """
    return {key: payload[key] for key in ("year", "date") if key in payload}


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
