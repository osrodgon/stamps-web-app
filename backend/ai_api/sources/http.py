"""The one door the AI API uses to reach the network (plan step A2).

Everything the pipeline fetches — the catalogue pages, the search backend, and
later Colnect and the price sites — goes through `HttpClient`: an allowlist of
hosts, timeouts, retries with jitter, a per-host limit and a cache. Keeping it in
one place is what turns "the endpoint can download any URL you give it" into "the
endpoint can reach the six hosts we chose".
"""

from __future__ import annotations

import random
import threading
import time
from typing import Any, Dict, Optional, Tuple
from urllib.parse import urlparse

import httpx

from ai_api.sources.errors import SourceError, SourceNotAllowed, SourceUnavailable
from common.log.logger import Logger


# Statuses worth trying again: the source is busy or broken, not the request.
RETRY_STATUSES = frozenset({429, 500, 502, 503, 504})


class HttpClient(Logger):
    """HTTP client with an allowlist, retries, a per-host limit and a cache.

    Attributes:
        allowed_hosts: hosts the client may reach; a subdomain of one is allowed.
        timeout: seconds to wait for the whole request.
        retries: extra attempts after the first one for 5xx, 429 and transport
            errors. A 4xx is never retried: asking again will not fix it.
        backoff: base seconds of the exponential wait; jitter is added on top.
        per_host_limit: how many requests to the same host may run at once.
        cache_ttl: seconds a 200 answer is reused, 0 to disable.
    """

    def __init__(
        self,
        allowed_hosts: Optional[list[str]] = None,
        timeout: float = 20.0,
        connect_timeout: float = 5.0,
        retries: int = 2,
        backoff: float = 0.5,
        per_host_limit: int = 4,
        cache_ttl: int = 3600,
        user_agent: str = "stamps-web-app/0.1",
        transport: Optional[httpx.BaseTransport] = None,
    ) -> None:
        """Build the client; `transport` exists so tests can fake the network."""
        super().__init__()
        self.allowed_hosts = tuple(host.lower() for host in (allowed_hosts or []))
        self.timeout = timeout
        self.retries = retries
        self.backoff = backoff
        self.per_host_limit = max(1, per_host_limit)
        self.cache_ttl = cache_ttl
        self.user_agent = user_agent

        # A minimal set of browser-like preferences: with only a User-Agent, some
        # shops answer Cloudflare's challenge instead of the page (TodoColeccion
        # does), and the User-Agent still identifies us.
        self._client = httpx.Client(
            timeout=httpx.Timeout(timeout, connect=connect_timeout),
            headers={
                "User-Agent": user_agent,
                "Accept": (
                    "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8"
                ),
                "Accept-Language": "es,en;q=0.8",
            },
            follow_redirects=True,
            transport=transport,
        )
        self._cache: Dict[str, Tuple[float, httpx.Response]] = {}
        self._cache_lock = threading.Lock()
        self._host_slots: Dict[str, threading.BoundedSemaphore] = {}
        self._slots_lock = threading.Lock()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def is_allowed(self, url: str) -> bool:
        """Return True when the URL points at an allowlisted host over http(s)."""
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https") or not parsed.hostname:
            return False
        host = parsed.hostname.lower()
        return any(
            host == allowed or host.endswith(f".{allowed}")
            for allowed in self.allowed_hosts
        )

    def get(self, url: str, **kwargs: Any) -> httpx.Response:
        """Fetch a URL with the allowlist, the cache and the retry rules."""
        return self._request("GET", url, **kwargs)

    def post(self, url: str, **kwargs: Any) -> httpx.Response:
        """POST to a URL with the same rules; responses are not cached."""
        return self._request("POST", url, **kwargs)

    def get_text(self, url: str, **kwargs: Any) -> str:
        """Fetch a URL and return its body as text, or raise `SourceError`."""
        return self.get(url, **kwargs).text

    def get_json(self, url: str, **kwargs: Any) -> Dict[str, Any]:
        """Fetch a URL and return its JSON body, or raise `SourceError`."""
        return self._json(self.get(url, **kwargs))

    def post_json(self, url: str, **kwargs: Any) -> Dict[str, Any]:
        """POST and return the JSON body, or raise `SourceError`."""
        return self._json(self.post(url, **kwargs))

    def clear_cache(self) -> None:
        """Drop every cached answer, for tests and for a forced refresh."""
        with self._cache_lock:
            self._cache.clear()

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _request(self, method: str, url: str, **kwargs: Any) -> httpx.Response:
        """Run the request, retrying when the failure is worth retrying."""
        # Fold the query string into the URL: the cache and the allowlist work on
        # the whole address, and `/products?term=1` is not `/products?term=2`.
        params = kwargs.pop("params", None)
        if params:
            url = str(httpx.URL(url, params=params))

        if not self.is_allowed(url):
            host = urlparse(url).hostname or url
            raise SourceNotAllowed(
                f"{host} is not an allowed host: {', '.join(self.allowed_hosts)}"
            )

        if method == "GET":
            cached = self._cache_get(url)
            if cached is not None:
                self.log.debug(f"cache hit: {url}")
                return cached

        with self._host_slot(url):
            response = self._send(method, url, **kwargs)

        if method == "GET" and response.status_code == 200:
            self._cache_put(url, response)

        return response

    def _send(self, method: str, url: str, **kwargs: Any) -> httpx.Response:
        """Send once, and retry the failures that a retry can fix."""
        kwargs.setdefault("headers", {})
        last_error: Optional[Exception] = None

        for attempt in range(self.retries + 1):
            started = time.perf_counter()
            try:
                response = self._client.request(method, url, **kwargs)
            except httpx.HTTPError as error:
                last_error = error
                self.log.warning(
                    f"{method} {url} failed ({type(error).__name__}), "
                    f"attempt {attempt + 1}/{self.retries + 1}"
                )
                if attempt < self.retries:
                    self._wait(attempt)
                    continue
                raise SourceUnavailable(f"{method} {url}: {error}") from error

            elapsed = round((time.perf_counter() - started) * 1000)
            self.log.debug(f"{method} {url} -> {response.status_code} in {elapsed} ms")

            if response.status_code in RETRY_STATUSES and attempt < self.retries:
                self.log.warning(
                    f"{method} {url} -> {response.status_code}, "
                    f"attempt {attempt + 1}/{self.retries + 1}"
                )
                self._wait(attempt)
                continue

            return response

        raise SourceUnavailable(f"{method} {url}: {last_error}")

    def _wait(self, attempt: int) -> None:
        """Sleep a jittered exponential backoff before the next attempt."""
        delay = self.backoff * (2 ** attempt) + random.uniform(0, self.backoff)
        if delay > 0:
            time.sleep(delay)

    def _host_slot(self, url: str) -> threading.BoundedSemaphore:
        """Return the semaphore that keeps one host from being hammered."""
        host = (urlparse(url).hostname or "").lower()
        with self._slots_lock:
            slot = self._host_slots.get(host)
            if slot is None:
                slot = threading.BoundedSemaphore(self.per_host_limit)
                self._host_slots[host] = slot
            return slot

    def _cache_get(self, url: str) -> Optional[httpx.Response]:
        """Return a fresh cached answer, or None."""
        if self.cache_ttl <= 0:
            return None
        with self._cache_lock:
            entry = self._cache.get(url)
            if entry is None:
                return None
            expires_at, response = entry
            if expires_at < time.time():
                del self._cache[url]
                return None
            return response

    def _cache_put(self, url: str, response: httpx.Response) -> None:
        """Remember a 200 answer for `cache_ttl` seconds."""
        if self.cache_ttl <= 0:
            return
        with self._cache_lock:
            self._cache[url] = (time.time() + self.cache_ttl, response)

    @staticmethod
    def _json(response: httpx.Response) -> Dict[str, Any]:
        """Turn a response into JSON, turning failures into `SourceError`."""
        try:
            return response.json()
        except ValueError as error:
            raise SourceError(
                f"expected JSON, got {response.status_code} "
                f"{response.headers.get('content-type', '')}"
            ) from error


