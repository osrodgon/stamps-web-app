# AI API

One endpoint that researches a stamp series: it finds the series in a catalogue,
reads its facts from the catalogue's own API, prices its stamps in a shop and in an
allowed-site search, and has an LLM write the text from those facts. Every number
travels with the page that supports it, and anything nobody can back is `null` and
reported in `gaps`.

The model is not a source. It normalises and writes; it does not remember philately
and it is not allowed to invent a code, a date or a price.

- **Endpoint:** `POST /stamps-backend/api/v1/issues/extraction/`
- **Auth:** master key only (`Authorization: API-KEY <key>` with `X_API_MASTER_KEY`);
  the view is deliberately **not** in `USER_VIEWS`.
- **Cost per request:** a handful of catalogue calls, one shop lookup and one search
  per priced stamp, one or more LLM calls. `AI_PRICE_STAMPS` and the budget in
  `AI_BUDGET_*` are what keep that finite.

The plan behind the module is `memory-bank/ai-api-plan.md`; what each source actually
answered, with status codes, is `memory-bank/ai-sources-spike.md`.

---

## How a request flows

1. **Identity.** `FesofiCatalogue.identify(name, date)` asks the Fesofi Store API by
   attribute (`Título Serie` and `Motivo Sello`, with the year as a filter). The
   search is partial and case-insensitive, so `castillos de españa 2007` lands on the
   series named `Castillos`. Candidates are tried in order of word coverage and the
   first one with products wins. A tie between two equally good candidates is a
   `gap`, not a guess.
2. **Facts.** `facts(products)` reads the catalogue product attributes: Edifil and
   Fesofi codes, face value, colour, perforation, print run, date, motive and the
   catalogue description (HTML stripped). The keys are the same the scraper used to
   produce.
3. **Fallback.** If the catalogue has no answer, `SearchService` finds a page and
   `ScrapingService` reads it; the response says so with an `identity` gap. The old
   path still exists, it is just no longer the first one.
4. **Prices.** `FilateliaCatalogue` asks the shop by `Nº Edifil` (with `Estado` and
   `Año`); `SearchPrices` searches the allowed sites and, when the snippet has no
   price or no condition, opens the listing page (at most three per query). A sold
   listing is a sale (`kind: "sold"`), not an asking price.
5. **Valuation.** `valuation.value()` makes a **trimmed mean** per condition: the
   lowest and the highest are dropped from four observations up, three is the
   minimum sample, and only euros are averaged. A price without a condition cannot
   be averaged and is not counted.
6. **Text.** The model writes the description and normalises the catalogue fields.
   `validation.check_support()` then compares every factual field against the facts
   of the request and nulls whatever they do not support.
7. **Budget.** `Budget` is a clock: each call gets the smaller of its timeout, the
   per-call ceiling and what is left. When it runs out the endpoint stops pricing and
   answers with what it has, `partial: true` and a `budget` gap.

## Sources

| Source | What it gives | Where |
| :--- | :--- | :--- |
| Fesofi Store API | Identity and catalogue facts (codes, face value, print run, colour, perforation, date, motive) | `sources/fesofi.py` |
| Filatelia.online (WooCommerce Store API) | Asking prices by Edifil code, with `Estado` as the condition | `sources/filatelia.py` |
| Allowed-site search (Serper) | Asking and sold prices from search results | `sources/search_prices.py` |
| TodoColeccion listing pages | Price and condition read from the listing itself | `sources/listings.py` |
| The model | Prose and normalisation only | `services/opencode_provider.py` |

Every outbound call goes through `sources/http.py`: an allowlist of hosts, timeouts,
retries with jitter for 5xx/429, a per-host concurrency limit, a TTL cache and our own
User-Agent. A host outside the list is refused before the request leaves the process,
and the direct-URL shortcut (`name` = URL, `date` = `"0"`) is subject to the same
allowlist — otherwise the endpoint would be an authenticated HTTP proxy.

Out of the plan on purpose: **Colnect** (dropped 2026-11-26), **Delcampe**
(`robots.txt` forbids its search path) and **eBay** (its item pages answer 403 to our
client, so no parser was written). **Iberphil** is a maybe for a later version: it
only publishes a hammer price per lot, and never a catalogue code.

