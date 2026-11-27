# Release 2026.11.27 — checklist and notes

Prepared 2026-11-27. Last release: **2026.10.01**; **132 commits** since then, three blocks of
work: DataDesk (a new internal app), the collections screens (a new user-facing area) and the
AI API (rewritten around real sources).

The tag follows the date style already in the repo: **`2026.11.27`**.

## 1. Before tagging

- [ ] Merge the open PR of the catalogue close-out (#508) into `development`; the branch
      `development` must be what goes out.
- [ ] Suites green on `development`: backend **1.869**, frontend **853**.
- [ ] `manage.py check` and `manage.py spectacular` clean (both were, on the closing commit).
- [ ] **Backup of the production database** before touching anything:
      `docker exec -t stamps-backend python manage.py stamps_db_backup --mode full`.

## 2. The one question to settle first: migrations

`.gitignore` ignores `migrations/` **and `Dockerfile.prod.dockerignore` excludes them from
the image**, so the production container ships no migration files. This release changes the
schema in two ways:

- a new table, `ai_api_sourceobservation` (the evidence behind every price);
- two new columns, `Issue.updated_at` and `Stamp.updated_at` (`auto_now`, nullable, indexed).

So the deployed database has to be migrated by hand, and the procedure depends on whether
the server's `django_migrations` table already has rows generated in the container:

- **If it has rows from a previous in-container generation**: generate and apply the new
  ones the same way —
  `docker exec -it stamps-backend python manage.py makemigrations` then
  `python manage.py migrate`.
- **If it does not** (tables exist, no migration history): `makemigrations` followed by
  `migrate --fake-initial`, which lets Django accept the tables that already exist for the
  initial migrations.

Rehearse it on a copy of the production dump before the release: `backups/` holds the dumps
and `stamps_db_restore` loads them (see `progress.md` for what a restore cannot bring back).

## 3. Environment (`backend/.env` on the server)

Added (see `backend/.env.example`):

| Key | What it is |
| :--- | :--- |
| `OPENCODE_API_KEY` | `oc_sk_…`; the AI API's only LLM provider. |
| `OPENCODE_MODEL` | The engine, e.g. `glm-5.3`. Paid models only: the free ones give 403 outside opencode. |
| `DATADESK_ENABLED` | `False` unless DataDesk is wanted on the server. |
| `DATADESK_TLS` | `1` behind nginx, `0` without TLS. |
| `DATADESK_STAMP_IMAGES` | The mounted `<year>/<code>.webp` path, e.g. `/srv/stamp-images`. |
| `AI_BUDGET_SECONDS` / `AI_BUDGET_PER_CALL` | Optional; 25 / 8 by default. |
| `AI_SOURCE_ALLOWED_HOSTS` and the `AI_SOURCE_*` family | Optional; every host the pipeline may reach. |

Removed: `GEMINI_API_KEY`, `GEMINI_MODEL_NAME`, `GROQ_API_KEY`, `GROQ_MODEL_NAME`,
`LLM_PROVIDER`. A deployment that still sets them is harmless (nothing reads them) but they
should go.

## 4. Build and publish the images

```bash
./stamps.sh prod release          # multi-arch (amd64 + arm64) to Docker Hub, tags :latest
```

The script pushes `osrogon/stamps-backend:latest` and `osrogon/stamps-frontend:latest`; it
does not create a versioned tag, so the release label lives in git and in the notes, not in
the image name.

## 5. Tag and publish the notes

```bash
git checkout development && git pull
git tag -a 2026.11.27 -m "Release 2026.11.27"
git push origin 2026.11.27

gh release create 2026.11.27 --title "2026.11.27" \
  --notes-file memory-bank/release-2026.11.27-notes.md
```

(The release body is `memory-bank/release-2026.11.27-notes.md`, the same text as section 6.)

## 6. Release notes

```markdown
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
```

## 7. After the deploy

- [ ] `/api/v1/issues/` answers with the master key and the login returns a JWT.
- [ ] Collections: the overview, a series list and a series detail open; the add dialog finds
      the catalogue and adds a stamp.
- [ ] `/datadesk/login/` answers 404 when `DATADESK_ENABLED=False`, and shows the login when
      it is on.
- [ ] A stamp picture is visible in the series detail (checks `DATADESK_STAMP_IMAGES` only
      matters for DataDesk; the public screens read the frontend's own assets).
- [ ] The AI endpoint answers with `sources` filled and `valuation` null or with numbers, not
      with the old invented market values.
