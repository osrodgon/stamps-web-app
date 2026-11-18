# Active Context

## Current Task
- **DataDesk app design (DB maintenance)** — design closed, ready to implement. Staff-only internal Django app to replace slow one-record-at-a-time maintenance in the Flet frontend. Stack: server-rendered templates + HTMX + Alpine + Tabulator, mounted at `/datadesk/` in the existing backend container (no new service, no `/api/v1/` changes). Core ideas: dense issue workbench with "needs attention" queues, issue editor with the stamp grid beneath it, change-set buffer committed in one transaction, generic lookup CRUD with usage counts + merge, audit log with revert.
- **Name (2026-11-18)**: renamed **Curator → DataDesk**. "Curator" said nothing about the job; DataDesk states it — the app edits the database directly, not through the API. Everything (`backend/datadesk/`, `/datadesk/`, `DATADESK_ENABLED`, `DATADESK_TLS`, `DataDeskChange`, `datadesk_make_messages`, docs and mockup) uses the new name.
- **Decisions closed**: single user but **deployed on an external server** → own login page (username + password, Django session), `is_staff` gate on every view including JSON endpoints, login throttling, TLS + optional IP allowlist at the proxy; images out of scope (read-only indicator + `no image` queue); UI in English + Spanish via Django i18n in `backend/datadesk/locale/` (never touches `assets/locales/en.json` / `es.json`); CSV import/export out of scope (DB is current).
- **Unified workspace**: creating and editing a series are one screen (`mode=new | edit`) — same template, same grid, same issue→stamp inheritance greys, same fast-row toggle and change-set footer. Only top-bar actions, prefill, footer wording and post-commit behaviour differ. No separate "new issue" screen.
- Mockup with the `new / edit` switch: `memory-bank/mockups/datadesk_issue_workspace.html` (open in a browser; image generation is blocked by an invalid provider credential).
- **Schema review closed (2026-11-18)**: `Stamp` has no `country` / `year` / `stamp_type` / `print_type` / `printer` / `artist` / `paper_type` / `perforation` — those are series attributes and a stamp belongs to exactly one series, so **no columns are added**. Inheritance of those 8 is display-only (metadata strip, never per row); the editable grey/`⟲` inheritance covers only the 5 fields the stamp stores: `name`, `description`, `total_printed`, `market_value_mnh`, `market_value_used`. `face_value` and `name` are required, so `rows=N` must prefill the issue name.
- **Step-by-step implementation plan**: `memory-bank/datadesk-implementation-plan.md` — D0 + S1–S22 with dependency map, size, files and acceptance criteria per step. **In the repo**, so it survives container rebuilds; still needs to be started at S1.
- **Auth decisions closed (S3, 2026-11-18)**: `FileBasedCache` for login throttling (one user, no concurrency, shared by the 4 gunicorn workers without a table); no nginx locally and nginx+TLS in the deployment, so TLS settings live behind `DATADESK_TLS` with a single code path; global `LOGIN_URL` untouched (`login_url` in the mixin); IP allowlist only documented in the README, implemented after DataDesk itself is finished.
- **Write core closed (S12, 2026-11-18)**: two endpoints, one transaction each — `POST /datadesk/issues/create` (issue + nested stamps, all-or-nothing, no temp ids) and `POST /datadesk/apply` (existing rows, savepoint per row). Transport is plain Django views returning JSON, **not a REST API** and never under `/api/v1/`; DRF serializers are used for validation only. `delete` is rejected by `/apply` (409) and lives in S17 with the dependency preview. Lookups created inline use `get_or_create`; optional `expected_updated_at` per row; 500-change cap.
- **Review status (2026-11-18)**: closed — §2 schema (opción A, no `Stamp` columns), S3 auth, S7+S8 workbench/querysets, S12 write core (two endpoints), S14 client buffer, S19 lookup merge, S21 revert. Still to skim: S1, S2, S4, S5, S6, S9–S11, S13, S15–S18, S20, S22.
- Full plan: `memory-bank/datadesk-app-plan.md`. **Implementation started 2026-11-18 — S1 done** (app mounted at `/datadesk/` behind `DATADESK_ENABLED`, provisional `DashboardView`, 3 mount tests). Next step: **S2** (vendored HTMX/Alpine/Tabulator + `base.html`).

## Notes
- **Dataset actual (2026-11-18)**: 2.540 series y 9.555 sellos (≈3,8 de media), con dispersión amplia — hay series de 1 sello y la mayor tiene 24. El grid del workbench pagina server-side; el de sellos del workspace no pagina porque es una sola serie, y el caso a probar es la serie de 24 más un fixture de 100, para confirmar que no hay techos escondidos.
- Frontend uses Flet 0.84.0 (not NiceGUI)
- Locale files are user-managed — never modify en.json or es.json
- DatePicker timezone fix complete — JS in index.html writes to localStorage, Python reads via SharedPreferences
- Add issues to database (backend) — complete on branch `212-feature-stamps-manager-add-issues`
- IssueTable fully implemented and integrated into StampsManagerPage
- COLUMNS list in column_def.py is single source of truth for table columns
- All table components extend ft.Container (no UserControl in Flet 0.84.0)
- Service methods return raw requests.Response (AuthService pattern)
- Colors defined in colors.py with named constants (no raw hex in components)
- YearRangeSelector: custom Canvas-drawn two-thumb slider, debounced on_change,
  configurable track height, thumb radius, step, padding, and hover aura
- StampIssueService renamed to IssueService, added get_years() method
- IssueDetailCard: 4 modules (Header, Specs Grid, Valuation Bar, Stamp Table) + description/notes
- Stamps fetched async via IssueTableApp._fetch_stamps_for_row → row.set_stamps()
- 3 service files are Flet-free (base_service, auth_service, issue_service)
- 5 core files have zero Flet dependency (utils, logger, severity, urls, log_setup)
- Frontend unit testing plan saved to memory-bank/frontend-testing-plan.md
- **Inline Multi-Select Color Picker**: Completed and tested. Replaced nested color picker modal dialog with inline Material 3 searchable `ft.Dropdown` (`border=UNDERLINE`, `border_color=GREY_400`, `menu_style=BOTTOM_LEFT`, `menu_height=200`) and removable `ft.Chip` controls. All 651 tests passing.
- **Normal User Collections Plan**: Mockups generated and plan saved in `memory-bank/user-collections-plan.md` with images in `memory-bank/mockups/`.

## Session Log
- [Today] Stamp color selection UX: replaced nested modal dialog color picker in `StampForm` with an inline Material 3 multi-select dropdown and removable chips. Fixed overlay position (`BOTTOM_LEFT`, height `200`). Updated `stamp_form.py` and `test_stamp_form.py`. All 651 frontend tests passing.
- [Today] Normal User Collections Planning: Generated 3 UI mockup screens, designed hierarchical card structure (`Collection` → `Issues` → `Stamps`), designed catalog browser with "Select All in Series" feature, and saved full plan to `memory-bank/user-collections-plan.md` and mockups to `memory-bank/mockups/`.