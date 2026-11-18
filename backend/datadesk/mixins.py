"""Access rules shared by the DataDesk views.

DataDesk is an internal tool: every screen and every JSON endpoint requires an
authenticated, active, staff user. The mixin covers views that forget it, and
``DataDeskGateMiddleware`` covers the rest.
"""
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, JsonResponse
from django.http.response import HttpResponseBase

JSON_CONTENT_TYPE = "application/json"


def wants_json(request: HttpRequest) -> bool:
    """Tells whether the caller expects JSON instead of an HTML page.

    HTMX requests and API-style ``Accept`` headers get a status code they can
    act on; a browser gets the login page.
    """
    if request.headers.get("HX-Request") == "true":
        return True
    accept = request.headers.get("Accept", "")
    return JSON_CONTENT_TYPE in accept


class DataDeskAccessMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Requires an active staff user, answering JSON callers with 401/403.

    Attributes:
        raise_exception (bool): Kept false: the mixin decides per request, so an
            anonymous browser is redirected to the DataDesk login instead of
            getting a bare 403.
    """

    raise_exception = False

    def get_login_url(self) -> str:
        """Points the login redirect at DataDesk, not at the project default."""
        return settings.DATADESK_LOGIN_URL

    def test_func(self) -> bool:
        """Only active staff users may use DataDesk."""
        user = self.request.user
        return bool(user.is_active and user.is_staff)

    def handle_no_permission(self) -> HttpResponseBase:
        """Returns 401/403 for JSON callers and a login redirect for browsers.

        The mixin follows the same split as ``DataDeskGateMiddleware``: an
        anonymous browser is sent to the form, and a logged-in non-staff user
        is refused outright instead of looping through the login page.
        """
        if self.request.user.is_authenticated:
            raise PermissionDenied("Staff access required.")
        if wants_json(self.request):
            return JsonResponse(
                {"success": False, "message": "Staff access required."},
                status=401,
            )
        return super().handle_no_permission()