## Request

```json
{
  "name": "Navidad 1986",
  "date": "1986"
}
```

| Field | Type | Description |
| :--- | :--- | :--- |
| `name` | string | Series name or the motive of one of its stamps. Max 200 characters. |
| `date` | string | Publication date. A four-digit year is enough; `"0"` only with a URL as `name`. |

`name` may also be a catalogue URL when `date` is `"0"`, in which case the page is
scraped directly and the host must be in the allowlist.

## Response

```json
{
  "issue_name": "Navidad",
  "description": "Sello dedicado a la Natividad…",
  "description_source": "llm",
  "issue_date": "1986-11-16",
  "artist": "n/a",
  "printer": "Fábrica Nacional de Moneda y Timbre",
  "print_type": "Offset",
  "perforation": "13 3/4",
  "paper_type": "n/a",
  "stamp_type": "n/a",
  "notes": "n/a",
  "total_printed": 4000000,
  "market_value_mnh": null,
  "market_value_used": null,
  "sources": [
    {"source": "fesofi", "status": "ok", "url": "", "fetched_at": "…"},
    {"source": "filatelia", "status": "empty", "url": "", "fetched_at": "…"},
    {"source": "search", "status": "ok", "url": "", "fetched_at": "…"}
  ],
  "observations": [
    {
      "source": "search",
      "external_id": "",
      "url": "https://www.todocoleccion.net/…",
      "issue": null,
      "stamp": null,
      "subject_code": "2867",
      "kind": "ask",
      "price": 2.9,
      "currency": "EUR",
      "condition": "mnh",
      "observed_at": "2026-11-26T11:30:00Z"
    }
  ],
  "valuation": null,
  "partial": false,
  "gaps": [{"field": "artist", "reason": "No source supports this value."}],
  "stamps": [
    {
      "edifil_code": "2867",
      "fesofi_code": "2884",
      "face_value": "17 PTA",
      "description": "Natividad. Toledo",
      "description_source": "llm",
      "color": "Multicolor",
      "market_value_mnh": 4.45,
      "market_value_used": null
    }
  ]
}
```

| Field | Meaning |
| :--- | :--- |
| `description_source` | `llm` means the model wrote the text from the facts; it is not a catalogue quote. |
| `sources` | One row per source consulted, for identity and for prices: `ok`, `empty` (asked, had nothing), `skipped` (never asked), `error` (the source broke). |
| `observations` | Every price found, with the page that supports it and the catalogue code it prices. This is the evidence; the estimate is built from it. |
| `valuation` | A **series-level** estimate. Always `null` today: a series is not the sum of its stamps, and no source sells the complete set as one item. |
| `partial` | `true` when the request ran out of budget. Asking again is cheap — the cache answers most of it. |
| `gaps` | What could not be filled in and why, capped at 20 entries per kind. |

`market_value_mnh` / `market_value_used` on a stamp are the trimmed mean of the
observations for that code and that condition. They are **deprecated on the series**
(always `null`) and are kept in the schema for shape compatibility.

### What the numbers mean

- **Asking price, not a sale.** Most observations are `kind: "ask"`; a sold listing is
  `kind: "sold"`. The method is written down next to the figure.
- **Three prices minimum, per condition.** One or two observations are a `gap`, not an
  average.
- **Euros only.** A price in another currency is not converted; no exchange rate is
  invented.
- **Condition comes from the source.** A bare "nuevo" is not `mnh`; when nobody states
  it, the observation is `unknown` and does not enter an estimate.
- **Nothing is discounted.** The old prompt applied a −25 % "correction". There is no
  such correction here: the trimmed mean is the whole method.

## Errors

| Status | When |
| :--- | :--- |
| `400` | Invalid payload, or a URL whose host is not in the allowlist. |
| `401` / `403` | Missing, invalid or insufficient credentials (this endpoint needs the master key). |
| `404` | Neither the catalogue nor the search found anything; the message says why. |
| `422` | The model answered something the contract cannot accept, or nothing was scraped from the page. |
| `500` | The module is not configured (missing key or URL) or an internal error. |
| `502` | A source is down or answered HTTP 5xx without recovering. |

