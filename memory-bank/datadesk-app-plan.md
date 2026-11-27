# DataDesk — Database Maintenance App (Design)

> **Status**: Design closed / ready to implement. Nothing implemented yet.
> **Problem**: The Flet frontend can do maintenance, but only one record at a time
> (one dialog, one POST, one reload). Fine for "add a series" or "fix a value",
> painful for sessions where you touch 50 issues and 400 stamps.
> **Explicitly excluded**: Django Admin (already customized in
> `backend/_backend/stamps_admin_site.py`, still too slow for this job).
> **Name**: `DataDesk` — renamed from "Curator" on 2026-11-18. "Curator" sounded
> like conservation; the point of this app is the opposite: editing the database
> **directly**, without going through `/api/v1/` and without the per-record
> round-trips of the Flet frontend. The name says what it is.

---

## 0. Decisions taken (2026-11-17)

| Decision | Choice | Consequence |
|---|---|---|
| Users | **One person, but deployed on an external server** | Own login page (username + password, Django session), `is_staff` gate on every datadesk view, login throttling, TLS via reverse proxy, optional IP allowlist. Still single-actor: no roles, no per-user permissions, no conflict resolution |
| Images | **Out of scope** | No drag&drop, no paste, no thumbnails; read-only "has image" flag + a `sin imagen` work queue only |
| UI language | **English + Spanish** | Django i18n with its own catalog in `backend/datadesk/locale/`; never `assets/locales/en.json` / `es.json` |
| CSV import | **Out of scope** | Database is up to date; no dry-run importer, no CSV export either |
| Database state | Current, no backfill needed | Adding `updated_at` is a clean migration with no data migration |

---

## 1. What "maintenance" actually means here

Measured against the real schema, the recurring jobs are:

| Job | Frequency | Current cost |
|---|---|---|
| Ingest a new year: 20–60 issues, each with 2–12 stamps | per catalog batch | hours |
| Fix wrong/typo'd lookups (artist, printer, paper type) across many issues | constant | one dialog per issue |
| Fill missing data (no country, no date, no face_value, no colors) | constant | record by record |
| Add stamps to an existing issue (5–10 at once, similar fields) | constant | 5–10 dialogs |
| Delete/merge duplicated lookups and reassign references | occasional | not possible in Flet |
| Re-check a series against the printed catalog (side-by-side) | per batch | open/close rows |

Two structural facts drive the design:

1. **Issue and Stamp are one unit of work.** `Issue.stamps` is a cascade, and
   most fields are inherited/duplicated from the issue to its stamps. Any tool
   that edits them in separate screens is the reason the current flow is slow.
2. **9 of the 16 tables are lookups** with `unique name` (Year, Country, Color,
   Artist, Printer, PaperType, PrintType, StampType, ConditionType). Cheap,
   repetitive CRUD + merge → generic screen, one implementation.

Since the database is already current, the bottleneck is not bulk ingest but
**many small touches per session**. That is what the change-set buffer (§4) and
the "needs attention" queues (§3.1) are for.

---

## 2. Stack decision

### Options considered

| Option | Verdict |
|---|---|
| **A. Internal Django app, server-rendered + HTMX + Tabulator** | **Recommended** |
| B. Standalone SPA (React/Svelte) against the DRF API | Rejected: needs new bulk endpoints anyway, plus auth duplication and a second deploy |
| C. Flet desktop app | Rejected: same API limits as B, and Flet is the thing we're escaping |
| D. TUI (Textual) | Rejected now that images/CSV are out — but still the natural fit for a later CLI add-on |
| E. Django Admin customization | Excluded by the user |

### Why A

- **Direct ORM access**. Bulk edit = one `transaction.atomic()` + `bulk_update`,
  not N HTTP round-trips through serializers. `Stamp.colors.set()` in bulk,
  `select_related`/`prefetch_related` for the grid load.
