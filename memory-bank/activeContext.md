# Active Context

## Current Task
- Stamp edit feature: reuse StampForm dialog for editing stamps

## Notes
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
- **StampForm edit mode**: accepts `stamp_data` param, pre-populates all fields + colors, dispatches to `update_stamp()` / `create_stamp()`
- Edit callback chain: StampCard passes `stamp_dict` → IssueStampGrid → IssueDetailCard wraps with `issue_id` → IssueRow → IssueTableApp → StampsManagerPage opens StampForm
- 653 tests total (9 new: 4 edit-mode + 4 update_stamp service + 1 handler)

## Session Log
- [Today] Stamp edit feature: added `update_stamp()` to IssueService, modified StampForm for edit mode (stamp_data param, pre-population of all fields + colors, _on_save dispatches to create/update), changed callback chain to pass stamp dict through 6 layers, implemented _handle_edit_stamp in StampsManagerPage, added 4 locale keys (edit_title, update_stamp, update_success, update_failed) to en/es, 8 new tests — 653 total passing