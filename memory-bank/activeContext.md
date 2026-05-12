# Active Context

## Current Task
- **Task**: TBD - awaiting new task assignment
- **Priority**: medium
- **Status**: waiting

## Notes
- Frontend uses Flet 0.84.0 (not NiceGUI)
- IssueTable fully implemented and integrated into StampsManagerPage
- COLUMNS list in column_def.py is single source of truth for table columns
- All table components extend ft.Container (no UserControl in Flet 0.84.0)
- Service methods return raw requests.Response (AuthService pattern)
- Colors defined in colors.py with named constants (no raw hex in components)

## Session Log
- [Today] Analyzed IconButton for readability improvements
- [Today] Created IssueTable implementation plan
- [Today] Stored plan in memory-bank/progress.md
- [Today] Implemented StampIssueService, IssueRow, TableHeader, TablePagination, IssueTableApp
- [Today] Integrated IssueTable into StampsManagerPage
- [Today] Refactored to COLUMNS-driven architecture with column_def.py
- [Today] Fixed circular import, UserControl, Dropdown, layout issues