- **True multi-object transactions** with per-row error reporting. The current
  API is one object per request; a 40-row edit is 40 requests and 40 chances to
  end up half-applied.
- **No new public API surface.** Nothing lands under `/api/v1/`, so the mobile
  app contract and the DRF schema stay untouched.
- **Same container, same DB, same settings.** Mount at `/datadesk/`.
- Reuses `stamps_db_backup` management command (already exists) for pre-commit
  safety snapshots on large commits.
- The team is Python-only; this adds templates and one JS lib, not a new
  toolchain.

### Libraries (all vendored locally, no CDN — the app runs in Docker, possibly offline)

- **HTMX 2** — panel/form posts, partial refreshes, no build step.
- **Alpine.js 3** — local UI state (selection, change counter, dirty flags).
- **Tabulator 6** — the dense grids: inline cell editing, keyboard nav, virtual
  scroll for thousands of rows, range selection, change tracking
  (`getChanges()`), built-in undo history.
  *Nice to have*: clipboard paste from a spreadsheet — needs a spike, and is not
  on the critical path now that CSV is out.
- No npm, no bundler. Files under `backend/datadesk/static/datadesk/vendor/`.

---

## 3. Screen map

```
/datadesk/login/               → login (username + password, redirects back to ?next=)
/datadesk/logout/              → POST-only logout
/datadesk/                     → Dashboard (counts + "needs attention" queues)
/datadesk/issues/              → WORKBENCH   (dense grid, one row per issue)
/datadesk/issues/new           ┐
/datadesk/issues/<id>/         ┘ ISSUE WORKSPACE, mode=new | edit (one template)
/datadesk/lookups/<table>/     → generic lookup CRUD + usage counts + merge
/datadesk/activity/            → audit log + revert per commit
```

Auth lives **under the same prefix**, so the gate is one rule. Note it must not
collide with the existing `/api/v1/login/` (DRF, JWT) — different namespace,
different mechanism, no shared code.

Everything except `/datadesk/login/` sits behind the staff gate (§8).

### 3.1 Workbench (`/datadesk/issues/`)

The default landing screen. One row per issue, ~60 rows visible, virtualized.

- Columns: year, date, name, country, stamp_type, print_type, printer, artist,
  paper_type, perforation, total_printed, market_value_mnh, market_value_used,
  **stamps count**, **missing-data badge**.
- Filters (persisted in URL and localStorage): year range, text search on name,
  country, stamp_type, and a **"needs attention" selector**:
  `no country` · `no date` · `no stamps` · `stamps without colors` ·
  `stamps without face_value` · `no image`. This last one is the feature that
  turns maintenance from browsing into a work queue.
- Inline editing, multi-cell range edit (set `country=Spain` on 30 rows at once),
  column sort/group by year, row expand-in-place showing its stamps read-only
  with a link into the workspace.
- Row actions: open workspace, clone, delete (with dependency preview).

### 3.2 Issue workspace (`/datadesk/issues/new` and `/datadesk/issues/<id>/`)

**One screen for both creating and editing a series.** Same template, same
components, one `mode` parameter. Creating a series and fixing a series must not
feel like two different tools, otherwise the two views drift apart and every
improvement has to be built twice.

```
┌ Issues / 1987 / "Exposición de Málaga" ────── [clone] [delete] ────┐
│ year · date · name · country · stamp_type · print_type ·           │
│ printer · artist · paper_type · perforation · total_printed ·      │
│ market_value_mnh · market_value_used · description / note          │
├ Stamps (8) ── rows[8] [generate] [fill series] [paste] [fast row] ┤
│ edifil fesofi name        face_value colors      mnh  used  img    │
│ 2744   1234   Retrato…    15 Pta     [Carmín]    1.20 0.80   ▢     │
│ 2745   1235   Retrato…    15 Pta     [Carmín]    1.20 0.80   ▢     │
└────────────────────────────────────────────────────────────────────┘
  New issue + 8 stamps · nothing saved yet       [Create issue + 8 stamps]
```

