# Active Context

## Current Task
- Stamp color selection UX improvement: replaced modal dialog color picker with inline Material 3 multi-select color dropdown and input chips in `StampForm`.

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
- **Inline Multi-Select Color Picker**: Replaced nested color picker modal dialog with inline Material 3 searchable `ft.Dropdown` (`border=UNDERLINE`, `border_color=GREY_400`) and removable `ft.Chip` controls directly inside `StampForm`. Available dropdown options automatically filter out selected colors, and removing a chip restores the color to available options. All 651 tests passing.

## Session Log
- [Today] Stamp color selection UX: replaced nested modal dialog color picker in `StampForm` with an inline Material 3 multi-select dropdown and removable chips. Updated `stamp_form.py` and `test_stamp_form.py`. All 651 frontend tests passing.