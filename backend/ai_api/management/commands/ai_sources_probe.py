"""Probe the external sources planned for the AI API (plan step A0).

Run it before writing an adapter: it records reachability, response shape and
``robots.txt`` for Colnect, Delcampe and Iberphil, and saves the raw evidence as
JSON next to the plan. See ``memory-bank/ai-api-plan.md``, step A0.

Usage:
    python manage.py ai_sources_probe
    python manage.py ai_sources_probe --source delcampe --delay 10
    python manage.py ai_sources_probe --json /tmp/probe.json
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any, Dict, List

import requests
from django.conf import settings
from django.core.management.base import BaseCommand

from ai_api import probe

SOURCES = ("colnect", "delcampe", "iberphil", "fesofi")

DEFAULT_REPORT = Path("memory-bank") / "ai-sources-spike.json"


def _has_code(title: str, code: str) -> bool:
    """Return True when the catalogue code appears in the title as a whole token."""
    if not code:
        return False
    return re.search(rf"(?<!\d){re.escape(code)}(?!\d)", title) is not None


def _series_matches(name: str, products: List[Dict[str, Any]]) -> bool:
    """Return True when a Fesofi product names the series we probed for."""
    wanted = name.strip().lower()
    for product in products:
        series = (product.get("attributes") or {}).get("Título Serie") or ""
        if series.strip().lower() == wanted:
            return True
    return False


class Command(BaseCommand):
    help = "Probe Colnect, Delcampe, Iberphil and Fesofi and save the evidence (A0)."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--source",
            action="append",
            choices=SOURCES,
            help="Probe only this source (repeatable). Default: all of them.",
        )
        parser.add_argument(
            "--json",
            dest="json_path",
            default=None,
            help=f"Where to save the raw evidence (default: {DEFAULT_REPORT}).",
        )
        parser.add_argument(
            "--timeout",
            type=int,
            default=probe.DEFAULT_TIMEOUT,
            help="Per-request timeout in seconds.",
        )
        parser.add_argument(
            "--delay",
            type=float,
            default=5.0,
            help="Seconds to wait between requests to the same host.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        sources: List[str] = options["source"] or list(SOURCES)
        timeout: int = options["timeout"]
        delay: float = options["delay"]
        report_path = Path(options["json_path"]) if options["json_path"] else None

        self._timeout = timeout
        self._delay = delay
        self._last_request = 0.0

        report: Dict[str, Any] = {
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "client": "requests/urllib3 (HTTP/1.1)",
            "user_agent": probe.USER_AGENT,
            "subjects": [subject.as_dict() for subject in probe.SUBJECTS],
            "sources": {},
        }

        handlers = {
            "colnect": self._probe_colnect,
            "delcampe": self._probe_delcampe,
            "iberphil": self._probe_iberphil,
            "fesofi": self._probe_fesofi,
        }

        for source in sources:
            self.stdout.write(self.style.MIGRATE_HEADING(f"\n=== {source} ==="))
            try:
                report["sources"][source] = handlers[source]()
            except Exception as error:  # a probe must never abort the other sources
                self.stdout.write(self.style.ERROR(f"probe failed: {error}"))
                report["sources"][source] = {"error": str(error)}

        path = report_path or settings.BASE_DIR.parent / DEFAULT_REPORT
        path = path if path.is_absolute() else Path.cwd() / path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        self.stdout.write(self.style.SUCCESS(f"\nEvidence saved to {path}"))

    # ------------------------------------------------------------------
    # HTTP
    # ------------------------------------------------------------------

    def _fetch(self, url: str, label: str, method: str = "GET") -> Dict[str, Any]:
        """Perform one request and describe it; never raises on HTTP errors."""
        wait = self._delay - (time.time() - self._last_request)
        if wait > 0:
            time.sleep(wait)

        started = time.time()
        info: Dict[str, Any] = {"label": label, "url": url, "method": method}

        try:
            response = requests.request(
                method,
                url,
                timeout=self._timeout,
                allow_redirects=True,
                headers={
                    "User-Agent": probe.USER_AGENT,
                    "Accept-Language": "es,en;q=0.8",
                    "Accept": "text/html,application/json;q=0.9,*/*;q=0.8",
                },
            )
            body = response.content
            text = body.decode(response.encoding or "utf-8", errors="replace")
            challenge = probe.detect_challenge(text)
            info.update(
                {
                    "status": response.status_code,
                    "final_url": response.url,
                    "elapsed_ms": round((time.time() - started) * 1000),
                    "bytes": len(body),
                    "content_type": response.headers.get("Content-Type", ""),
                    "server": response.headers.get("Server", ""),
                    "shape": probe.response_shape(
                        response.headers.get("Content-Type", ""), body
                    ),
                    "challenge": challenge,
                    "verdict": probe.verdict(response.status_code, challenge),
                    "body_head": text[:200] if len(text) < 4000 else text[:200],
                }
            )
            self.stdout.write(
                f"  {label:<34} {response.status_code:<4} {len(body):>8} B  "
                f"{info['elapsed_ms']:>5} ms  {info['verdict']}"
            )
            info["_text"] = text
            return info
        except requests.RequestException as error:
            info.update(
                {
                    "status": None,
                    "error": type(error).__name__,
                    "elapsed_ms": round((time.time() - started) * 1000),
                    "verdict": probe.verdict(None, None, type(error).__name__),
                }
            )
            self.stdout.write(
                self.style.ERROR(f"  {label:<34} FAIL  {type(error).__name__}")
            )
            return info
        finally:
            self._last_request = time.time()

    @staticmethod
    def _public(info: Dict[str, Any]) -> Dict[str, Any]:
        """Strip the response body before the evidence is stored."""
        return {key: value for key, value in info.items() if not key.startswith("_")}

    # ------------------------------------------------------------------
    # Sources
    # ------------------------------------------------------------------

    def _probe_capi_http2(self) -> Dict[str, Any]:
        """Ask the CAPI over HTTP/2, the only protocol it accepts.

        ``requests`` cannot negotiate HTTP/2, so the 426 the probe records above
        is about the client, not about the source. ``httpx`` is a declared
        dependency, but its ``h2`` extra is not: without it this check reports the
        ImportError instead of a protocol, which is the honest answer.
        """
        try:
            import httpx
        except ImportError:
            return {"available": False, "reason": "httpx is not installed"}

        url = probe.colnect_capi_url()
        try:
            with httpx.Client(http2=True, timeout=self._timeout) as client:
                response = client.get(url, headers={"User-Agent": probe.USER_AGENT})
            return {
                "available": True,
                "httpx": httpx.__version__,
                "protocol": response.http_version,
                "status": response.status_code,
                "body": response.text[:200],
            }
        except Exception as error:  # a probe reports, it does not raise
            return {
                "available": True,
                "error": type(error).__name__,
                "reason": str(error)[:200],
            }

    def _probe_colnect(self) -> Dict[str, Any]:
        robots = self._fetch(probe.COLNECT_ROBOTS, "robots.txt")
        rules = robots.get("_text", "")
        robots_rule = probe.robots_rule(rules, "/en/stamps/list/")
        crawl_delay = "Crawl-delay: 10"

        capi = self._fetch(probe.colnect_capi_url(), "CAPI over HTTP/1.1")
        http2 = self._probe_capi_http2()
        public = self._fetch(
            probe.colnect_public_url(probe.SUBJECTS[0]), "public site (1850)"
        )

        self.stdout.write(
            "  robots: "
            + (
                "Crawl-delay 10, /en/stamps/list/ allowed"
                if robots_rule is None
                else f"blocked by {robots_rule}"
            )
        )
        self.stdout.write(
            "  CAPI body: " + str(capi.get("_text", ""))[:160]
        )
        self.stdout.write(
            f"  CAPI over HTTP/2: {http2.get('protocol')} {http2.get('status')} "
            f"{str(http2.get('body'))[:80]}"
        )

        return {
            "robots": self._public(robots),
            "robots_rule_for_list": robots_rule,
            "robots_crawl_delay": crawl_delay,
            "capi_http1": self._public(capi),
            "capi_body": str(capi.get("_text", ""))[:300],
            "capi_http2": http2,
            "public_site": self._public(public),
        }

    def _probe_delcampe(self) -> Dict[str, Any]:
        robots = self._fetch(probe.DELCAMPE_ROBOTS, "robots.txt")
        rules = robots.get("_text", "")
        search_rule = probe.robots_rule(rules, probe.DELCAMPE_SEARCH_PATH)
        searches: List[Dict[str, Any]] = []

        for subject in probe.SUBJECTS:
            info = self._fetch(probe.delcampe_search_url(subject), f"search {subject.query}")
            cards = probe.parse_delcampe_cards(info.get("_text", ""), limit=5)
            searches.append(
                {
                    "subject": subject.as_dict(),
                    "request": self._public(info),
                    "cards_returned": len(cards),
                    "cards": cards,
                    "titles_with_edifil": sum(
                        1 for card in cards if "edifil" in (card["title"] or "").lower()
                    ),
                    "titles_with_code": sum(
                        1
                        for card in cards
                        if _has_code(card["title"] or "", subject.first_edifil)
                    ),
                }
            )

        self.stdout.write(
            "  robots for "
            + probe.DELCAMPE_SEARCH_PATH
            + ": "
            + (search_rule or "allowed")
        )

        return {
            "robots": self._public(robots),
            "robots_readable": robots.get("status") == 200,
            "robots_rule_for_search": search_rule,
            "searches": searches,
        }

    def _probe_iberphil(self) -> Dict[str, Any]:
        robots = self._fetch(probe.IBERPHIL_ROBOTS, "robots.txt")
        history = self._fetch(probe.IBERPHIL_HISTORY, "history index")
        auctions = probe.parse_iberphil_auctions(history.get("_text", ""), limit=1)

        auction_url = auctions[0] if auctions else None
        results_url = f"{auction_url}/informacion-de-subasta" if auction_url else None
        lots_url = f"{auction_url}/auction-sold-lots" if auction_url else None

        results = self._fetch(results_url, "results page") if results_url else {}
        lots = self._fetch(lots_url, "sold lots table") if lots_url else {}

        home = self._fetch(probe.IBERPHIL_HOME, "home (first lot link)")
        lot_url = probe.parse_iberphil_first_lot(home.get("_text", ""))
        lot = self._fetch(lot_url, "one lot page") if lot_url else {}

        # The sold-lots table only lists the starting price; the hammer price is
        # on the lot page, one request each.
        lot_urls = probe.parse_iberphil_lot_links(lots.get("_text", ""), limit=4)
        lot_pages: List[Dict[str, Any]] = []
        for index, url in enumerate(lot_urls, start=1):
            info = self._fetch(url, f"sold lot {index}")
            lot_pages.append(
                {**self._public(info), **probe.parse_iberphil_lot(info.get("_text", ""))}
            )

        return {
            "robots": self._public(robots),
            "robots_rule_for_lots": probe.robots_rule(robots.get("_text", ""), "/es/subastas"),
            "history": self._public(history),
            "auction": auction_url,
            "auction_count_found": len(auctions),
            "results": self._public(results),
            "sold_lots": self._public(lots),
            "sold_lots_rows": probe.parse_iberphil_sold_lots(lots.get("_text", ""), limit=5),
            "lot_url": lot_url,
            "lot": {**self._public(lot), **probe.parse_iberphil_lot(lot.get("_text", ""))}
            if lot
            else None,
            "lot_pages": lot_pages,
            "search_available": self._has_search(history.get("_text", "")),
        }

    @staticmethod
    def _has_search(html: str) -> bool:
        lowered = html.lower()
        return any(
            marker in lowered
            for marker in ('type="search"', "buscador", "name=\"q\"", "name='q'")
        )

    def _probe_fesofi(self) -> Dict[str, Any]:
        home = self._fetch(probe.FESOFI_HOME, "catalogue home")

        # The public HTML pages render their product lists with JavaScript, but
        # the WooCommerce Store API answers JSON without a key.
        searches: List[Dict[str, Any]] = []
        for subject in probe.SUBJECTS:
            info = self._fetch(
                probe.fesofi_search_url(subject), f"store api {subject.first_fesofi}"
            )
            searches.append(
                {
                    "subject": subject.as_dict(),
                    "request": self._public(info),
                    "products": probe.parse_fesofi_products(info.get("_text", ""), limit=3),
                    "series_matches": _series_matches(
                        subject.name,
                        probe.parse_fesofi_products(info.get("_text", ""), limit=3),
                    ),
                }
            )

        return {"home": self._public(home), "searches": searches}