Shared behaviour, identical in both modes:

- **Inheritance.** `Stamp` only stores `issue`, the catalog codes, `face_value`,
  `name`, `description`, `image`, `colors`, `total_printed` and the two market
  values. Country, year, stamp type, print type, printer, artist, paper type and
  perforation are **series attributes**: they live once in the metadata strip and
  are never repeated per row, because a stamp belongs to exactly one series and
  no exception exists (decided 2026-11-18).
  **Nothing is inherited** (decided 2026-11-18, superseding the earlier grey/`↺`
  design). Every value on a stamp belongs to the stamp: the series values
  describe the **set**, not its members. The print run is the run of the whole
  series and the two market values are what the complete series is worth — which
  is normally *less* than the sum of its stamps — so an equal number is a
  coincidence, never a copy. The stamp `name` is its own for the same reason.
  In practice: the strip shows the series values, the grid shows the stamp
  values, and nothing is pre-filled per row except the `name` required to create
  a row, which is a default value and not an inheritance.
- **Fast row mode** (default on): only `edifil`, `fesofi`, `face_value`, `colors`
  are visible; a toggle reveals the rest. Typing a series is 4 columns wide.
- **Toolbar**: `rows=N` + generate, `fill series` (auto-numbers the `edifil`
  column consecutively, preserving variant suffixes: `2744a → 2744b`), paste TSV
  rows from the clipboard, fast-row toggle.
- **Duplicate row** (`Ctrl+D`) — covers the "next stamp is identical except
  edifil and face_value" case, which is most of the typing.
- **Colors**: chip multi-select with type-ahead, creating a new `Color` inline.
- **Lookups inline**: any missing lookup (a new year, artist, printer…) is
  created from the cell without leaving the screen.
- **Image column is read-only** (`▣` / `▢`), no upload, no preview. It exists so
  the `no image` queue has something to point at.
- **Footer**: the change-set summary and one commit button (`Ctrl+Enter`).
- **Keyboard**: same map everywhere (§4).

Mode differences, and nothing else:

| | `mode=new` | `mode=edit` |
|---|---|---|
| Route | `/datadesk/issues/new` | `/datadesk/issues/<id>/` |
| Opened by | `N` from the workbench | row click / Enter |
| Prefill | metadata from the **last issue** (`↺ Use last issue` to re-apply) | the issue as stored |
| Top-bar actions | `↺ Use last issue` | `Clone`, `Delete` (dependency preview) |
| Change-set operations | creates only | updates, creates, deletes |
| Footer label | "New issue + 8 stamps · nothing saved yet" | "12 changes not saved" |
| Draft recovery | none — finish it now or start again | buffer recalled from `localStorage` after a reload |
| Commit button | `Create issue + N stamps` | `Commit N changes` |
| `Shift+Enter` | create the issue shell only (stamps are optional) | commit the focused row |
| After commit | stays put with `Create another in this year`, metadata still loaded | back to the workbench, focus on the saved row |

**Entering a whole year never leaves the screen.** With the `mode=new` loop, 30
issues of the same year are 30 passes through one form that is already 80% filled.

### 3.3 Lookups (`/datadesk/lookups/<table>/`)

One template for the **8 lookup tables in scope** (`ConditionType` stays in the
admin: only user collections use it), driven by a registry:

- Grid of `name` + **usage count** (issues/stamps referencing it) + created date.
- Inline rename with live propagation preview ("used by 143 stamps").
- **Merge**: pick A and B → all references move from B to A, B is deleted, in one
  transaction. Fixes the duplicate-artist/duplicate-printer mess that no current
  screen can fix.
- Unused rows (count = 0) highlighted → safe to delete.
- `Year` is numeric, so it also gets a "create the next 10 years" quick action.

### 3.4 Activity (`/datadesk/activity/`)