_client: Optional[HttpClient] = None
_client_lock = threading.Lock()


def get_client() -> HttpClient:
    """Return the process-wide client, built from settings the first time.

    One instance on purpose: the cache and the per-host limits only mean
    something if every request shares them.
    """
    global _client
    if _client is not None:
        return _client
    with _client_lock:
        if _client is None:
            from django.conf import settings as django_settings

            allowed = list(django_settings.AI_SOURCE_ALLOWED_HOSTS)
            # The search backend comes from configuration, not from the request,
            # so its host is trusted as much as the list in settings.
            search_host = urlparse(django_settings.SERPER_URL or "").hostname
            if search_host and search_host not in allowed:
                allowed.append(search_host)

            _client = HttpClient(
                allowed_hosts=allowed,
                timeout=django_settings.AI_SOURCE_TIMEOUT,
                connect_timeout=django_settings.AI_SOURCE_CONNECT_TIMEOUT,
                retries=django_settings.AI_SOURCE_RETRIES,
                per_host_limit=django_settings.AI_SOURCE_MAX_PER_HOST,
                cache_ttl=django_settings.AI_SOURCE_CACHE_TTL,
                user_agent=django_settings.AI_SOURCE_USER_AGENT,
            )
    return _client


def set_client(client: Optional[HttpClient]) -> None:
    """Replace the shared client; `None` forgets it so the next call rebuilds."""
    global _client
    with _client_lock:
        _client = client
