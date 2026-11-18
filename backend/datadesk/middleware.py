"""Path-level gate for DataDesk.

The views also use ``DataDeskAccessMixin``; this middleware is the belt for the
JSON endpoints that will be added later (S8, S12) and for anything that forgets
the mixin. It only looks at paths under ``/datadesk/``, so ``/health`` and
``/api/v1/`` keep working exactly as before.
"""
from django.conf import settings
from django.http import HttpRequest, HttpResponseRedirect, JsonResponse
from django.http.response import HttpResponseBase
from django.shortcuts import render
from django.urls import NoReverseMatch, reverse

from datadesk.mixins import wants_json

EXEMPT_URL_NAMES = ("datadesk:login", "datadesk:logout")


class DataDeskGateMiddleware:
    """Requires an active staff user for every DataDesk path but login/logout."""

    def __init__(self, get_response) -> None:
        """Stores the next callable in the chain."""
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponseBase:
        """Rejects non-staff callers before the view runs."""
        if self._requires_staff(request):
            return self._deny(request)
        return self.get_response(request)

    def _requires_staff(self, request: HttpRequest) -> bool:
        """Tells whether this request must pass the staff gate."""
        if not settings.DATADESK_ENABLED:
            return False

        root = f"/{settings.DATADESK_URL}"
        if not request.path.startswith(root):
            return False

        exempt = self._exempt_paths()
        if exempt is None:
            return False
        if request.path in exempt:
            return False

        user = getattr(request, "user", None)
        return not (user and user.is_authenticated and user.is_active and user.is_staff)

    def _exempt_paths(self) -> set[str] | None:
        """Resolves the login/logout URLs, or ``None`` if DataDesk is not mounted."""
        try:
            return {reverse(name) for name in EXEMPT_URL_NAMES}
        except NoReverseMatch:
            return None

    def _deny(self, request: HttpRequest) -> HttpResponseBase:
        """Answers JSON callers with 401, non-staff with 403, browsers with a redirect."""
        user = getattr(request, "user", None)
        authenticated = bool(user and user.is_authenticated)
        if authenticated:
            if wants_json(request):
                return JsonResponse(
                    {"success": False, "message": "Staff access required."},
                    status=403,
                )
            return render(request, "datadesk/forbidden.html", status=403)

        if wants_json(request):
            return JsonResponse(
                {"success": False, "message": "Staff access required."},
                status=401,
            )

        login_url = reverse("datadesk:login")
        return HttpResponseRedirect(f"{login_url}?next={request.path}")