Every commit writes rows to `DataDeskChange` (§5). Single actor, so the screen is a
plain reverse-chronological list (date, **actor**, table, object, op, fields
changed) with a **Revert this commit** action that applies the inverse change
set. No user filters, no role scoping — but the actor is visible, and reverts are
attributed too. This replaces "I hope I didn't break anything".

---

## 4. The core interaction: the change set

The reason ad-hoc dialogs are slow is that every edit is its own commit. DataDesk
inverts this:

1. Every edit (cell, bulk range, add row, delete row) is added to an in-memory
   **change set**: `{model, object_id|null, op: create|update|delete, patch}`.
2. Grid keeps showing optimistic values; changed cells are marked.
3. `Review & commit` opens a side panel: table of N changes, grouped by model,
   with before → after per field.
4. Commit posts the whole set once:
   `POST /datadesk/apply` → `transaction.atomic()` → per-row validation → apply
   → audit rows → JSON result `{applied: 39, rejected: [{row, errors}]}`.
5. Rejected rows stay in the buffer, applied rows disappear from it.
6. Uncommitted **edits to an existing issue** are mirrored to `localStorage` so a
   closed tab doesn't lose 40 edits. In `mode=new` there are no drafts: a series
   is finished now or started again (decided 2026-11-18), so nothing is persisted
   there. Two tabs on the same issue: warn, don't block (single user).

Single-edit commits still exist (`Shift+Enter` = save that row now) for the
"fix one typo" case, so the tool doesn't force ceremony where it isn't needed.

### Keyboard contract (non-negotiable for speed)

`/` search · `j`/`k` next/prev row · `N` new issue · `Enter` edit ·
`Tab` next cell · `Esc` revert cell · `Shift+Enter` commit row ·
`Ctrl+D` duplicate row · `Ctrl+Z` undo in buffer · `Ctrl+Shift+Z` redo ·
`Ctrl+Enter` commit all.

### Server contract

```
POST /datadesk/apply            change set → transaction → per-row results
POST /datadesk/issues/clone     source issue (+stamps) → new issue, year/date overridable
POST /datadesk/lookups/merge    {table, from_id, to_id}
GET  /datadesk/grid/issues      filtered/paginated JSON for Tabulator
GET  /datadesk/grid/stamps      ?issue_id=...
POST /datadesk/backup           runs stamps_db_backup before a bulk commit
```

Views stay thin; all logic lives in `backend/datadesk/service.py`
(`apply_change_set`, `clone_issue`, `merge_lookup`, `bulk_upsert_stamps`,
`missing_data_report`), following rule #3 of `opencode_rules.md`.

---

## 5. Data changes

### Required (Phase 1, clean migration — DB is current)

- `Issue.updated_at` / `Stamp.updated_at` (`auto_now=True`, `db_index=True`).
  Needed for: audit "before" snapshots, "recently touched" sorting, and a
  same-row-conflict warning (two tabs).
- **Nothing else.** `Stamp` does not gain series columns. Country, year, stamp
  type, print type, printer, artist, paper type and perforation are attributes of
  the series, shared by all its stamps, and a stamp belongs to exactly one series
  — no exception exists in the data (decided 2026-11-18). The alternative
  (`NULL = inherit`, stored value = override) was considered and rejected; if it
  is ever needed it is an additive, instantly-applied migration in Postgres.

### New table

```python
class DataDeskChange(models.Model):
    created_at  = models.DateTimeField(auto_now_add=True, db_index=True)
    user        = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)  # always set: request.user
    commit_id   = models.UUIDField(db_index=True)   # groups one commit
    model_label = models.CharField(max_length=64)   # "stamps_api.Stamp"
    object_id   = models.BigIntegerField(null=True)
    operation   = models.CharField(max_length=8)    # create|update|delete
    before      = models.JSONField(null=True)
    after       = models.JSONField(null=True)
    reverted_at = models.DateTimeField(null=True, blank=True)      # set when S21 reverts this row's commit
    reverts_commit_id = models.UUIDField(null=True, blank=True)    # on revert rows: the commit they undo
```

