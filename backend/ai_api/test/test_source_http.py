"""Tests for the source HTTP client (plan step A2).

No network: every test drives `httpx.MockTransport`, so the allowlist, the
retries, the per-host limit and the cache are exercised against a fake server.
"""

import threading
import time

import httpx
import pytest

from ai_api.sources.errors import SourceNotAllowed, SourceUnavailable
from ai_api.sources.http import HttpClient


ALLOWED = ["catalogodesellos.fesofi.es", "google.serper.dev"]


def client(handler, **kwargs) -> HttpClient:
    """Build a client wired to a fake transport."""
    options = {
        "allowed_hosts": ALLOWED,
        "retries": 0,
        "backoff": 0,
        "cache_ttl": 60,
        "per_host_limit": 4,
    }
    options.update(kwargs)
    return HttpClient(transport=httpx.MockTransport(handler), **options)


class TestAllowlist:
    """Only the hosts we chose are reachable."""

    def test_a_listed_host_is_fetched(self):
        transport = client(lambda request: httpx.Response(200, text="ok"))

        url = "https://catalogodesellos.fesofi.es/producto/0001/"

        assert transport.get_text(url) == "ok"

    def test_a_subdomain_of_a_listed_host_is_allowed(self):
        transport = client(
            lambda request: httpx.Response(200, text="ok"),
            allowed_hosts=["fesofi.es"],
        )

        assert transport.get_text("https://catalogodesellos.fesofi.es/x") == "ok"

    def test_an_unlisted_host_is_refused_before_the_request(self):
        calls = []

        def handler(request: httpx.Request) -> httpx.Response:
            calls.append(request.url)
            return httpx.Response(200, text="should not happen")

        transport = client(handler)

        with pytest.raises(SourceNotAllowed):
            transport.get("http://169.254.169.254/latest/meta-data/")

        assert calls == []

    def test_a_url_without_scheme_is_refused(self):
        transport = client(lambda request: httpx.Response(200))

        with pytest.raises(SourceNotAllowed):
            transport.get("catalogodesellos.fesofi.es/producto/1/")

    def test_a_lookalike_host_is_refused(self):
        transport = client(lambda request: httpx.Response(200))

        with pytest.raises(SourceNotAllowed):
            transport.get("https://catalogodesellos.fesofi.es.evil.test/x")


class TestRetries:
    """Retry what a retry can fix, and nothing else."""

    def test_a_500_is_tried_again(self):
        calls = []

        def handler(request: httpx.Request) -> httpx.Response:
            calls.append(request.url)
            if len(calls) == 1:
                return httpx.Response(500, text="boom")
            return httpx.Response(200, text="fine")

        transport = client(handler, retries=1)

        response = transport.get("https://catalogodesellos.fesofi.es/x")

        assert response.status_code == 200
        assert len(calls) == 2

    def test_a_429_is_tried_again(self):
        calls = []

        def handler(request: httpx.Request) -> httpx.Response:
            calls.append(request.url)
            return httpx.Response(429 if len(calls) == 1 else 200)

        transport = client(handler, retries=1)

        assert transport.get("https://catalogodesellos.fesofi.es/x").status_code == 200
        assert len(calls) == 2

    def test_a_404_is_not_tried_again(self):
        calls = []

        def handler(request: httpx.Request) -> httpx.Response:
            calls.append(request.url)
            return httpx.Response(404, text="no")

        transport = client(handler, retries=2)

        assert transport.get("https://catalogodesellos.fesofi.es/x").status_code == 404
        assert len(calls) == 1

    def test_a_timeout_is_wrapped_after_the_last_attempt(self):
        calls = []

        def handler(request: httpx.Request) -> httpx.Response:
            calls.append(request.url)
            raise httpx.ReadTimeout("too slow", request=request)

        transport = client(handler, retries=1)

        with pytest.raises(SourceUnavailable):
            transport.get("https://catalogodesellos.fesofi.es/x")

        assert len(calls) == 2

    def test_a_timeout_recovers_on_the_second_attempt(self):
        calls = []

        def handler(request: httpx.Request) -> httpx.Response:
            calls.append(request.url)
            if len(calls) == 1:
                raise httpx.ConnectError("nope", request=request)
            return httpx.Response(200, text="fine")

        transport = client(handler, retries=1)

        assert transport.get_text("https://catalogodesellos.fesofi.es/x") == "fine"


