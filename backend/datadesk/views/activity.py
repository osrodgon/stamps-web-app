"""The activity screen, and the one button on it: undo a commit.

The reading is in ``datadesk.activity``. What lives here is the page, the labels
the page shows — taken from the same definitions the editor uses, so the log
cannot call a column something the editor does not — and the POST that undoes a
commit, which answers with the page itself when it is refused.
"""

from typing import Any

from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic import TemplateView

from datadesk.activity import activity_page, revert_commit
from datadesk.mixins import DataDeskAccessMixin
from datadesk.views.workspace import field_labels
from datadesk.write import WriteError


class ActivityView(DataDeskAccessMixin, TemplateView):
    """Lists the commits, newest first, one page at a time."""

    template_name = "datadesk/activity.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Adds the page of commits and the banner of a finished revert."""
        context = super().get_context_data(**kwargs)
        context.update(
            activity=activity_page(
                page=_int(self.request, "page") or 1,
                labels=field_labels_for_log(),
                anonymous=str(_("Anonymous")),
            ),
            reverted=self.request.GET.get("reverted", ""),
        )
        return context


class CommitRevertView(DataDeskAccessMixin, View):
    """Undoes one commit, all of it or nothing."""

    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Reverts, then redirects back to the log — or back with the reason."""
        try:
            result = revert_commit(kwargs["commit_id"], request.user)
        except WriteError as error:
            return _refused(request, error)

        return redirect(f"{reverse('datadesk:activity')}?reverted={result.reverted}")


def field_labels_for_log() -> dict[str, str]:
    """Returns one flat map of column names to translated labels.

    The series and stamp columns come from the editor's own definitions (the
    same ones the review panel uses); the two lookup columns are the only fields
    a reference row has.
    """
    labels = field_labels()
    return {
        **labels["issue"],
        **labels["stamp"],
        "name": str(_("Name")),
        "year": str(_("Year")),
    }


def _refused(request: HttpRequest, error: WriteError) -> HttpResponse:
    """Renders the log again with the reason on top of it.

    A redirect would lose the message, and a JSON endpoint would leave the page
    without the list the user was reading: the screen is the answer.
    """
    view = ActivityView()
    view.setup(request)
    context = view.get_context_data()
    context["error"] = error.message
    return render(request, view.template_name, context, status=error.status)


def _int(request: HttpRequest, name: str) -> int | None:
    """Returns an integer query parameter, or ``None`` when absent or invalid."""
    raw = request.GET.get(name, "").strip()
    if raw == "":
        return None
    try:
        return int(raw)
    except ValueError:
        return None
