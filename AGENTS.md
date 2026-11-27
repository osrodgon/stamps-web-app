# Agent Instructions

## ⚠️ CRITICAL: Session Start Protocol — READ BEFORE ANY OTHER ACTION
At the **very start of every session** (before any tool calls or responses), you **MUST**:
1. Read `/workspaces/stamps-web-app/memory-bank/index.md`
2. Follow the instructions in index.md for which memory-bank files to read
3. Update `activeContext.md` with your current task status when prompted

**Failure to do this will result in missing critical context and producing incorrect work.**

## Workspace
- Working directory: `/workspaces/stamps-web-app`
- Memory-bank location: `/workspaces/stamps-web-app/memory-bank/`

## Working style (agreed 2026-11-22)

- **Plan first, and announce the work before touching a file.** The user decides
  when programming starts; while a plan is being discussed, change nothing but
  the plan. Before every step, say **what** is going to be done and **how**
  (files, approach, what the step leaves working) and wait for the go-ahead when
  the user is in review mode.
- **New code follows the style that is already there**, file by file: the
  frontend's own patterns (see "Frontend conventions" in
  `memory-bank/user-collections-plan.md` §5) before any personal preference.
  When a new need has no precedent, copy the closest existing component or
  service instead of inventing a second way of doing it.
- **Tests are part of the step, not a follow-up.** A step is done when the unit
  tests it needs exist or are updated (services with mocked responses, components
  where Flet allows it) and the whole suite stays green.
- **A screen step is compared with its mockup before it is called done.** The
  mockups in `memory-bank/mockups/` are the design, not a suggestion: run the real
  page with stubbed services in the headless Chromium, take a screenshot and put it
  next to the mockup. The shape of the screen (header, filter card, rows, paginator)
  is what the step is judged on, not only its data. Tests cannot see a screen that
  renders nothing like it was drawn.
- **A mockup is drawn with the app's own controls and tokens.** `colors.py` and
  `components/constants.py` are the palette and the radii, and the shapes are the ones
  Flet will render: the house `TextField` (label above, underline, no box), the house
  dropdown, `PrimaryButton`/`DefaultButton`/`LinkButton`. A mockup that invents boxed
  inputs or a second button style cannot be built without a rewrite, and the comparison
  above then fails on the controls instead of the layout. The three first mockups
  (overview, series, detail) predate this rule and are kept as they are.

## Language and GitHub

- **GitHub issue titles are also branch names.** Issue creation lowercases the
  title and replaces spaces with dashes, so write the title naturally in English
  (spaces are fine, no need to pre-kebab-case it) but keep it short and free of
  punctuation a branch name cannot hold (`:` `,` `!` `/` quotes). Do not add the
  issue number or the type yourself — the tooling that creates the branch adds
  both (`212-feature-stamps-manager-add-issues`).
- **Use normal capitalisation in issue titles** — capital first word, and proper
  nouns as they are written (`DataDesk authentication staff gate and login
  throttling`, not `datadesk authentication staff gate and login throttling`).
  GitHub lowercases it for the branch; the issue list keeps the readable form.
- **Always state the type along with the suggested title** — `feature` (new
  capability the user can see), `chore` (scaffolding, tooling, refactors,
  styling, dependency bumps), `fix` (bug), `doc` (documentation only), `test`
  (tests only). It is not part of the title, but it is part of the answer:
  say which one and why in one line.
- **Every GitHub operation is in English** — issue titles and descriptions,
  commit messages, PR titles and descriptions, review comments.
- **GitHub operations are not authorized.** Never create, edit, close or comment
  on issues, PRs or releases, and never push. Suggesting issue titles,
  descriptions and commit messages is allowed and expected.
- **Code is exclusively in English** — identifiers, comments, docstrings, log
  messages, test names, template/UI strings keys (translations themselves may be
  in any language).