class TestCache:
    """A cached answer is not requested twice."""

    def test_a_get_is_served_from_the_cache(self):
        calls = []

        def handler(request: httpx.Request) -> httpx.Response:
            calls.append(request.url)
            return httpx.Response(200, text="ok")

        transport = client(handler)

        transport.get_text("https://catalogodesellos.fesofi.es/x")
        transport.get_text("https://catalogodesellos.fesofi.es/x")

        assert len(calls) == 1

    def test_a_post_is_never_cached(self):
        calls = []

        def handler(request: httpx.Request) -> httpx.Response:
            calls.append(request.url)
            return httpx.Response(200, text="ok")

        transport = client(handler)

        transport.post("https://google.serper.dev/search", json={"q": "x"})
        transport.post("https://google.serper.dev/search", json={"q": "x"})

        assert len(calls) == 2

    def test_clearing_the_cache_forces_a_new_request(self):
        calls = []

        def handler(request: httpx.Request) -> httpx.Response:
            calls.append(request.url)
            return httpx.Response(200, text="ok")

        transport = client(handler)

        transport.get_text("https://catalogodesellos.fesofi.es/x")
        transport.clear_cache()
        transport.get_text("https://catalogodesellos.fesofi.es/x")

        assert len(calls) == 2

    def test_the_query_string_is_part_of_the_cache_key(self):
        calls = []

        def handler(request: httpx.Request) -> httpx.Response:
            calls.append(str(request.url))
            return httpx.Response(200, text="ok")

        transport = client(handler)

        transport.get("https://catalogodesellos.fesofi.es/x", params={"page": 1})
        transport.get("https://catalogodesellos.fesofi.es/x", params={"page": 2})

        assert len(calls) == 2

    def test_an_error_is_not_cached(self):
        calls = []

        def handler(request: httpx.Request) -> httpx.Response:
            calls.append(request.url)
            return httpx.Response(404, text="no")

        transport = client(handler)

        transport.get("https://catalogodesellos.fesofi.es/x")
        transport.get("https://catalogodesellos.fesofi.es/x")

        assert len(calls) == 2


class TestPerHostLimit:
    """One host is not hammered: the limit is a real ceiling."""

    def test_the_limit_is_respected(self):
        current = 0
        peak = 0
        lock = threading.Lock()

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal current, peak
            with lock:
                current += 1
                peak = max(peak, current)
            time.sleep(0.03)
            with lock:
                current -= 1
            return httpx.Response(200, text="ok")

        transport = client(handler, per_host_limit=2, cache_ttl=0)

        threads = [
            threading.Thread(
                target=transport.get,
                args=(f"https://catalogodesellos.fesofi.es/{index}",),
            )
            for index in range(6)
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        assert peak <= 2


class TestJson:
    """JSON answers and the ones that are not JSON."""

    def test_a_json_body_is_returned(self):
        handler = lambda request: httpx.Response(200, json={"organic": []})
        transport = client(handler)

        assert transport.get_json("https://google.serper.dev/search") == {"organic": []}

    def test_a_non_json_body_raises_source_error(self):
        from ai_api.sources.errors import SourceError

        handler = lambda request: httpx.Response(200, text="<html>not json</html>")
        transport = client(handler)

        with pytest.raises(SourceError):
            transport.get_json("https://google.serper.dev/search")


class TestHeaders:
    """The client introduces itself."""

    def test_the_user_agent_is_ours(self):
        seen = {}

        def handler(request: httpx.Request) -> httpx.Response:
            seen["ua"] = request.headers.get("user-agent")
            return httpx.Response(200, text="ok")

        transport = client(handler, user_agent="stamps-web-app/9.9")

        transport.get("https://catalogodesellos.fesofi.es/x")

        assert seen["ua"] == "stamps-web-app/9.9"
