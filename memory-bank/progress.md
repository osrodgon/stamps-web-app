# Progress Tracker

## Open / Next

### DataDesk app — implementation (design closed, see `datadesk-app-plan.md`)

- [x] **S1 — Skeleton**: `backend/datadesk/` + `/datadesk/` mount behind `DATADESK_ENABLED`,
      provisional `DashboardView`, 3 mount tests. Next: S2 (vendored static + `base.html`)
- [x] S1 verified locally (2026-11-18): `DATADESK_ENABLED=True` added to `backend/.env`
      (dev only, not committed), backend up via `./stamps.sh dev start backend`,
      `GET http://localhost:8000/datadesk/` → 200 with the provisional page, and
      `pytest datadesk/tests -q` → 3 passed inside the dev container
- [x] **S2 — Vendored static + `base.html`** (2026-11-18): htmx 2.0.11, Alpine 3.17.5,
      Tabulator 6.7.1 pinned in `vendor/VERSIONS.md` with sha256 (a test enforces the
      hashes); `datadesk.css` with the mockup tokens; `base.html` (topbar, breadcrumbs,
      content/extra_css/extra_js blocks, `hx-headers` CSRF); `dashboard.html` extends it.
      Also: `STATIC_URL` → `/static/`, `STORAGES` uses plain storage when `DEBUG`,
      `sourceMappingURL` stripped from Tabulator. `collectstatic` clean, assets 200 in
      DEBUG, 1020 backend tests green. Next: S3 (login, logout, staff gate, throttling)
- [x] **S3 — Login, logout, staff gate, throttling** (2026-11-18): `DataDeskLoginView`
      (+ 429 with `Retry-After` after 5 failures in 5 min, sliding window),
      `DataDeskLogoutView` (POST-only), `DataDeskAccessMixin` (401/403 for JSON,
      redirect + `next` for browsers), `DataDeskGateMiddleware` scoped to `/datadesk/`
      and disabled with the flag. `CACHES` = `FileBasedCache` in `backend/.cache/`;
      sessions 14 days, `HttpOnly`, `SameSite=Lax`; `DATADESK_TLS` flips only cookie
      and proxy-header flags. 20 tests; 1040 backend tests green. Next: S4 (i18n en/es)
- [ ] Phase 1 — Scaffold: `backend/datadesk/`, `/datadesk/` mount, `DATADESK_ENABLED`,
      login/logout + staff gate + login throttling, vendorized HTMX/Alpine/Tabulator,
      en/es i18n catalog, `updated_at` + `DataDeskChange` migrations, `service.py` skeleton
- [ ] Phase 2 — Read-only Workbench + Issue Workspace (both modes on one template):
      grids, inheritance display, filters, "needs attention" queues, perf check on real data
- [ ] Phase 3 — Inline editing + single-row commit + audit; `mode=new` flow
      (last-issue defaults, `rows=N`, edifil auto-numbering, fast row mode,
      create-another loop); add/duplicate stamp row; inline lookup creation from a cell
- [ ] Phase 4 — Change set / review panel / transactional commit / clone issue / `Ctrl+Z`
- [ ] Phase 5 — Lookup CRUD + usage counts + merge; dashboard queues; activity log +
      revert; keyboard polish; tests
- [ ] Optional, documented only (plan §8): TOTP 2FA via `django-otp`

### Normal-user collections (plan only: `user-collections-plan.md`)

- [ ] Step 1 — `CollectionService` + `CollectionForm` dialog
- [ ] Step 2 — `CollectionsPage` grid + `CollectionCard`
- [ ] Step 3 — `CollectionDetailPage` + `CollectionIssueCard`
- [ ] Step 4 — `StampCatalogPicker` + "Select All in Series"
- [ ] Step 5 — unit tests (`test_collection_service.py`, `test_collection_form.py`, `test_stamp_catalog_picker.py`)

### Test debt (frontend)

- [ ] Tier 6 auth components (`login_card`, `signup_card`) — deferred: `ft.Container._values`
      issue, needs integration test
