## DataDesk, a database workbench for one editor

A new internal app at `/datadesk/`, off by default (`DATADESK_ENABLED`), with its own staff
login and throttling. It edits the database directly instead of going through `/api/v1/`:
a filterable workbench with the "needs attention" queues, a workspace per series with its
stamp grid and pictures, a change set that is reviewed and committed in one transaction,
reference tables with usage counts and merge, an activity log with per-commit revert, and a
pre-commit backup. English and Spanish, keyboard-driven.

## Collections for the normal user

A user can now see and fill their collection from the frontend: the overview with a collage
and counters, the series of a collection with progress and what was paid, the series detail
with the catalogue read-only and "your copy" editable, and a dialog that adds **a stamp, a
whole series or a whole year** in one request. The collection and its items are scoped by the
user's JWT: another user's rows answer 404.

## The AI API answers with evidence

The extraction no longer invents philately: the series is identified in the Fesofi catalogue
and its facts are read from there, prices come from `filatelia.online` and an allowed-site
search (the condition is read from the listing), and the value is a trimmed mean over at
least three observations per condition. Every price travels with the page that supports it
(`SourceObservation`), the model can no longer state a code, a date or a number the sources
do not carry, a request has a time budget and answers `partial`, and
`manage.py ai_prices_backfill` fills the catalogue without duplicating evidence. The only
LLM provider is opencode.

## Fixes and polish

- The collection screens no longer collapse on a wrapping row, a `BASELINE` alignment or a
  floating scrollbar over the cards.
- The series list is ordered by the catalogue code after the date, so two series of the same
  day no longer swap places between pages.
- The series detail walks the list with `‹ n / total ›` and can remove a series from the
  collection with its copies, never from the catalogue.
- DataDesk: the refused cell's ring stays visible, the plate behind a stamp picture is grey
  instead of white, money and dates are written the way the language writes them, and the
  date is picked in a calendar of its own.

## Upgrading

- **Migrations**: the new `ai_api_sourceobservation` table and the `updated_at` columns on
  `Issue` and `Stamp` have to be generated and applied in the backend container; see the
  release checklist.
- **Configuration**: `GEMINI_*`, `GROQ_*` and `LLM_PROVIDER` are gone; `OPENCODE_API_KEY` and
  `OPENCODE_MODEL` are the new engine settings, and `DATADESK_*` turns the internal app on.
- `/api/v1/` keeps its shape: the new `updated_at` columns are excluded from the response
  serializers and the schema has no new warnings.
