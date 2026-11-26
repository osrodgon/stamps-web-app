"""Tests for scraping through the shared client (plan step A2)."""

import httpx

from ai_api.services.scraping_service import DESCRIPTION_LIMIT, ScrapingService
from ai_api.sources.http import HttpClient


PAGE = """
<html><body>
  <h1 class="product_title">6 cuartos</h1>
  <div id="paneldescription">Primer sello español.</div>
  <div id="paneladditional_information">
    <table>
      <tr><th>Año de Emisión:</th><td>1850</td></tr>
      <tr><th>Facial:</th><td>6 cuartos</td></tr>
    </table>
  </div>
</body></html>
"""


def service(handler, **kwargs) -> ScrapingService:
    """Build the service over a fake transport."""
    options = {"allowed_hosts": ["catalogodesellos.fesofi.es"], "cache_ttl": 0}
    options.update(kwargs)
    transport = httpx.MockTransport(handler)
    return ScrapingService(client=HttpClient(transport=transport, **options))


class TestScrapeContent:
    """One page per URL, in order, and a failure does not abort the rest."""

    def test_every_url_is_fetched_once(self):
        calls = []

        def handler(request: httpx.Request) -> httpx.Response:
            calls.append(str(request.url))
            return httpx.Response(200, text=PAGE)

        result = service(handler).scrape_content(
            [
                "https://catalogodesellos.fesofi.es/producto/0001/",
                "https://catalogodesellos.fesofi.es/producto/0002/",
            ]
        )

        assert len(calls) == 2
        assert [row["url"] for row in result] == calls

    def test_the_page_is_parsed(self):
        handler = lambda request: httpx.Response(200, text=PAGE)

        result = service(handler).scrape_content(
            ["https://catalogodesellos.fesofi.es/producto/0001/"]
        )

        assert result[0]["titulo"] == "6 cuartos"
        assert result[0]["descripcion"] == "Primer sello español."
        assert result[0]["facial"] == "6 cuartos"

    def test_a_failing_page_is_skipped_and_the_rest_survives(self):
        def handler(request: httpx.Request) -> httpx.Response:
            if request.url.path.endswith("/0001/"):
                return httpx.Response(500, text="boom")
            return httpx.Response(200, text=PAGE)

        result = service(handler).scrape_content(
            [
                "https://catalogodesellos.fesofi.es/producto/0001/",
                "https://catalogodesellos.fesofi.es/producto/0002/",
            ]
        )

        assert len(result) == 1
        assert result[0]["url"].endswith("/0002/")

    def test_a_repeated_url_is_fetched_once(self):
        calls = []

        def handler(request: httpx.Request) -> httpx.Response:
            calls.append(str(request.url))
            return httpx.Response(200, text=PAGE)

        url = "https://catalogodesellos.fesofi.es/producto/0001/"
        service(handler, cache_ttl=0).scrape_content([url, url])

        assert len(calls) == 1

    def test_no_urls_is_no_work(self):
        scraping = service(lambda request: httpx.Response(200, text=PAGE))

        assert scraping.scrape_content([]) == []


class TestDescription:
    """The description is the best material for the card, so it is not dieted."""

    def test_a_normal_description_arrives_whole(self):
        text = "Sello dedicado a la «Natividad» de Toledo. " * 20

        assert ScrapingService._snippet(text) == text

    def test_a_short_description_gets_no_ellipsis(self):
        assert ScrapingService._snippet("Corto.") == "Corto."

    def test_a_very_long_description_is_cut_and_says_so(self):
        text = "x" * (DESCRIPTION_LIMIT + 500)

        snippet = ScrapingService._snippet(text)

        assert len(snippet) == DESCRIPTION_LIMIT + 1
        assert snippet.endswith("…")

    def test_a_missing_description_is_marked(self):
        assert ScrapingService._snippet("") == "N/A"


class TestExtractLinks:
    """The index page still goes through the client."""

    def test_links_are_absolute_and_deduplicated(self):
        html = """
        <html><body>
          <h2>Resto valores serie</h2>
          <a href="https://catalogodesellos.fesofi.es/producto/0002/">2</a>
          <a href="https://catalogodesellos.fesofi.es/producto/0002/?x=1">2 again</a>
          <a href="https://elsewhere.test/producto/0003/">outside</a>
        </body></html>
        """
        handler = lambda request: httpx.Response(200, text=html)

        links = service(handler).extract_links(
            "https://catalogodesellos.fesofi.es/producto/0001/"
        )

        assert "https://catalogodesellos.fesofi.es/producto/0002/" in links
        assert "https://elsewhere.test/producto/0003/" not in links
        assert len(links) == 2

    def test_a_host_outside_the_allowlist_yields_nothing(self):
        links = service(lambda request: httpx.Response(200, text=PAGE)).extract_links(
            "https://elsewhere.test/producto/0001/"
        )

        assert links == []
