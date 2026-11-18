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