A single source failing generally does **not** fail the request: it becomes an `error`
row in `sources` and the rest of the answer stands.

## Settings

| Variable | Default | Description |
| :--- | :--- | :--- |
| `OPENCODE_API_KEY` | — | Console inference key (`oc_sk_…`). Required. |
| `OPENCODE_MODEL` | — | Model id, sent in the request body. Required. |
| `OPENCODE_BASE_URL` | `https://opencode.ai/inference/openai/v1` | API root. |
| `OPENCODE_TIMEOUT` | `120` | Seconds per LLM call. |
| `OPENCODE_MAX_TOKENS` | `8192` | Answer budget per call. |
| `LLM_BATCH_SIZE` | `5` | Stamps per LLM call; calls are made in series. |
| `SERPER_API_KEY` / `SERPER_URL` | — | Search backend for the allowed-site prices. |
| `AI_SOURCE_ALLOWED_HOSTS` | Fesofi, filatelia.online, TodoColeccion, eBay, Serper | Hosts the module may reach, comma-separated. Subdomains are allowed. |
| `AI_SOURCE_TIMEOUT` | `20` | Seconds per outbound request. |
| `AI_SOURCE_CONNECT_TIMEOUT` | `5` | Seconds to connect. |
| `AI_SOURCE_RETRIES` | `2` | Extra attempts for 5xx / 429. |
| `AI_SOURCE_MAX_PER_HOST` | `4` | Concurrent requests per host. |
| `AI_SOURCE_CACHE_TTL` | `3600` | Seconds a `200` answer is reused. |
| `AI_SOURCE_USER_AGENT` | `stamps-web-app/0.1 (+repo)` | Honest User-Agent; not a browser. |
| `AI_PRICE_STAMPS` | `5` | Stamps per series priced in one request. |
| `AI_BUDGET_SECONDS` | `25` | Wall clock for the whole request. |
| `AI_BUDGET_PER_CALL` | `8` | Ceiling for one outbound call. |

Free-tier Console models only work from inside opencode; other clients get `403`, so
the backend needs a paid model (or Go). The engine is a deployment choice, not a code
constant: swap `OPENCODE_MODEL`.

## Pricing the catalogue: `ai_prices_backfill`

The endpoint prices one series. Filling the database is a command:

```bash
python manage.py ai_prices_backfill --limit 10 --dry-run
python manage.py ai_prices_backfill --source filatelia --only 842
python manage.py ai_prices_backfill --stamps 3
```

| Flag | Description |
| :--- | :--- |
| `--limit N` | Stop after N series (0 = all). |
| `--source filatelia\|search` | Price only this source (repeatable). Default: both. |
| `--only ID` | Walk these issue ids (repeatable). |
| `--stamps N` | Price only the first N stamps of each series (0 = all). |
| `--dry-run` | Ask and report, write nothing. |

Observations are stored as `SourceObservation` rows attached to the real `Stamp`.
`raw_hash` is their identity, so running the command twice does not duplicate the
evidence. A source that fails is logged and the walk continues.

**Where research is triggered, decided in A8:** DataDesk and the Flet app ask the
endpoint for one series; the command fills the catalogue. There is no queue, no Celery
and no worker container.

## Tests

```bash
python -m pytest ai_api -q
```

The suite never touches the network: every HTTP test uses `httpx.MockTransport`, and
the view tests stub `FesofiCatalogue`, `FilateliaCatalogue` and `SearchPrices`.

## What this module does not do

- **Value a complete series.** No source sells the set as one item, so
  `valuation` at series level stays `null` instead of adding up its stamps.
- **Convert currencies.** A price in dollars or pounds is left out.
- **Read eBay.** Its item pages answer 403 to the server.
- **Judge prose.** `check_support()` verifies codes, dates, numbers and catalogue
  fields; a description is labelled `llm` and cannot be checked against a source
  without reading it.
- **Write to the catalogue.** The endpoint has no subject to attach an observation to;
  that is the backfill command's job, and the import path is a later step.