A commit containing a `merge` is **not revertible**: the audit stores the
reference count, not the ids that moved. Everything else is.

No soft-delete. Deleting is a legitimate maintenance action, and the audit log
plus the existing backup command give a recovery path without polluting every
query in the app with `is_deleted` filters.

### Delete safety

Deletion always shows the dependency preview first, computed server-side:

> Delete issue "Exposición de Málaga 1987"? This will also delete **8 stamps**
> and **14 collection items** belonging to 3 user collections. Type the year
> (1987) to confirm.

---

## 6. Scope boundaries

In scope: `Issue`, `Stamp`, `Color`, `Year`, `Country`, `StampType`,
`PrintType`, `Printer`, `Artist`, `PaperType`.

Out of scope: `User`, `APIKey`, `Collection`, `CollectionItem`,
`ConditionType`, `Location`, `Config`, `UserCollection`, `UserToken` (stay in
Django Admin); **image upload** (the pictures are displayed read-only from the frontend's folder since S10b, but nothing uploads or imports them); **CSV import/export**.

---

## 7. Implementation phases

| Phase | Deliverable |
|---|---|
| 1 | Scaffold: `backend/datadesk/`, `/datadesk/` mount, `DATADESK_ENABLED` flag, **login/logout pages + staff gate + login throttling**, local-only port publish, base template with vendored HTMX/Alpine/Tabulator, django i18n catalog (en/es), `updated_at` + `DataDeskChange` migrations, `service.py` skeleton |
| 2 | Read-only Workbench + Issue Workspace (both modes on one template): grids, issue→stamp inheritance display, filters, "needs attention" queues, navigation, performance check on the real dataset |
| 3 | Inline editing + single-row commit + audit; `mode=new` flow (last-issue defaults, `rows=N`, edifil auto-numbering, fast row mode, create-another loop); stamp row add/duplicate; inline lookup creation from a cell |
| 4 | Change set / review panel / transactional commit / clone issue / `Ctrl+Z` |
| 5 | Lookup CRUD + usage counts + merge; dashboard queues; activity log + revert; keyboard polish; tests |

Testing: `pytest-django` throughout — `service.py` unit tests (transaction
rollback on partial failure, merge correctness, cascade preview counts) and view
tests via the Django test client. No browser tests unless the JS grows beyond
glue.

---

## 8. Security / ops (single user, external server)

The app and the database live on a remote server. That changes the threat model:
the tool mutates the production catalog and can delete issues and stamps, so
authentication is not optional even if the port is firewalled.

### Authentication

- **Own login page**, plain Django `LoginView` + a template styled like the rest of
  DataDesk: username + password. No JWT, no API keys — server-rendered sessions
  only, so there is no token to leak from a browser.
- **Gate**: a single `DataDeskAccessMixin` requiring `request.user.is_staff`
  (plus `is_active`). Applied to *every* view, including the JSON endpoints
  (`/datadesk/grid/*`, `/datadesk/apply`, `/datadesk/lookups/merge`,
  `/datadesk/backup`) — those are the easy ones to forget, so a middleware-level
  `/datadesk/` prefix check backs it up. `LOGIN_URL` points at
  `/datadesk/login/`, not at `/admin/login/`.
- **Logout**: POST only (`LogoutView`), no GET logout.
- **Session**: `SESSION_COOKIE_AGE` 14 days, `SESSION_COOKIE_HTTPONLY`,
  `SESSION_COOKIE_SAMESITE=Lax`; shared with `/admin/` since it is the same
  Django project and the same superuser.
- **Throttling**: cache-based counter on the login view — 5 failures per
  IP+username in 5 minutes → 429 with backoff. No new dependency; `django-axes`
  only if this ever goes to multiple users.
- **Passwords**: Django validators already configured in `settings.py`. The
  existing superuser works as-is; no separate user model.
- **Audit attribution**: `DataDeskChange.user = request.user`. With auth in place
  the column stops being decorative: the Activity screen (§3.4) shows the actor
  on every commit, and revert is attributed too.

### Transport and exposure

- TLS is terminated by the reverse proxy (nginx/Caddy in front of the container),
  which also proxies to the app on `127.0.0.1:8001` — the Django port is never
  published publicly. Set `SECURE_PROXY_SSL_HEADER`, `CSRF_TRUSTED_ORIGINS`, and
  `SESSION_COOKIE_SECURE` / `CSRF_COOKIE_SECURE` under `DATADESK_TLS=1`.
- **Second layer**: nginx `allow <your-ip>; deny all;` on `/datadesk/`, or the
  same rule at the firewall. Cheap, and it means a stolen password alone is not
  enough from a foreign IP.
- `DATADESK_ENABLED=False` by default: the whole URL prefix (login included) is
  not registered unless set, so a stray deploy cannot expose the tool.
- CSRF on all POSTs (HTMX sends the token via `hx-headers`).
- Every destructive or bulk action is audited; `POST /datadesk/backup` calls the
  existing `stamps_db_backup` command so a snapshot exists before big commits.
- Same `backend` container and image → no new Dockerfile, no new compose service.
  Additions: the `gettext` binary for `compilemessages`, and
  `docker-compose.datadesk.yml` for the port/locals settings.

### Optional 2FA (documented, not built)

Kept out of Phase 1–5 on purpose: with a single user and an IP allowlist, the
allowlist already blocks credential stuffing from anywhere else. Build it if the
tool ever has to be reachable from arbitrary IPs, or if the password is going to
be typed on a machine you don't own.

If built, do it with **TOTP via `django-otp`** — no custom JS, no external
service, no email/SMS dependency:

- `TOTPDevice` per user (`django_otp.models.TOTPDevice`), one device only.
- **Enrolment without a UI**: `manage.py datadesk_totp_enroll --user <name>`
  prints the `otpauth://` URI plus an ASCII QR (`segno`), scanned once. No
  enrolment screen means no screen to protect, and no "reset 2FA" endpoint.
- **Two-step login on the existing `/datadesk/login/`**: `authenticate()` without
  `login()`, keep `user.pk` in the session, ask for the 6-digit code, then
  `verify_token(device, code, valid_window=1)` → `login()` + session rotate.
- **Enforced in middleware**, not just in the view: require
  `request.user.is_verified()` in addition to `is_staff`. Checking only at login
  would let a password alone open every other URL.
- Replay protection comes from `django-otp` (a token can't be reused);
  add a code-step throttle (3 tries / 5 min, cache-based) and
  `valid_window=1` for clock drift.
- **Recovery codes**: 5 single-use codes hashed with Django's hashers, generated
  at enrolment, shown once. Losing the phone must not mean losing the tool.
- Tests: `freezegun` to freeze time and `pyotp` to compute the expected code.

Stronger but heavier: **passkey/WebAuthn** with `fido2` + a small JS shim —
phishing-resistant and no shared secret, but needs HTTPS, per-browser
registration, and a device-loss plan. Not worth it for one user.

Honest ranking of value here: IP allowlist > TLS > long unique password > 2FA.
2FA protects against a leaked password, not against a compromised server.

### Deliberately not built

Per-object permissions, roles, and multi-user conflict resolution. Revisit only
if a second person ever needs access.

---

## 9. Deliberately deferred

- Images: upload, rename, dedupe, preview.
- CSV import with dry-run diff, and CSV export.
- Command palette (`Ctrl+K`) and clipboard paste from a spreadsheet.
- `CollectionItem` maintenance and the user-facing tables.
- Multi-user concerns: per-user undo, permission granularity, conflict resolution.
