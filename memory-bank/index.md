# Memory Bank Index

This folder contains essential context for working on the Stamps Web App.

## Files to Read (in order)

### 1. opencode_rules.md
- 5 critical rules for development
- Tech stack: Django 6.0 + DRF, Flet frontend
- Coding standards and naming conventions

### 2. productContext.md
- Why the app exists
- Core goals and target users

### 3. techContext.md
- Architecture overview
- Development environment details

### 4. activeContext.md
- Current work in progress
- What to focus on today

### 5. progress.md
- Recent completed tasks
- Pending work items

### 6. datadesk-app-plan.md
- Agreed design for DataDesk, the internal DB-maintenance app (closed, not implemented)

### 7. datadesk-implementation-plan.md
- DataDesk build plan: D0 + S1–S22, dependencies, files and acceptance criteria per step
- **§7 at the end is the implementation log**: which steps are done, with date, files touched and
  decisions taken while implementing. Read it first when resuming work after a rebuild

### 8. ai-api-plan.md
- Improvement plan for `backend/ai_api/` — **A0 done 2026-11-25; next: A1 + A1b**
- Analysis of the current module, what Colnect, Delcampe, Iberphil and Fesofi actually
  offer, steps A0–A10 (A1b added for the opencode provider)
- Read it before touching the extraction pipeline; §3 has the open decisions, §4 the
  steps with their state, §7 the log of what is done and decided
- **A0's results are in `ai-sources-spike.md`** (raw evidence in
  `ai-sources-spike.json`): what each source answered, what it allows, and the
  Delcampe decision. Read the spike before A1

## How to Use

1. At session start → read index.md
2. Then read other files listed above
3. Check activeContext.md for current focus
4. Review progress.md for recent work
5. Update progress.md after completing tasks

## Important Notes

- Frontend tech: **Flet** (NOT NiceGUI - that's deprecated)
- Backend tech: Django 6.0 + DRF
- Always read this index first at the start of every session