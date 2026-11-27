"""Login and logout for DataDesk, with a throttle on failed attempts.

DataDesk has its own login page because it is deployed on an external server and
the global ``LOGIN_URL`` belongs to the public app. Failures are counted per
username and IP in the shared file cache, so four gunicorn workers see the same
counter without needing a database table.
"""
import logging

from django.conf import settings
from django.contrib.auth.views import LoginView, LogoutView
from django.core.cache import cache
from django.http import HttpRequest, HttpResponse
from django.http.response import HttpResponseBase
from django.template.response import TemplateResponse

from datadesk.mixins import wants_json

logger = logging.getLogger(__name__)

THROTTLE_LIMIT = 5
"""Failed attempts allowed inside the window before answering 429."""

THROTTLE_WINDOW_SECONDS = 300
"""Length of the counting window, in seconds."""

THROTTLE_KEY = "datadesk:login:{username}:{ip}"

PARTIAL_TEMPLATE = "datadesk/partials/login_form.html"
PAGE_TEMPLATE = "datadesk/login.html"

RETRY_AFTER_HEADER = "Retry-After"


def _throttle_key(username: str, ip: str) -> str:
    """Builds the cache key for one username/IP pair."""
    return THROTTLE_KEY.format(username=username.strip().lower(), ip=ip)


def _client_ip(request: HttpRequest) -> str:
    """Returns the caller IP.

    Behind nginx this is the proxy address, which collapses the key to the
    username — exactly what a single-user tool wants. ``X-Forwarded-For`` is
    deliberately ignored: anyone can send that header.
    """
    return request.META.get("REMOTE_ADDR", "")


def _register_failure(key: str) -> int:
    """Counts one failed attempt and returns the new total.

    Each failure re-arms the window (sliding expiry): someone who keeps trying
    stays locked out instead of getting a fresh allowance every five minutes.
    """
    failures = cache.get(key, 0) + 1
    cache.set(key, failures, THROTTLE_WINDOW_SECONDS)
    return failures


def _retry_after(key: str) -> int:
    """Returns the seconds the caller should wait before trying again."""
    ttl = cache.ttl(key, None) if hasattr(cache, "ttl") else None
    return int(ttl) if ttl else THROTTLE_WINDOW_SECONDS


def _is_throttled(key: str) -> bool:
    """Tells whether the key already reached the limit."""
    return cache.get(key, 0) > THROTTLE_LIMIT


class DataDeskLoginView(LoginView):
    """Login form for DataDesk, throttled after repeated failures.

    Attributes:
        template_name (str): Page template; the form lives in a partial so a 429
            can be returned to HTMX without the surrounding document.
        redirect_authenticated_user (bool): A logged-in user never sees the form.
    """

    template_name = PAGE_TEMPLATE
    redirect_authenticated_user = True

    def get_default_redirect_url(self) -> str:
        """Sends the user to DataDesk, never to ``/accounts/profile/``.

        ``LOGIN_REDIRECT_URL`` is not defined in settings, and Django's default
        would be wrong for an internal tool.
        """
        return f"/{settings.DATADESK_URL}"

    def form_invalid(self, form) -> HttpResponseBase:
        """Counts the failure and answers 429 once the limit is reached."""
        key = self._key(form)
        if _is_throttled(key):
            return self._throttled_response(form, key, status=429)

        failures = _register_failure(key)
        if failures > THROTTLE_LIMIT:
            logger.warning("DataDesk login throttled for %s", key)
            return self._throttled_response(form, key, status=429)

        return super().form_invalid(form)

    def form_valid(self, form) -> HttpResponseBase:
        """Clears the counter: a successful login resets the window."""
        cache.delete(self._key(form))
        logger.info("DataDesk login succeeded for %s", form.get_user().get_username())
        return super().form_valid(form)

    def _key(self, form) -> str:
        """Returns the throttle key for the submitted username."""
        username = form.data.get("username", "")
        return _throttle_key(str(username), _client_ip(self.request))

    def _throttled_response(
        self, form, key: str, status: int
    ) -> TemplateResponse:
        """Renders the form with a wait message and the ``Retry-After`` header."""
        retry_after = _retry_after(key)
        context = self.get_context_data(
            form=form,
            throttled=True,
            retry_after=retry_after,
        )
        template = PARTIAL_TEMPLATE if wants_json(self.request) else PAGE_TEMPLATE
        response = TemplateResponse(self.request, template, context, status=status)
        response[RETRY_AFTER_HEADER] = str(retry_after)
        return response


class DataDeskLogoutView(LogoutView):
    """Closes the DataDesk session and returns to the login page.

    Django 6 already restricts logout to POST, so a ``GET`` answers 405.
    """

    next_page = settings.DATADESK_LOGIN_URL