- [ ] `login_page`, `signup_page`, `collections_page` — deferred: `ft.View` `_values`
      descriptor issue

### Code quality

- [ ] Fix pre-existing LSP type errors in frontend code
- [ ] Add type hints to remaining untyped functions (rule #2)

### Known gaps

- [ ] JWT validation runs on first page load only; API-level checks TBD

---

## Completed

### Devcontainer — docker group guard in `stamps.sh` (2026-11-18)

- [x] `./stamps.sh` failed with "permission denied … /var/run/docker.sock" in a fresh
      container: `.devcontainer/setup.sh` runs `usermod -aG docker vscode` at postCreate, so
      `/etc/group` lists the user (`docker:x:994:vscode`) but the already-running session has
      no gid 994 and the socket is `root:docker 660`
- [x] Added a re-exec guard right after the `cd "$PROJECT_ROOT"` block in `stamps.sh`: when the
      socket is not writable and `getent group docker` lists the current user, it re-execs itself
      through `sg docker` once (`STAMPS_DOCKER_REEXEC` prevents loops, args re-quoted with
      `printf '%q '`)
- [x] Verified `bash -n`, usage output, and `dev start db` — no permission errors, container
      reported `Running`

### DataDesk — S1 done: app skeleton, flag and mount (2026-11-18)

- [x] `backend/datadesk/` with `apps.py` (`DataDeskConfig`), `urls.py`
      (`app_name = "datadesk"`), `views/dashboard.py` (`DashboardView`, provisional
      `TemplateView`) and `templates/datadesk/dashboard.html`
- [x] `settings.py`: `DATADESK_ENABLED` (env, default `False`), `DATADESK_URL = "datadesk/"`,
      `DATADESK_LOGIN_URL = "/datadesk/login/"`; `"datadesk"` added to `INSTALLED_APPS`
- [x] `_backend/urls.py`: mounted **after** the list and only `if settings.DATADESK_ENABLED`,
      using `django.conf.settings` (not the plain module) so `override_settings` can drive it
- [x] `backend/.env.example`: documented `DATADESK_ENABLED=False`
- [x] `datadesk/tests/test_mount.py`: flag off → 404, flag on → 200, `reverse("datadesk:dashboard")`
      is `/datadesk/`; the URLconf is reloaded with `clear_url_caches()` + `importlib.reload`
      because it is imported once per process
- [x] Verified: `manage.py check` clean, `spectacular` schema has 0 `datadesk` mentions,
      1011 backend tests pass (1008 existing + 3 new)

### DataDesk — schema review + step plan (2026-11-18)

- [x] Verified `Stamp` carries no series-level columns: model, `StampRequestSerializer`,
      `StampForm` and `ai_api` all agree (11 stamp fields, no country/artist/printer)
- [x] Closed the decision: **no schema change** (option A). Country, artist and printer are
      series attributes shared by every stamp of the series, and no exception exists in the data
- [x] Inheritance redefined: display-only for the 8 series fields (metadata strip), editable
      grey/`⟲` only for the 5 fields a stamp stores (`name`, `description`, `total_printed`,
      `market_value_mnh`, `market_value_used`)
- [x] Corrected design §3.2 and §5, and the mockup: `1 override` removed from the `mode=new`
      footer, overrides moved to fields that can actually differ (total printed, used)
- [x] Implementation plan written step by step (D0 + S1–S22, dependency map, per-step
      acceptance criteria) at `memory-bank/datadesk-implementation-plan.md` (moved into the repo
      on 2026-11-18 so a devcontainer rebuild can't lose it)
- [x] S3 auth review: `FileBasedCache` for throttling (shared by the 4 gunicorn workers, no
      table), `DATADESK_TLS` toggles cookie/header flags only so local (no nginx) and deployed
      (nginx + TLS) run the same code, global `LOGIN_URL` untouched, IP allowlist deferred to
      the README after implementation
- [x] S7+S8 review: real volume is **2.540 issues / 9.555 stamps**, heavily skewed (series of 1
      to more than 10); one query for the grid via `select_related` + `Count`, attention filters
      and the dashboard report share one function, flat endpoint params with Tabulator's
      `last_page`/`last_row` shape, decimals sent as strings, no speculative indexes (seq scan is
      milliseconds at this size)
- [x] S12 write-core review: two endpoints with one transaction each — `/datadesk/issues/create`
      (issue + nested stamps, all-or-nothing, no temp ids) and `/datadesk/apply` (existing rows,
      savepoint per row); plain Django views returning JSON, not a REST API and nothing under
      `/api/v1/`; `delete` excluded from `/apply` (409) and kept behind S17's dependency preview
- [x] S19 merge review: `keep_name_from: "a"|"b"` selector (move refs → delete the loser to free its
      `unique` name → rename the survivor); `.update()` doesn't fire `auto_now`, so merges set
      `updated_at` explicitly or S12's conflict check goes blind; colors resolved through the M2M
      table with `ignore_conflicts` instead of `.set()`/`.add()`; rename collision → 409 offering
      merge; 8 lookups in scope, not 9 (`ConditionType` stays in admin)
- [x] S21 revert review: commit-level revert (all or nothing), model order lookups → Issue → Stamp,
      deletes recreated with their original ids, merge commits marked non-revertible, `reverted_at`
      + `reverts_commit_id` added to `DataDeskChange`; the UI states that reverted deletes do **not**
      restore `CollectionItem` rows removed by the cascade
- [x] S14 buffer review: state per object (not per cell) with `patch`/`base`/`expected_updated_at`,
      diff against base so no-op edits vanish, undo as an operation log, colours carry names for the
      review panel, `localStorage` recovery **only in `mode=edit`** (no drafts for a new series:
      finish it now or start again), deletes excluded from the buffer and therefore from undo
- [x] **Renamed Curator → DataDesk** (2026-11-18): "Curator" described conservation, not the job;
      the app edits the DB directly instead of going through `/api/v1/`. Migrated the two docs,
      `index.md`, `activeContext.md`, `progress.md` and the mockup filename; nothing implemented
      yet, so no code to rename

### DataDesk App — DB Maintenance Design (2026-11-17)

- [x] Surveyed schema: Issue→Stamp cascade, 9 unique-name lookup tables, no `updated_at` timestamps
- [x] Evaluated stack options (internal Django+HTMX vs SPA vs Flet desktop vs TUI vs Django Admin)
- [x] Wrote design doc `memory-bank/datadesk-app-plan.md`: workbench, issue workspace, lookup merge,
      audit/undo, change-set commits, 5 phases
- [x] Decisions closed: single user, **external server** → own login page + staff gate + throttling +
      TLS/allowlist (revised from "no login screen"); images out of scope; EN+ES via Django i18n;
      CSV import/export out of scope (DB is current)
- [x] Merged the editor and new-issue specs into one "Issue workspace" with a `mode=new | edit`
      differences table (create and edit share template, inheritance, fast row, footer)
- [x] HTML mockup `memory-bank/mockups/datadesk_issue_workspace.html` with a working new/edit switch
      (image generation blocked: invalid provider credential)
- [x] Documented optional TOTP 2FA design in plan §8 (django-otp, CLI enrolment, two-step login,
      `is_verified()` in middleware, recovery codes) — not built

### Stamp Edit Feature & Material 3 UI Improvements (2025-06-15)

- [x] Added `update_stamp()` to IssueService (PUT /stamps/{id}/)
- [x] StampForm edit mode: `stamp_data` param, pre-populates all fields + colors, `_on_save`
      dispatches to create/update
- [x] Callback chain: StampCard passes `stamp_dict` → wrapped with `issue_id` in IssueDetailCard →
      StampsManagerPage opens StampForm
- [x] Implemented `_handle_edit_stamp` in StampsManagerPage
- [x] Added 4 locale keys: `edit_title`, `update_stamp`, `update_success`, `update_failed`
- [x] Refined `issue_header_section.py` and `issue_specs_grid.py`: clean `UNDERLINE` borders
      (`border_color=GREY_400`), `prefix="€ "` for valuation fields, constrained title/badge widths
- [x] 653 tests total passing

### Inline Multi-Select Color Picker

- [x] Replaced the nested color-picker modal in `StampForm` with an inline Material 3 searchable
      `ft.Dropdown` (`border=UNDERLINE`, `border_color=GREY_400`, `menu_style=BOTTOM_LEFT`,
      `menu_height=200`) plus removable `ft.Chip` controls
- [x] Updated `stamp_form.py` and `test_stamp_form.py`; 651 frontend tests passing

### IssueForm Visual Alignment with IssueDetailCard (2025-06-12)

- [x] `hide_action_icons: bool = False` on IssueHeaderSection — guards icon visibility in
      enter/exit_edit_mode
- [x] Rebuilt IssueForm on IssueHeaderSection + IssueSpecsGrid in permanent edit mode
- [x] Cancel/Create kept at the bottom of the dialog
- [x] Removed hand-rolled builders (`_build_name_section`, `_build_specs_grid`, `_paired_cell`, …)
- [x] `_on_create` reads from IssueHeaderSection properties + IssueSpecsGrid edit_state
      (same pattern as `_handle_save_edit`)
- [x] 24 tests updated; 624 total passing

### IssueDetailCard Read/Edit Toggle (2025-05-30)

- [x] Added `update_issue()` to IssueService (PUT issues/{id}/)
- [x] Local edit-mode toggle in IssueDetailCard for the `stamp_type` field
- [x] Edit icon swaps to save/cancel; `stamp_type` cell replaced with `AutoCompleteField`
- [x] Passes IssueService through IssueRow → IssueTableApp → IssueDetailCard
- [x] On save: resolves stamp_type (select or create ref), calls PUT, updates local data,
      fires `on_edit_issue`
- [x] `_handle_edit_issue` in StampsManagerPage upgraded from stub to `self._table.load(reset_page=True)`
- [x] 614 tests passing

### DatePicker Timezone Fix (2025-05-30)

- [x] `index.html` JS writes `Intl.DateTimeFormat().resolvedOptions().timeZone` to `localStorage`
      (`flutter.stamps_app._timezone`, `JSON.stringify()`)
- [x] `init_client_timezone()` reads it via `SharedPreferences`
- [x] `get_local_today()` returns today in the client timezone via `zoneinfo.ZoneInfo`
- [x] `to_local_date()` converts Flutter's UTC-normalised datetime back to client local date
- [x] `DEFAULT_TIMEZONE` env var in `settings.py`; wired `init_client_timezone()` into `main.py`
- [x] Replaced `datetime.date.today()` with `get_local_today()` in `date_picker.py` and `issue_form.py`
- [x] 12 new tests; 597 total passing

### Client-Side JWT Token Validation (2025-05-30)

- [x] `validate_jwt_token()` in `core/utils.py` — decodes without signature verification, checks
      `exp` against UTC
- [x] Wired into `main.py` root route (redirect only when the stored JWT is still valid)
- [x] Added `PyJWT==2.10.1` to `requirements.base.txt`
- [x] Cleaned up unused imports in `login_view.py`

### IssueService + IssueForm Refactoring (2025-05-28)

- [x] Extracted `_fetch_ref` / `_create_ref` helpers — 14 boilerplate methods → 1-liners
- [x] Split `_build_form()` into `_build_name_section`, `_build_date_row`, `_build_specs_grid`,
      `_build_notes_section`, `_build_actions`, `_assemble_card`
- [x] Renamed `_mnh_field` → `_mint_field`, `_date_picker_icon` → `_date_picker`
- [x] Removed dead `_on_field_change` handler and `_field_cell` static method
- [x] Replaced `_make_dropdown` setattr pattern with `_build_dropdown` + explicit assignment
- [x] Moved DatePicker overlay append from `_build_form()` to `show()`
- [x] Added `super().__init__()`; documented `_on_success` as sync-only; fixed stale docstrings
- [x] 585 tests passing

### Client Timezone Detection (2025-05-26)

- [x] Timezone query param `?tz=` from `index.html`; `init_client_timezone(page)` + `get_local_today()`
- [x] `DEFAULT_TIMEZONE` env var; called on startup in `main.py`
- [x] Replaced naive `datetime` calls in `date_picker.py` and `issue_form.py`
- [x] 6 new tests; 566 total passing

### Add Issue Form (2025-05-24)

- [x] Added URL definitions for `countries`, `artists`, `paper_types`, `printers`
- [x] 7 service methods: `create_issue`, `get_countries`, `get_artists`, `get_stamp_types`,
      `get_paper_types`, `get_print_types`, `get_printers`
- [x] `IssueForm` dialog with specs grid (3 cols), date picker + "Today", reference dropdowns,
      multiline description/notes, Create/Cancel
- [x] Wired `_handle_add_issue` → opens IssueForm → reloads table on success
- [x] 44 new tests; 535 total passing
- [x] Flet 0.84.0 quirks noted: `ft.Dropdown` sets `on_change` after construction;
      `ft.TextButton` uses `content` not `text`

### DatePicker Styling & Future Dates (2025-05-24)

- [x] `year_shape` added to DatePickerTheme via post-construction assignment (skipped by `__init__`)
- [x] `shape` added for dialog corner radius (8px)
- [x] `DatePickerField.last_date` default changed from `today` to `today + 365 days`
- [x] 2 new tests; 560 total passing

### Add Issues to Database (backend) — Complete

- [x] Backend endpoint to persist issues from the frontend IssueForm
- [x] Wired working-tree changes on branch `212-feature-stamps-manager-add-issues`
- [x] Fixed duplicate issue creation bug in `issue_form.py` (duplicated `_on_create` → two API calls)

### Add Stamps — Complete

- [x] Backend endpoint to add stamps to an issue
- [x] `StampForm` dialog (`components/form/dialogs/stamp_form.py`) — create + edit modes
- [x] Wired: `IssueStampGrid` add card → `IssueDetailCard._handle_add_stamp` →
      `StampsManagerPage._handle_add_stamp` → `StampForm(issue_id=…)`, refresh on success

### Stamp Deletion (2025-05-22)

- [x] `delete_stamp()` in IssueService
- [x] Confirmation dialog in `StampCard._handle_delete` + callback wrapping in IssueDetailCard
- [x] Wired `on_delete_stamp(stamp_id, issue_id)` through → StampsManagerPage with live API call,
      notifications and stamps refresh
- [x] Delete locale keys supplied by the user (not managed by automation)
- [x] All 488 tests passing

### Issue Deletion (2025-05-22)

- [x] Confirmation dialog in `IssueDetailCard._handle_delete_issue` (issue name + cascade warning)
- [x] Live API call in `StampsManagerPage._handle_delete_issue` with notifications and table reload
- [x] 3 new tests (dialog shown, confirm fires callback, cancel does not)
- [x] 491 tests passing

### Database Backup/Restore Commands (2025-05-22)

- [x] `stamps_db_backup.py` — interactive/non-interactive with `--mode` (system/stamps/full)
- [x] `stamps_db_restore.py` — interactive restore with confirmation prompt
- [x] `backend/backups/` added to `.gitignore`
- [x] 1008 backend + 491 frontend tests passing

### Frontend Unit Testing (2025-05-22)

- [x] `frontend/tests/` with `__init__.py`, `conftest.py`; isolated `frontend/pytest.ini`
- [x] Pure functions — `core/utils.py` (29 tests)
- [x] Service layer (41): `test_base_service.py` 14, `test_auth_service.py` 9,
      `test_issue_service.py` 18
- [x] Translations + formatters (88): `test_translations.py` 33, `test_column_def.py` 55
- [x] Colors + BaseUI (61): `test_colors.py` 43, `test_base_ui.py` 20
- [x] log_setup (17)
- [x] Buttons (30): Alert, Default, Primary, Text, Link, Icon — 5 each
- [x] Form components (34): `FieldStyle` 7, `DEFAULT` 3, `APP_HEADER` 9, `TextField` 15
- [x] Layout (14): HorizontalLine 7, VerticalLine 7
- [x] Components (84): app_header 13, year_range_selector 14, table_pagination 18,
      table_header 10, issue_row 10, issue_table_app 19
- [x] Table detail card (35), page templates (16), StampsManagerPage statics + stubs (15),
      `main.py` (24)
- [x] Total: 618 tests passing

### IssueDetailCard Read/Edit + Add-Stamp Button (2025-05-21)

- [x] `on_add_stamp` callback through IssueDetailCard → IssueRow → IssueTableApp
- [x] Add-stamp card as last grid item: centered 48px `IconButton`, hover GREY_700→GREEN_700,
      tooltip from locale
- [x] Fixed `ft.Card.on_click` → `ft.Container.on_click` (Card lacks `on_click` in Flet 0.84.0)
- [x] Locale key `stamps.add` → `stamps.add_tooltip`
- [x] Add-issue `IconButton` in `AppHeader.right_area`; async `_handle_add_issue` stub
- [x] Docstrings on handlers, callbacks and `show_stamp_detail_dialog()`
- [x] 398 tests passing

### IssueDetailCard Implementation (2025-05-14)

- [x] Component with 4 modules: header (32px bold + emission date), technical spec matrix
      (ResponsiveRow 4→2, GREY_50), description & notes, valuation summary
      (mint GREEN_700, used BLUE_700, total printed) + stamp inventory DataTable
- [x] Async stamp fetch in `IssueTableApp._on_expand` → `_fetch_stamps_for_row`
- [x] `set_stamps()` on IssueRow; loading/empty states
- [x] 7 translation keys: `year`, `mint`, `used`, `market_value_mnh`,
      `technical_specifications`, `valuation`, `image`
- [x] `_kv_cell` sets `container.col` as attribute, not kwarg

### YearRangeSelector (2025-05-12)

- [x] Canvas-drawn two-thumb slider; configurable `track_height`, `thumb_radius`, `step`,
      `padding`; hover aura, drag focus, tap-to-move
- [x] Async callback support in `_notify_change`; `set_range()`; `sel_min_year` / `sel_max_year`
- [x] `get_years()` on IssueService (GET /years/)
- [x] Integrated into StampsManagerPage header (round to nearest 5), 300ms debounced filter
- [x] `SLIDER_INACTIVE` color constant; locale-aware pagination range text

### Memory Bank & Documentation (2025-05-11)

- [x] Created `memory-bank/index.md`, `activeContext.md`, `progress.md`, `productContext.md`,
      `techContext.md`, `opencode_rules.md` (Flet, not NiceGUI)
- [x] Docstrings added to 11 frontend files and all 20 color constants in `colors.py`
      (type hints + `__all__`); fixed wrong `PrimaryButton` docstring in `alert_button.py`
- [x] Analyzed `main.py` for unit testing; reviewed backend and legacy frontend test structure
- [x] Documented test patterns in `frontend-testing-patterns.md`

---

## Notes

- Frontend framework: **Flet 0.84.0** (not NiceGUI); backend Django 6.0 + DRF
- Testing: pytest, `pytest-asyncio`, `pytest-mock`; frontend config is isolated in `frontend/pytest.ini`
- Locale files (`assets/locales/en.json`, `es.json`) are user-managed — never edit them
- Stamp create/edit lives in `StampForm`; `StampsManagerPage` only wires callbacks
- Historic design docs: `memory-bank/archive/issue-table-plan.md` (implemented),
  logger MRO reference moved to `techContext.md`