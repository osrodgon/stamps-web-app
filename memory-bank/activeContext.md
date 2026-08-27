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
- **Form UI Styling Alignment**: updated `issue_header_section.py`, `issue_specs_grid.py`, and `stamp_form.py` to use consistent `ft.InputBorder.UNDERLINE` with `border_color=GREY_400`. In `StampForm`, valuation fields (`_mnh_field` and `_used_field`) use standard regular font (`Roboto`, `GREY_700`) and non-italic `prefix_style` for `€`. 653 tests passing.

## Session Log
- [Today] Stamp edit feature & Form UI adjustments: updated `StampForm` valuation inputs (`_mnh_field` & `_used_field`) to regular `Roboto` text in `GREY_700` and non-italic `prefix_style` for the euro symbol. All 653 frontend tests passing.