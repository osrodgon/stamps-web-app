# Active Context

## Current Task
- **AI API A0, A1, A1b, A2 and A6 done (2026-11-25/26)**: the source probe ran
  (report in `memory-bank/ai-sources-spike.md`), the extraction contract is
  evidence-based (`SourceObservation` plus `sources` / `observations` / `valuation`
  / `gaps` / `description_source`, with the old `market_value_*` always null),
  **opencode is the only LLM provider**, **every outbound call goes through one HTTP
  client** (allowlist, retries, per-host limit, cache: a 29-stamp series went from
  7.0 s to 0.9 s) and **the series is identified in the Fesofi catalogue** — by
  partial name, with the facts read from its attributes and a scored matcher that
  reports a tie as a gap. **A7 and A7b are done too**: the valuation is a trimmed
  mean over observations (`n ≥ 3` per condition, euros only), and the condition comes
  from the listing page — TodoColeccion yes, eBay blocks the server with a 403.
  `navidad 1986` and `castillos 2007` now return estimates. **A8 is done too**: a
  request has a budget and answers `partial`, and `ai_prices_backfill` stores
  observations without duplicating them. **A9 is done too**: the model can no longer
  write a code, a date or a number the sources do not carry — `check_support()` drops
  it and reports it. **A10 is done too, so the AI API plan is closed**: the README
  describes the module as it is, `sources` really reports what each source answered,
  the dead registry and the Colnect leftovers are gone, and the schema carries
  `partial` and `subject_code`. Details in Notes below.
- **Proveedor de IA (2026-11-25)**: la API usará **opencode** como único proveedor y
  **Gemini y Groq se retiran del código** (paso **A1b**, anunciado en el plan con la
  superficie exacta a borrar). Se llama por la **API de inferencia del Console**
  (`https://opencode.ai/inference/...`, `Bearer oc_sk_…`): **no se instala opencode
  en el backend ni se usa `opencode serve`**. Ojo: los modelos gratuitos del Console
  sólo funcionan dentro de opencode (403 desde fuera), así que el backend usa
  modelos de pago. **El motor se decide más adelante** y entra por configuración en
  la petición (`OPENCODE_MODEL`), no como constante. **Serper se queda de momento**
  (`SERPER_*` + `SearchService` intactos, A2 le pone el timeout que le falta) y se
  quitará en su propio paso si la búsqueda de precios no lo necesita.
- **DataDesk app design (DB maintenance)** — design closed, ready to implement. Staff-only internal Django app to replace slow one-record-at-a-time maintenance in the Flet frontend. Stack: server-rendered templates + HTMX + Alpine + Tabulator, mounted at `/datadesk/` in the existing backend container (no new service, no `/api/v1/` changes). Core ideas: dense issue workbench with "needs attention" queues, issue editor with the stamp grid beneath it, change-set buffer committed in one transaction, generic lookup CRUD with usage counts + merge, audit log with revert.
- **Name (2026-11-18)**: renamed **Curator → DataDesk**. "Curator" said nothing about the job; DataDesk states it — the app edits the database directly, not through the API. Everything (`backend/datadesk/`, `/datadesk/`, `DATADESK_ENABLED`, `DATADESK_TLS`, `DataDeskChange`, `datadesk_make_messages`, docs and mockup) uses the new name.
- **Decisions closed**: single user but **deployed on an external server** → own login page (username + password, Django session), `is_staff` gate on every view including JSON endpoints, login throttling, TLS + optional IP allowlist at the proxy; images **displayed** read-only from the frontend's `<year>/<code>.webp` tree (upload/import still out of scope); UI in English + Spanish via Django i18n in `backend/datadesk/locale/` (never touches `assets/locales/en.json` / `es.json`); CSV import/export out of scope (DB is current).
- **Unified workspace**: creating and editing a series are one screen (`mode=new | edit`) — same template, same grid, same fast-row toggle and change-set footer (no inheritance greys: dropped 2026-11-18). Only top-bar actions, prefill, footer wording and post-commit behaviour differ. No separate "new issue" screen.
- Mockup with the `new / edit` switch: `memory-bank/mockups/datadesk_issue_workspace.html` (open in a browser; image generation is blocked by an invalid provider credential). Its grey/`⟲` inheritance is **superseded** — that concept was removed on 2026-11-18.
- **Schema review closed (2026-11-18)**: `Stamp` has no `country` / `year` / `stamp_type` / `print_type` / `printer` / `artist` / `paper_type` / `perforation` — those are series attributes and a stamp belongs to exactly one series, so **no columns are added**. Inheritance of those 8 is display-only (metadata strip, never per row); **nothing is inherited** (2026-11-18, supersedes the grey/`↺` design): series values describe the set — print run, value of the complete series (less than the sum of its stamps) — and stamp values describe the stamp, so an equal number is a coincidence. `name` included. `face_value` and `name` are required, so `rows=N` prefills the issue name as a default, not as an inheritance.
- **Step-by-step implementation plan**: `memory-bank/datadesk-implementation-plan.md` — D0 + S1–S22 with dependency map, size, files and acceptance criteria per step. **In the repo**, so it survives container rebuilds. **D0 + S1–S22 done (2026-11-19).** A first review with the app running opened a second wave, **S23–S27** (its own table in the plan): the refused cell's ring hidden by the next row (S23, XS), type scale and rhythm (S24, M), deleting a stamp with a preview (S25, M), a `New row` button on the reference tables (S26, S), and the S27 that now covers two things at once: moving between series and deleting one (M). S23–S27 are done, so the second wave is closed too. A third wave is a single planned step, **S28** (visual polish, M, explicitly not urgent), and a fourth, **S29–S32** (2026-11-20), comes from using the app with real data; **S29, S29b and S30 are done**, and a fifth, **S33** (add a stamp to an existing series), came from doing the work and is done too. Still open: **S31** (backups screen) and **S32** (restore), and colours in `mode=edit` (needs M2M in the change set).
- **S29 done (2026-11-21)**: the series screen has a **preview pane on the right of the grid**, tied to the selected row — no hover, no click on the picture — with the stamp picture at 258px and the description underneath, editable and inside the change set. Selection did not exist in this screen (`j`/`k` were the workbench's), so S29 adds `selectableRows: 1` and `j`/`k`. `Stamp.description` is a **hidden** column (`visible: false`, `patch: "description"`), which puts it in `patchOf`, the review labels ("Stamp description"), undo and the `localStorage` draft with no new machinery, and keeps what was typed when the selection moves. The pane and the undo write with `quietCell`, so a keystroke is not an undo step and undo no longer pushes itself back; the base comes from `previewStart` (value on focus) because `cell.getOldValue()` is the page-load value. Both modes, pane stacks under the grid below 1100px, S/M/L selector deliberately out. **Two older bugs found while checking**: `mode=new` painted nothing (`setData` in the same tick as Tabulator's build → `verticalFillMode` crash; now waits for `tableBuilt`, reproduced with `HEAD`'s JS), and `?rows=N` is never read by the view. 493 datadesk / 1509 backend; checked in Chromium at 1366 and 1024.
- **S30 done (2026-11-21)**: the usage number of a reference row is a link to the workbench with that filter, above zero only, and the list shows one chip per active filter with its own clear link plus a clear-all. Five filters added — `printer`, `artist`, `paper_type`, `print_type` as series columns and `color` as `Exists` (a join would multiply rows and inflate `Count("stamps")`, which a test with a two-colour stamp pins; this corrects the plan's `stamps__colors` + `distinct`). The link counts **series** (`Count("stamps__issue", distinct=True)` in the same query) while the cell title still says the stamps when they differ, and a year links with `year_min` + `year_max` because `Year.pk` is not the year. The chips are painted in the script from the form: the page reloads only the grid, so server-rendered chips went stale as soon as a filter was set from the bar — seen in the browser, not in a test. `filters_from()` is now one function shared by the page and the grid endpoint (the endpoint had its own copy). 16 tests; 509 datadesk / 1525 backend.
- **S30b done (2026-11-21)**: the same day it was used, S30 broke the workbench layout — five more selects made the filter bar four rows tall (193px) while the grid kept `height: calc(100vh - 300px)`, so at 1440×900 the pagination footer landed at y=899, outside the window. The card is now a column as tall as the window and the grid takes what the filters leave (`flex: 1` + `height: "100%"`); the empty chips strip stopped taking 17px because `[hidden]` now beats `display: flex`; and the five new selects moved behind a "More filters" `<details>` that opens itself when one of them filters. Also: "the filters don't work" was the previous `workbench.js` in the browser — selects come from the template, filtering from the script — so DataDesk's assets now carry `?v=` with the newest asset's mtime (`datadesk/context.py`). 8 tests; 517 datadesk / 1533 backend; checked at 1440×900, 1366×768 and 1366×600.
- **S30c done (2026-11-21)**: CI found what `.env` hid — `lookup_page()` reversed `datadesk:issues` and that namespace only exists with the app mounted, so the fourteen tests that call the service directly failed with `NoReverseMatch` while locally `DATADESK_ENABLED=True` kept them green. The service returns `filter: {...}` now and `views/lookups.py` builds the URL (`with_filter_url()`); `pytest.ini` pins `DATADESK_ENABLED=False`, so the suite runs CI-shaped and `mounted` turns it on where needed. 518 datadesk / 1534 backend (flag off).
- **S28 done (2026-11-21)**: the polished mockup is the app now — Inter 4.001 self-hosted (48 KB latin variable, pinged with its real version and sha256), 34px controls with a soft focus ring, 120ms motion with `prefers-reduced-motion`, a borderless card with two shadow levels, a **light grid header** with a 2px left bar on the selected row, a 4px rhythm, 38px rows and tabular numbers. Two findings: the `—` of an empty cell cannot be CSS (Tabulator writes `&nbsp;`, so `:empty` never matches) and needed a formatter; and the headers truncated because columns are shared by `grow` with no floor, so the workbench and the stamp grid got real minimum widths and "Total printed" became "Printed" on the header only (a new `label` key keeps the review panel precise). 6 pins in `test_layout`; 524 datadesk / 1540 backend; screenshots of every screen at 1440×900 and 1366×768.
- **S28b done (2026-11-21)**: five fixes from using the new skin — the workbench date column was being shrunk by `fitColumns` because the workbench's `buildColumn` never copied `width` (now a fixed 112 and the builder understands it); the shortcuts line had no margin; Tabulator's root `#888` showed as a grey band under a series with one stamp (both grids set a surface background); the series card had square corners because its strip paints over the radius (the strip and the commit bar are rounded rather than clipping the card, which cut 12px off the colour editor); and the market values now say `1.20 €`, with `(€)` in the strip fields and the review labels. 526 datadesk / 1542 backend.
- **S33 done (2026-11-22, the gap that mattered)**: `+ Stamp` in the `mode=edit` grid head adds a stamp to the open series as a **draft row** — `new-<n>`, name prefilled with the series name, nothing sent until the commit. `entryFor()` marks it `op: "create"` from `newRows` and `sync()` writes the row whole (the eight fields plus `issue`) instead of diffing against a `base` it does not have; the review shows it with a server-sent `NEW` chip and every non-empty field, and it counts as **one** change. `Ctrl+Z` removes the row and restores one removed with its ×, which never asks the server (`delete` and `add` are opposite history steps, and mixing them up made undo re-delete). After the commit `adoptDraft()` replaces the id with the real one plus `updated_at` and the two per-row URLs, which the server now sends as a **shape** (`url_template()`, `%(id)s`), because a row without an id cannot have them rendered. A clean commit **reloads the series page** instead of returning to the workbench — reloading is what turns the draft into a stored row — and `?focus=` stays only as a manual deep link. A partial commit reconciles in place, so retrying cannot create the same stamp twice; a row nobody typed in is dropped on commit; a `create` is never kept in `localStorage` (no `base`). 16 tests (14 in `test_workspace_add_stamp.py`, 2 CSS pins); 545 datadesk / 1561 backend; Chromium: add → review → partial commit (one created, one refused) → edit the created one → fix and commit the refused one → reload with both rows stored.
- **S29b done (2026-11-22)**: stamp pictures sit on `--dd-plate` (#cfd6df after comparing #d7dde5 and #c2cad4 on screen), one token for the S29 pane and the 26px thumbnail, with a hairline border in the pane and a hairline `box-shadow` on the thumbnail (a border at 26px costs two pixels of stamp). The files are RGBA with the piece cut out, so the plate was ours to choose — and white was hiding the dentado of every stamp with a white frame. 3 pins in `test_layout`; 529 datadesk; checked with the 1976 series in Chromium, pane and 26px thumbnail.
- **S34 done (2026-11-22, from the production screenshots and from using it)**: the money, the print run, the dates and the review panel are written the way the active language writes them. `datadesk/texts.py` gained `separators()` (Spanish groups with a **dot**, not Django's no-break space: in a 13px cell it does not read as a separator) and `date_text()` (`1 dic 1853` / `Dec 1, 1853` — **month by name**, which supersedes the first design of `01/12/1853` / `12/01/1853` because that still made the reader work out which number is the month). Columns declare `"format": "money" | "number" | "date"` (replacing S28's `money: True`); money and the print run are grouped in the script from the cell value so an edit paints at once, while the read-only date travels written per row (`date_text`). Money columns went to `min: 120` (`999.999,99 €`), the date to 128. `config.numberFields` makes the review format too (`37.500,00 → 36.000.000`). Not touched on purpose: the strip's inputs keep the stored value (`36000000`), because a number input cannot hold separators and guessing them on read is how you write 219 instead of 2,19. **What is left, as S34b**: the workbench footer still says 2600 instead of 2,540, its pager is English in Spanish, and the entity is *issues* in the menu and the counter. 13 tests; 581 datadesk / 1597 backend; Chromium in both languages with real data.
- **S35 done (2026-11-22, the gap since S18, closed)**: a stamp's colours are edited in the **preview pane** — chips with their tone and an ×, plus a typed field with a datalist and `+ Create "X"` (the S18 pattern) — in both modes. The writer already accepted `colors` on an update and S21's revert already restored them; what changed is the screen and the language the row speaks: `serialize_stamp()` sends colour **ids** (ordered by name) instead of `{name, tone}` and the palette ships in `mode=edit` too (a conscious exception to S18: a multi-value editor needs its options up front), so the cell, the patch, the review, undo and the draft all say the same thing. The column gets `patch: "colors"` in `edit` only and never an editor; the pane field is deliberately **not** a `data-lookup`, because `unresolvedLookup()` blocks the commit on a typed name and a colour here is created, not refused. `flushTypedColour()` takes a colour typed but not confirmed before a commit, `same()` compares colour lists as sets, and an empty cell now paints `—` (1.648 stamps have no colour on prod). The toolbar's `New colour` panel stays, by decision, sharing the palette through `addToPalette()`. 13 new tests — the first `/apply` update with colours, `[]` to clear them and the revert of a colour change (S21's `_restore` was untested for M2M) — 558 datadesk / 1574 backend, and Chromium with the 1976 series: add, remove, undo both, review with names, commit and reload, a colourless stamp, `+ Create` end to end and `mode=new` with both doors live. Plan §3 séptima tanda, §4 S35, §7.
- **S36 done (2026-11-22, reported from using the list)**: two series of the same date did not always come out in the same order, because the default order (year, date, **name**) left ties — 419 repeated dates in the real data, the biggest being 29-12-1998 with 15 series called «España 2000» — and with OFFSET paging a tie can repeat a row on one page and skip another. The tiebreak is now the series' **catalogue code**: `first_code` = `Min` of its stamps' **Fesofi** code with **Edifil** as the per-stamp fallback (Edifil is missing on 2,761 of 9,557 stamps and 696 series; Fesofi on 61 and 6), compared by **length then text** so «3649» beats «1998042», and the order ends in the `pk`, which makes it total. Every column sort ends in the same tiebreak, and `issue_positions()` got the annotation so the workspace arrows and the `4 / 2,541` counter walk it too. Cost: grid page 65 → 68 ms, counters unchanged, positions 2 → 8 ms, no index. 7 tests; 565 datadesk / 1581 backend. Plan §3 octava tanda, §4 S36, §7.
- **S37 done (2026-11-22, from comparing the pane with the strip)**: the preview pane's colour field and description rendered as raw browser inputs. The cause was not the pane: the control look was declared as `.dd-field .dd-input`, so it only applied **inside a strip label**, and the block was duplicated three times (`.dd-field .dd-input`, `.dd-rows .dd-input`, `.dd-filter input`) while the pane's copy never existed. Now it is plain `.dd-input`; the rows control keeps its narrow box and alignment, the filters keep their selects and chevron, and `textarea.dd-input` gained vertical padding. Measured: 34 px, radius 8, 13 px Inter, same border and padding in all four fields; the strip's datalist field shows the same native arrow as the pane's. 3 pins in `test_layout`; 568 datadesk. Plan §3 novena tanda, §7.
- **S34b planned (2026-11-22, the rest of S34)**: the workbench footer says "Showing 1-100 of 2600 rows" while the counter says 2540 — Tabulator derives the total from pages × size in remote pagination and the endpoint's `total` never reaches it — its `First/Prev/Next/Last` stay English in Spanish, and the entity is *issues* in the menu and the counter while everything else says *series*. Send the footer sentence for the page from the server, deal with the four buttons, rename the text only. Plan §4 S34b.
- **S38 done (2026-11-22, porque el popup nativo no es nuestro)**: the series date field stops being an `input[type=date]` — the native picker speaks the browser's language, wears the browser's chrome and cannot show the month by name. The field shows the date written out (`12 may 1987`) and keeps the ISO in `data-value`, like a reference field keeps its id; `formValue()` learned that branch, so the change set, the review, the draft and the writer keep ISO, and undo repaints it with `setDate(value, quiet)`. The calendar is ours: month select with full names, year box, `‹`/`›`, weekday header (rotated **on the server**: Django lists Monday-first while its `firstDay` counts from Sunday, and the first try had Spanish starting on Sunday), day grid and «Clear the date». Esc and a click outside close it without leaving the page. The month abbreviations come from `date_format(..., "M")` — the same source `date_text` reads — because `django.utils.dates.MONTHS_3` is not translated in this version (June is "jun" in English too). Read-only by design: typing is where `01/12` and `12/01` argue. Two follow-ups from seeing it: the month is a **button** that opens a grid of twelve (a `select` opens the browser's square list) and a **Today** button sits next to «Clear the date»; the panel now follows the field on scroll instead of closing — it used to close itself when the browser scrolled to reach it — and the outside click is decided with `composedPath()`, because the control just clicked may have been repainted by its own handler. Widths measured, not guessed: the panel is 286, the month keeps what is left (102px of room against the 70 «septiembre» needs) and the year is 56 with `min-width: 0` — an input's automatic minimum is its twenty-character default and was eating the flex basis at 85px. 9 tests + 1 restored; 590 datadesk / 1606 backend. Plan §3 décima tanda, §4 S38, §7.
- **S31–S32 planned (2026-11-20, from the first review with real data)**: the rest of the fourth wave lives in the plan (§3 table, §4 detail, §7 log). **S31**: backups screen — list, run, download; the endpoint already exists, but `BACKUP_DIR` is inside the container. **S32**: restore as pre-dump → maintenance (503 for the rest of `/datadesk/`) → `clear_data` + `loaddata` + `sqlsequencereset`, typed confirmation, only `stamps`/`full`; `loaddata` overwrites by PK but does not delete what the dump lacks, and `clear_data` + `loaddata` without `setval` breaks the next insert. Nothing implemented.
- **S28 mockups**: `memory-bank/mockups/workbench-compare.html` stacks the three variants (current, Bootstrap 5.3.3, polished on the S24 tokens with Inter vendored), and `workbench-polished.html` is the reference the step was built against. The devcontainer has a headless Chromium (playwright, in `/tmp/opencode`), so visual steps are checked with screenshots instead of blind.
- **S27 done (2026-11-19)**: the workspace walks the list it was opened from — `issue_positions()`/`neighbours_of_issue()` reuse `page_of_issue()`'s pks, the filters travel in the `↗` link and come back in the arrows, the `1.234 / 2.540` counter and the back link, with `[`/`]` on the keyboard and a fallback to the whole list for a series outside the filter. The list also deletes a series in place with the shared S17 dialog and `Supr`.
- **S26 done (2026-11-19)**: the reference tables can finally gain a row — `New row` and `N`, a one-field dialog over the existing create endpoint, numeric with the workspace's year bounds, a duplicate selects the row that already existed, and the new row is revealed even when the sort left it on another page.
- **S25 done (2026-11-19)**: one stamp can be deleted from the grid in `mode=edit`, with its own preview (`stamps/<pk>/dependencies`: collection items, their collections and the sibling stamps), no typed confirmation, one audited `delete` row whose snapshot S21 uses to restore the stamp with its id and colours (collection items do not come back), and the action dimmed/refused while the change set has edits.
- **S24 done (2026-11-19)**: the type scale is six tokens and the 52 `font-size` rules go through them (nothing below 11 px, nothing literal), grid 13 px with 36 px rows, and — the part that mattered most — Tabulator's own chrome replaced by ours (`#aaa` cell borders, `#efefef` zebra and `#9baeca` selection were the real "dated" culprit). Four tests pin the scale; seen on a 2560 monitor the wider type pushed the workbench into a horizontal scroll, so the card cap went to 1600, the workbench and lookups grids moved to `fitColumns` with per-column `grow` weights, `.dd-btn` stopped inheriting the underline of its `<a>` variants, and the grid height went to `calc(100vh - 300px)`. The buttons then got the same treatment: `.dd-btn` is `inline-flex` with a centred label and `min-height: 32px`, and the ghost variant only sets its sides, so a row of them lines up.
- **S23 done (2026-11-19)**: the refused cell's ring no longer loses its bottom edge — the cell is lifted with `position: relative` + `z-index` instead of being painted inside itself (an `outline` would be covered the same way), and two tests pin the declaration.
- **Second wave (2026-11-19, plan only)**: five findings from using the app — see S23–S27 in the plan. Two are mine to answer for: the cell ring painted with `box-shadow: inset` loses its bottom edge under the next row, and the type scale never leaves the 10–12,5 px band. The other three are gaps left on purpose (stamp delete, `New row` in the lookups screen) and one door that exists only inside the workspace (deleting a series from the list).
- **Close-out (S22, 2026-11-19)**: `/`, `j`/`k` and `N` complete the keyboard contract (each grid lists its keys, no shortcut fires while a control has focus), `↺ Use last issue` names the values it sets and is disabled when the form already has them, a test forbids prose in the JS, `--dd-soft` went to 4.8:1 with `:focus-visible` everywhere, `service.py`'s last coverage gap (date sorting) is tested, and the README documents the keyboard, the pre-commit backup, turning the flag off and what a revert cannot restore.
- **Activity and revert (S21, 2026-11-19)**: `/datadesk/activity/` lists commits newest first, paginated by commit, with rows, operations and changed columns, and a state badge (reversible / merge / reverted on …). `POST activity/<id>/revert` undoes the whole commit in one transaction: creations deleted children-first, updates restored from the full `before` with `updated_at` set by hand, deletions recreated with their ids and colours, merges refused; refusals are 409 and re-render the page with the reason. The revert is a commit of its own (`reverts_commit_id`) and the original rows get `reverted_at`. The dialog says the `CollectionItem` rows the cascade removed do not come back.
- **Dashboard (S20, 2026-11-19)**: `/datadesk/` shows the six "needs attention" queues as cards that open the workbench filtered; the stamp-level ones also say how many series hold those stamps because the grid counts series (1.177 · in 1.044 series on the real data). One table maps counter → filter → label → unit. Counters at zero are listed apart, not shown as work. **The filter `stamps_without_image` was broken and is fixed here**: it read `Stamp.image` (empty in every real row) and matched 2.542 of 2.543 series; both the counter and the filter now come from `picture_gaps()`, one walk of the index, 28 ms warm.
- **Lookups screen (S19, 2026-11-19)**: `/datadesk/lookups/` (eight tables with their size) and `/datadesk/lookups/<key>/` (one grid for all of them: usage annotated, inline rename, merge, delete). Rename → 409 `duplicate_name` with the id and the merge opens pre-filled; merge is one transaction with `keep_name_from` (a = survivor's name, b = the deleted row's), one `operation="merge"` audit row with counts, non-revertible; FK moves set `updated_at` by hand (`auto_now` does not fire on `update()`), colours go through the junction table with `ignore_conflicts` and then delete the source rows, years move their series; delete only when usage is 0 (409 `in_use`). JSON envelope now in `views/envelope.py`, plurals in `texts.py`. The screen creates nothing: creation lives in the workspace (S18).
- **Typed reference fields (S18, 2026-11-19)**: the six strip lookups are `<input list>` + `<datalist>` fed by `GET /datadesk/lookups/<key>/search?q=` (50 rows) with `+ Crear "X"` when the text is not a known row, so the page ships no reference table and a new artist/printer/colour is one click away. The form speaks ids (two maps translate name↔id, seeded from the DOM, grown by searches, saved with the draft); an unknown name blocks the commit instead of clearing the field; a created row is written at once, so the review panel lists it apart as already saved; colours are created from the grid toolbar since Tabulator's list editor takes no text. Colours remain read-only in `mode=edit`: the change set has no M2M and S19 did not need it either, so correcting a stamp's colours is the one gap left (recorded in `progress.md`, not assumed to be covered).
- **Clone and delete (S17, 2026-11-19)**: `datadesk/dependencies.py` + `clone_series()` + `delete_series()` behind `POST issues/<pk>/clone`, `GET issues/<pk>/dependencies` and `POST issues/<pk>/delete`. A clone copies rows, not a form (gaps travel, name and codes kept, `year`/`date` overridable, `cloned_from` on the series' audit row); the delete checks the typed year server-side, recounts inside its transaction and audits one `delete` row per stamp plus the series with a full `before` for S21. `Clone`/`Delete` sit in the strip of `mode=edit` and are disabled while the change set has edits; the dialog lists the three counts and closes with `Esc` without leaving the page.
- **Write core (S12, 2026-11-19)**: `datadesk/write.py` + `datadesk/views/write_api.py`, plain Django JSON endpoints (never `/api/v1/`): `POST issues/create` (series + nested stamps, one transaction, all or nothing), `POST apply` (`create`/`update`, savepoint per row, `delete` → 409 `needs_confirmation`), `POST lookups/<key>/create` (`get_or_create`, duplicate → `created: false`). `year` is a **number** resolved with `get_or_create` (the implicit `Year` is not audited, so a 8-stamp series writes 9 audit rows); colours bypass the serializer because DRF refuses `colors: []` and a colourless stamp is a gap, not an error; `""` on a nullable column becomes `None`; `image` is read-only; `select_for_update()` guards the `expected_updated_at` check; 500-change cap; one `commit_id` per request. Year bounds live in `datadesk/rules.py` (shared with the form) and `IssueCreateView` became `IssueNewView`. 56 tests; 1250 backend tests green.
- **New-series dry mode (S11, 2026-11-19)**: `GET /datadesk/issues/new/` renders the same workspace template with `mode="new"`, the series form (all 15 `Issue` fields), a client-side row generator and no write anywhere. Prefill is **only `country` + `year`** from the highest `id` (a table of keep/copy decisions is in the plan: classification changes per series and the print run/market values belong to a set, so copying them corrupts data); `↺ Use last issue` re-applies it from the page config, no extra endpoint. `rows=N` is 4 by default, 1–100, grows by appending and shrinks only while the last row is untouched — rows carry `touched: false`, follow the series name until first edit, and get `new-<n>` ids (real ids are numeric, so no collision; prefix comes from the server). `beforeunload` fires only when the form or the row set differs from the start, `Shift+Enter` stays inert with a fixed notice under the grid, the form is a `div` on purpose (a `<form>` would reload on Enter), and the detail route uses `int:` so `new` cannot be read as an id. The year is **typed, not chosen** (`input[type=number]` + `<datalist>` of existing years, value sent as the number, `get_or_create` on save, bounds 1800–current+2, quiet notice when the year does not exist yet) because a series usually opens a new year and `Year` has no row yet. 28 tests; 1194 backend tests green.
- **Workspace polish (S10b, 2026-11-18)**: thumbnails read from the mounted image tree — `DATADESK_STAMP_IMAGES` (dev binds `../frontend/assets/stamps` read-only in its compose; prod defines its own mount in the single compose that runs db + backend + frontend, so the repo's prod compose stays untouched and the env var can point anywhere) — served by a staff-gated `/datadesk/stamps/<id>/image` with ETag/private cache. 8.419 of 9.558 stamps (88%) have a file; the listing is cached 60 s and passed to bulk callers (queue 36 ms instead of 11.5 s). Chips carry a tone from `palette.py` (Spanish keyword stems, stable md5 fallback, Multicolor/Cuatricomía neutral). Open icon is an inline SVG chevron + double-click; inheritance was removed entirely after review (series values describe the set), leaving a short hint under the strip. `missing_data_report()` counts missing files, not `Stamp.image`.
- **Read-only workspace (S10, 2026-11-18)**: `/datadesk/issues/<id>/` with the series strip and its stamps. Every cell shows what the stamp stores: the `inherited` map and its tint were removed on 2026-11-18. Rows travel inside the page (`json_script`), the grid does not paginate, and the 8 series attributes are never repeated per row. The workbench opens a series from its chevron link, a double click or `Enter` (`selectableRows: 1`); `Esc` uses `history.back()` so the filters survive. `base.html` now emits the real `<html lang>` from `{% get_current_language %}`. Measured: 57-stamp series 14 ms / 3 queries / 28 KB.
- **Performance (S9, 2026-11-18)**: measured on the real data and documented in `memory-bank/datadesk-perf.md`. First page 68 ms, last page 67 ms (the big OFFSET costs nothing extra), worst queue 82 ms; p95 far under the 300 ms target and 2 queries at any `size`. The cost is **planning** (42 ms) over execution (24 ms) of the 8-table join, so **no index is added**: `icontains` compiles to `UPPER(name) LIKE UPPER('%q%')` (a btree cannot serve it; would need `pg_trgm` + GIN), the year filter already uses the FK index, and the stamp-level queues are semi joins over 9.558 rows. Revisit if p95 passes 150 ms or the volume grows tenfold — then the lever is thinning the join, not an index.
- **Production deployment (2026-11-19)**: the server runs one compose file with the three containers (db, backend, frontend), not the repo's per-service ones. The stamp-picture mount and `DATADESK_STAMP_IMAGES` live there, so the path can move without touching the repo; a path that does not resolve is not an error (placeholder + queue counts everything).
- **Longest series is 57 stamps** (measured in S9), not 24 as the earlier note said; S10's acceptance was corrected. `stamp_queryset()` is 2 queries / 3 ms.
- **Workbench (S8, 2026-11-18, first milestone)**: `/datadesk/issues/` + `/datadesk/grid/issues`. Filters in the URL, column choice in `localStorage`, column titles rendered by Django as JSON (no UI text in `workbench.js`), 300 ms debounce, `size` capped at 200 and `page` clamped. `SORT_FIELDS` is a whitelist; the three stamp-level "needs attention" filters use `Exists` so they cannot break the `Count("stamps")` annotation. Grouping by year is per page by design, and the expandable row waits for S10. Real data: 100 rows in 138 ms.
- **Read layer (S7, 2026-11-18)**: `datadesk/registry.py` (8 lookups, `Lookup` dataclass with model, label, name column, numeric flag and incoming refs that a test resolves against `apps.get_model`) and `datadesk/service.py` — `issue_queryset()` is one query with 7 `select_related` + `Count("stamps")`, ordered year / date (nulls last) / name; `stamp_queryset()` prefetches colors; `missing_data_report()` returns the 6 counters behind the "needs attention" selector, counting `face_value == ""` (the column is NOT NULL) and `image` NULL-or-empty.
- **Audit trail (S6, 2026-11-18)**: `DataDeskChange` (one row per touched object, grouped by `commit_id`, with `reverted_at`/`reverts_commit_id` for S21) and `datadesk/audit.py`. `snapshot()` keys fields by `attname`, so `Stamp(**snapshot)` rebuilds a deleted row; `Decimal` goes in as string and dates as ISO-8601. `record()` validates the operation and coerces `AnonymousUser` to NULL. Admin is read-only on add/change/delete.
- **Timestamps (S5, 2026-11-18)**: `Issue.updated_at` / `Stamp.updated_at` are `auto_now=True, null=True, db_index=True`. Nullable is what lets the pre-existing backups load (verified: 12.763 objects from July, all timestamps NULL); on a table that already has rows, `AddField` stamps them with the migration time, which becomes S12's baseline. Both response serializers use `exclude = ["updated_at"]` so `/api/v1/` and the schema are unchanged; both admins show it read-only.
- **Auth in place (S3, 2026-11-18)**: own login page at `/datadesk/login/` (standalone template, no shell), `DataDeskAccessMixin` + `DataDeskGateMiddleware` (401/403 for JSON, redirect with `next` for browsers), throttling 5 failures / 5 min in a `FileBasedCache` at `backend/.cache/` (already gitignored), shutdown via POST-only logout. `DATADESK_TLS` only flips cookie/`SECURE_PROXY_SSL_HEADER` flags; it is read at import, so tests prove it in a subprocess. IP is `REMOTE_ADDR` on purpose (behind nginx it collapses to per-user).
- **Auth decisions closed (S3, 2026-11-18)**: `FileBasedCache` for login throttling (one user, no concurrency, shared by the 4 gunicorn workers without a table); no nginx locally and nginx+TLS in the deployment, so TLS settings live behind `DATADESK_TLS` with a single code path; global `LOGIN_URL` untouched (`login_url` in the mixin); IP allowlist only documented in the README, implemented after DataDesk itself is finished.
- **Write core closed (S12, 2026-11-18)**: two endpoints, one transaction each — `POST /datadesk/issues/create` (issue + nested stamps, all-or-nothing, no temp ids) and `POST /datadesk/apply` (existing rows, savepoint per row). Transport is plain Django views returning JSON, **not a REST API** and never under `/api/v1/`; DRF serializers are used for validation only. `delete` is rejected by `/apply` (409) and lives in S17 with the dependency preview. Lookups created inline use `get_or_create`; optional `expected_updated_at` per row; 500-change cap.
- **Review status (2026-11-18)**: closed — §2 schema (opción A, no `Stamp` columns), S3 auth, S7+S8 workbench/querysets, S12 write core (two endpoints), S14 client buffer, S19 lookup merge, S21 revert. Still to skim: S1, S2, S4, S5, S6, S9–S11, S13, S15–S18, S20, S22.
- Full plan: `memory-bank/datadesk-app-plan.md`. **Implementation started 2026-11-18 — S1 done** (app mounted at `/datadesk/` behind `DATADESK_ENABLED`, provisional `DashboardView`, 3 mount tests). Next step: **S2** (vendored HTMX/Alpine/Tabulator + `base.html`).

## Retomar aquí (guardado 2026-11-26)

**El plan de la AI API está cerrado: A0–A2, A6–A10 hechos.** El contrato pide
evidencia, el proveedor es opencode, la red pasa por un cliente con allowlist y caché,
la identidad la resuelve el catálogo de Fesofi, el valor sale de una media recortada
con condición leída de la ficha, una request tiene presupuesto y el modelo no puede
afirmar nada que las fuentes no sostengan.

- **Leer primero**: `backend/ai_api/README.md` (el módulo tal y como es) y
  `memory-bank/ai-api-plan.md` §3 (decisiones), §4 (pasos) y §7 (registro). Lo que
  contestó cada fuente, con los códigos HTTP reales, está en
  `memory-bank/ai-sources-spike.md`; la evidencia cruda, en `ai-sources-spike.json`.
- **Lo que queda fuera, con su motivo**: valuación de serie (ninguna fuente vende el
  conjunto como una pieza), Iberphil (sólo martillo por lote), eBay (403), conversión
  de divisa, y validar la prosa (va marcada `llm`).
- **Dos decisiones de despliegue, no de código**: el valor de `OPENCODE_MODEL` (los
  gratuitos del Console dan 403 desde fuera, así que será de pago) y quién llama al
  endpoint. **Dónde se investiga ya está decidido**: DataDesk y Flet piden una serie
  al endpoint, `ai_prices_backfill` llena la base; pero **ninguna de las dos apps lo
  llama todavía** — ese es el siguiente trabajo si se quiere usar, y vive en sus
  propios planes, no aquí.
- **Palanca pendiente y gratis**: `LLM_BATCH_SIZE=15`. Las llamadas al modelo son
  `1 + ceil(n / LLM_BATCH_SIZE)` y van en serie: con el lote en 5, la serie de 6
  sellos hace 3 llamadas y la de 57 haría 13.
- **Verificación rápida**: `python -m pytest ai_api -q` → **316 verdes**; la suite
  completa, **1.823**. `manage.py check` y `manage.py spectacular` limpios. Y la
  prueba de verdad: `navidad 1986` resuelve a 2884/2883; 29 sellos en 0,9 s.

## Notes
- **AI API A0 done (2026-11-25)**: the source probe ran and its report is
  `memory-bank/ai-sources-spike.md` (raw evidence in `ai-sources-spike.json`),
  produced by `manage.py ai_sources_probe` (`ai_api/probe.py` +
  `management/commands/ai_sources_probe.py`, 27 tests). Findings: **Colnect** 426 on
  HTTP/1.1 / 401 `Invalid appId!` on HTTP/2 (network fine, key missing) and its
  public site behind **Anubis**; **Delcampe** forbids `/en_GB/collectables/search`
  in `robots.txt`, so scraping is **discarded** (its search does work with `term=`,
  not `q=`); **Iberphil** only shows the hammer on some lot pages and never a
  catalogue code; **Fesofi** — not in the plan — has a public exact WooCommerce
  Store API (`?sku=`) with `Número EDIFIL`, series title, face value, print run,
  colour and perforation, which is the identity bridge A6 needed. A2 must declare
  `httpx[http2]`; `min(edifil)` ≠ `min(fesofi)` per series, so matching is stamp by
  stamp.
- **Decidido por el usuario**: **Fesofi sí** (primera fuente de identidad y de
  hechos de catálogo), **Iberphil fuera**, **Delcampe fuera** y **Colnect fuera**
  (2026-11-26). Siguen abiertas, sin frenar código, el motor de opencode y dónde se
  dispara la investigación (condiciona A8). Dos cifras para A6/A7: 2.733 de los
  2.761 sellos sin Edifil tienen Fesofi (Fesofi recupera el 99% de los códigos), y
  2.433 de las 2.541 series ya tienen algún valor puesto por el LLM actual, sin
  auditoría.
- **AI API plan (2026-11-24, en marcha)**: `memory-bank/ai-api-plan.md` holds the plan
  to stop the LLM inventing philately. De las tres fuentes que se estudiaron al
  principio —Colnect, Delcampe e Iberphil— **ninguna ha quedado**: Colnect por
  decisión (2026-11-26), Delcampe por `robots.txt` e Iberphil por ser lotes sin
  código. La identidad la da **Fesofi** y los precios salen de la búsqueda en
  sitios permitidos.
- **Dataset actual (2026-11-18)**: 2.540 series y 9.558 sellos (≈3,8 de media), con dispersión amplia — hay series de 1 sello y la mayor tiene 57 (medido en S9). El grid del workbench pagina server-side; el de sellos del workspace no pagina porque es una sola serie, y el caso a probar es la serie de 57 más un fixture de 100, para confirmar que no hay techos escondidos.
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
- **Normal-user collections (A1–A4 done 2026-11-26, A5 next)**: the three reading screens are
  designed in `memory-bank/user-collections-plan.md` — collections (cards), one collection
  (its series, paginated server-side, 15 per page), one series (catalogue read-only + one
  card per stamp with the «Your copy» block). Mockups in `memory-bank/mockups/`. **A1 is
  done**: the `CurrentUser` class reads the JWT, the four collection and item views
  are scoped by it (foreign row → 404), the item update is a six-field serializer that
  refuses `collection`/`stamp`, `POST /collection_items/` refuses a foreign collection,
  `POST /collections/` takes the owner from the token and `?username=` is gone. **Measured**:
  a missing header is **403** (DRF only makes it 401 with a challenge header, and
  `CustomAPIKeyAuthentication` has none) — the plan and issue said 401 and are corrected.
  **A2 is done too**: `GET /collections/` returns `series`, `stamps`, `total` and up to 12
  `covers` in exactly five queries (pinned), with a fixture that makes the three figures
  differ. **A3 is done too**: `CollectionService(token)` with the four calls and the JWT
  header, and the URLs in `URLs.Backend` (frontend suite 660), **mergeado en la PR #477**.
  **A4 is done too**: `CollectionCard` with the collage, summary, bar and percentage
  (frontend suite 675), en la rama **478** y pendiente de commit/PR. Suite total 1.781
  backend / 675 frontend. **A5 is next** (the page itself), después de mergear A4. Decisions still standing: the series order **mirrors
  `/issues/`** with no DataDesk; services are Flet-free; neutral labels; `PUT` for renames
  and item edits. The catalogue browser is a later phase.

## Session Log
- [Today] Colecciones A4: **la tarjeta del overview**. `CollectionCard` (`ft.Container`)
  pinta el collage con los **primeros seis `covers` cuyo archivo existe** —uno grande, o
  mosaico de tres columnas, o `no_stamp` atenuado—, el nombre, el resumen por
  `collections.summary` y la barra con su porcentaje (`—` cuando no hay nada que
  completar). No es clicable todavía: `on_open` se guarda y B3 lo conecta cuando exista la
  ruta. `fmt_number` ganó un argumento `zero` para que un contador que vale cero diga `0`
  mientras las tablas conservan su guion. 14 tests con los archivos mockeados; suite del
  frontend **675**.
- [Today] Colecciones A3: **el servicio habla con el JWT del usuario**. `CollectionService`
  (Flet-free, `BaseService`) recibe el token en el constructor y ofrece listar, crear,
  renombrar (`PUT`, sin barra final porque la ruta del backend es `collections/<pk>`) y
  borrar; el token lo lee la página de `SharedPreferences` y se lo pasa, así que la capa
  sigue siendo testeable sin Flet. Añadidas `URLs.Backend.collections` y
  `collection_items`. 9 tests con `_make_request` mockeado (URL, método, cabecera, payload,
  `None` en error de red) y la suite del frontend en **660**.
- [Today] Colecciones A2: **la tarjeta ya tiene sus números, y cuestan cinco consultas**.
  `CollectionOverviewService` calcula `series` (issues distintas), `stamps` (sellos
  distintos; `quantity` no infla) y `total` (sellos de esas series, el denominador de la
  barra), más hasta 12 `covers` `{year, code}` de sellos con `fesofi_code`, en un orden
  estable. La página entera son **5 consultas** con cualquier número de tarjetas, fijado
  con `django_assert_num_queries`; el fixture hace que los tres números sean distintos
  (2 sellos en 2 series, 4 sellos en esas series). `CollectionOverviewSerializer` sustituye
  al serializador con usuario anidado **solo en la lista**; `GET /collections/<pk>/` no
  cambia. Una colección con `user=None` no se lista. 14 tests nuevos, suite **1.781**.
- [Today] Colecciones A1: **la propiedad sale del token**. `common/core/current_user.py`
  convierte el `Authorization: JWT` en el `UserCollection` y las cuatro vistas de
  colecciones e items se acotan con él: lista, lectura, renombrado y borrado, con **404**
  para la fila de otro usuario. El `PUT` de items estrena `CollectionItemsUpdateSerializer`
  con los seis campos de «Tu copia» y rechaza `collection`/`stamp` (el `GenericSerializer`
  convierte el whitelist en un 400 real), y `POST /collection_items/` rechaza una colección
  ajena. `POST /collections/` deja de buscar el usuario en `X-API-KEY` — se va el `# TODO` y
  el método — y `?username=` desaparece del esquema. 45 tests con **tokens de verdad**
  (`JwtToken().create()` en fixtures): solo lo mío, 404 ajeno, 403 sin cabecera, token malo
  y master key. **La sorpresa**: sin cabecera es **403**, no 401 — DRF solo convierte
  `AuthenticationFailed` en 401 si la clase de autenticación declara un challenge header, y
  `CustomAPIKeyAuthentication` no lo hace; el plan y el issue decían 401 y se corrigieron.
  Un 401 real exigiría `authenticate_header()` y 75 expectativas en la suite, así que queda
  fuera. La suite baja de 1.823 a **1.761** porque las permutaciones de auth (el mismo
  `PermissionDenied` mockeado por método) se sustituyen por un caso por comportamiento, ya
  cubierto en `common/test/test_permissions.py`. Después, siguiendo la regla nueva de que
  **el código vive en clases**, `current_user` pasó a `CurrentUser(request).get()` y los
  helpers de los tests a métodos estáticos (`Api.url`, `Api.headers`, `Requests.with_header`);
  la regla quedó escrita en `opencode_rules.md`. Y, por la regla de **reutilizar antes de
  escribir**, el parseo del header se movió a `common/core/authorization.py`, que ahora usan
  el permiso y `CurrentUser` (antes cada uno partía la cadena a su manera): 6 tests nuevos.
  Verde: **51 tests** de la zona y la suite en **1.767**.
- [Today] Colecciones de usuario: **mockups y plan revisados antes de escribir código**.
  Los tres mockups pierden el nombre de usuario de la derecha del header (ya está en el
  drawer) y el separador que solo existía para él. El plan se contrastó con el código y
  salieron cinco correcciones: sin cabecera son **401**, no 403; el **paso A1 incluye las
  vistas de items y el whitelist del update** (si no, un item se puede mover a la colección
  de otro); el orden de series **copia `/issues/`** (`sortBy=date`, empate por `id`) y no
  toca DataDesk; los servicios siguen **Flet-free** y reciben el token de la página; y los
  contadores usan **etiquetas neutras** porque el sistema de locales no tiene plurales.
  Renombrar y editar un item van por **`PUT`**, que ya existe. El plan queda en dos fases
  (A1–A6 overview, B1–B5 las otras dos pantallas), con contrato, ficheros y tests por paso.
  Nada de código tocado: lo siguiente es A1.
- [Today] AI API A10 y cierre del plan: **el cierre encontró tres promesas sin
  cumplir y las arregló**. `sources` llegaba siempre vacío —ahora la vista informa de
  cada fuente de precios con `ok` / `empty` / `error` / `skipped`, y un fallo deja de
  disfrazarse de «respuesta vacía»—; `SourceObservation.Source` ofrecía `colnect` y
  `ebay` (fuera del plan) y no ofrecía `filatelia` ni `search`, que es lo que el
  pipeline escribe; y sobraba código: `sources/registry.py` con su ABC
  `SourceAdapter` (7 tests), el `issues_extraction` que nadie usaba en el frontend y
  el extra `httpx[http2]`, que sólo existía para la CAPI de Colnect (el sondeo de A0
  sin `h2` informa del `ImportError`, que es la verdad). El README del módulo está
  reescrito entero —recorrido de una petición, fuentes, contrato, ajustes, backfill,
  errores y lo que no hace— y el del repo tiene su sección. El esquema muestra
  `partial`, `subject_code` y `valuation` sin avisos. `valuation` de serie sigue
  `null` por decisión: una serie no es la suma de sus sellos. 3 tests nuevos, 1.823
  verdes.
- [Today] AI API A9: **lo que las fuentes no sostienen, no sale**. `ai_api/validation.py`
  con `check_support(data, facts)` compara la respuesta del modelo contra los hechos de
  la petición: texto sin mayúsculas, acentos ni espacios; números sin separadores
  (`4.000.000` = `4000000`); y fechas, con tabla de meses en español (`1986-11-16` =
  «16 noviembre 1986»). Un **código Edifil o Fesofi que no está en la fuente se anula**,
  que es el error que más se parece a un dato; igual con una fecha, un facial o una
  tirada inventados. `paper_type` y `stamp_type` no tienen campo propio en el catálogo,
  así que no se tiran por sistema: se aceptan si el texto de las fuentes los menciona
  («estucado», «hoja bloque» en una descripción) y se anulan si no. Los sellos se
  emparejan por su código y se comprueban sus campos; las descripciones sobreviven y
  siguen marcadas `llm`, porque el validador no juzga prosa. Los huecos van en `gaps`
  con el nombre del campo, con tope de 20. 17 tests nuevos, 1.827 verdes.
- [Today] AI API A8: **una request con reloj y un comando para el catálogo**.
  `ai_api/budget.py` es un reloj (`total`, `per_call`, `remaining`, `timeout_for`) y
  la vista corta el bucle de precios cuando se agota: responde con lo que tiene,
  `partial: true` y un `gap` de `budget` que dice que la caché acabará en la
  siguiente llamada. El catálogo recibe el tope en cada llamada. Lo que **no** se
  promete: interrumpir una llamada ya bloqueada; el límite es por llamada y por
  fase, y la suma de la fase del catálogo puede llegar a n × per_call. `manage.py
  ai_prices_backfill` con `--limit`, `--source`, `--only`, `--stamps` y `--dry-run`
  recorre las series, pide precios y guarda `SourceObservation` colgado del `Stamp`
  real —lo que el endpoint no puede, porque no tiene sujeto— con `raw_hash` como
  identidad, así que una segunda pasada no duplica la evidencia. Y con esto queda
  decidido **dónde se investiga**: DataDesk y Flet piden una serie al endpoint, el
  comando llena la base, sin cola ni Celery. 19 tests nuevos, 1.804 verdes.
- [Today] AI API A7b: **la condición estaba en la ficha**. Antes de escribir el
  parser, sondeo: la ficha de TodoColeccion es `/<sección>/<slug>~x<id>` (ruta que su
  `robots.txt` permite) y responde **403 con sólo un User-Agent** (Cloudflare) pero
  **200 con `Accept` y `Accept-Language`** manteniendo nuestro User-Agent; por eso el
  `HttpClient` manda ahora esas dos cabeceras. La condición está en el **título**
  (`h1#lote-page-h1`: «NUEVO MNH** sin fijasello», «Usado») y el precio en
  `span.lote-precio`; «Estado del lote» describe desgaste y no se usa. Las fichas de
  **vendidos** («Vendido el …») dan precio de venta real, el primero que tenemos, y
  se marcan `kind: sold`. **eBay no**: responde 403 con una página de error, así que
  no se escribe un parser que no se puede probar. `sources/listings.py` con `Listing`
  y un parser por sitio; `SearchPrices` abre hasta 3 fichas por consulta cuando la
  snippet no trae precio o condición, y la ficha manda sobre la snippet.
  `text.price_in()` entiende el separador de miles («1.250,00 €» son 1250,00, no
  1,25). Medido: el Edifil 4350 pasa de 0 condiciones conocidas a **4 MNH** y de
  ningún estimado a **4,45 €** (n = 4); el 2867 tiene una oferta real de 0,03 € y con
  n = 1 es un `gap`. 19 tests nuevos, 1.788 verdes.
- [Today] AI API A7: la valoración, y el dato que la hace honesta. `ai_api/valuation.py`
  hace una **media recortada** (mínimo y máximo fuera con n ≥ 4), exige `n ≥ 3` por
  condición, devuelve rango, `sample_size`, `sources`, `method` y `as_of`, y **sólo
  euros**: otra divisa no se convierte, se dice. `sources/store.py` saca la parte
  común de WooCommerce, `sources/filatelia.py` lee precios por `Nº Edifil` con su
  `Estado` y su `Año`, y `sources/search_prices.py` lee el precio de la snippet y
  deduce la condición del texto (sólo hosts permitidos, sin precio no hay
  observación). La respuesta gana `subject_code` por observación; los valores por
  sello salen sólo de sus observaciones y de su condición, y la serie se queda en
  `null` porque no hay observación del conjunto. **Dos correcciones de datos**: el
  precio de la Store API viene en **unidades menores** (la «Prueba Oficial 100» son
  10 €, no 1.000 €) y la tienda tiene mucho menos stock de lo que parecía: 100, 1 y
  10 dan **un** precio cada uno y el 286 ninguno. La búsqueda sí encuentra ofertas
  (2,90 € y 6,10 € para el 4350) pero **sin condición**, así que no entran en el
  estimado. De ahí que A7 quede hecho y **A7b** sea abrir la ficha del anuncio para
  leer el estado: sin condición no hay valor, y el `gap` es la respuesta correcta.
  47 tests nuevos, 1.769 verdes.
- [Today] AI API A6, segunda rebanada: **los hechos vienen del catálogo**. `identify()`
  devuelve un `Match` con `products`, `term`, `score`, `candidates` y `gap`; el orden
  es cobertura de palabras, nombre exacto antes que parcial, serie antes que motivo y
  nombre más corto, y **un empate es un `gap` con los dos nombres**, no una elección
  por suerte. `facts()` construye `serie_info` y `stamps` con **las mismas claves que
  `clean_scraped_data`**, leídas de los atributos: códigos, facial, color, dentado,
  tirada, fecha, motivo y la descripción del catálogo sin HTML. El emparejamiento es
  sello a sello por sus códigos, y un acierto por **motivo se ensancha a la serie**
  que el producto declara, así que «la sagrada familia» da el sello 2883 y el informe
  sale con los dos de «Navidad 1986». La vista prefiere el catálogo y deja búsqueda +
  raspado de respaldo, con un `gap` de `identity` cuando el respaldo es quien
  rescata. Cuatro cosas que sólo se ven con datos reales: `Fecha De Emisión` lleva la
  D mayúscula y `Año de Emisión` no (las claves se comparan sin acentos ni
  mayúsculas), `Formato` es el **tamaño** y no el tipo (`stamp_type` no se inventa),
  un término de serie y uno de motivo con el mismo nombre no empatan porque el
  atributo desempata, y el ensanche necesita la taxonomía del término. Real:
  `navidad 1986` → 2867/2868, `castillos 2007` → 4349/4350, `isabel ii 1850` → 1–5,
  `quijote 1998` por motivo y ensanchado, `zzzz` → `gap`. 15 tests nuevos, 1.707
  verdes.
- [Today] AI API: mirados tres sitios más para el precio, ya sin Colnect.
  **`filatelia.online` entra**: es WooCommerce y expone la misma Store API que
  Fesofi, pero con atributos de sello —`Nº Edifil` (`pa_sello-numeracion`, id 45),
  `Estado` (12), `Año` (2)—, así que se resuelve un código a término y sus productos
  traen precio y condición (la «Prueba Oficial 100 – Navidad – 2009» está a 1.000 €,
  «Nuevo (sin circular), Sin charnela»). Es precio de **oferta** a nivel de sello,
  que es lo que la búsqueda genérica no da; su cobertura es su stock, así que
  `n ≥ 3` fallará a menudo y será un `gap`. **`circulomadrid.com` descartado**:
  vende y expertiza y muestra P.V.P. y precio de catálogo, pero es un CGI
  (`cirmar.dll`) con una página por sello, sin búsqueda explotable y con catálogo
  cargado de extranjero. **`stampworld.com` descartado por ahora**: catálogo con
  valores y `robots.txt` que permite el uso de referencia, pero 403 de Cloudflare a
  cualquier cliente que no sea un navegador. Iberphil sigue opcional y a nivel de
  lote. Anotado en el plan: A7 con las dos fuentes en orden, la allowlist tendrá que
  sumar `filatelia.online` al implementarse, y los dos descartes con su motivo.
- [Today] AI API: **Colnect queda fuera** por decisión del usuario. Se cae A3 y con
  él la clave CAPI, que era el único paso bloqueado del plan. Lo que importa es lo
  que arrastra: Colnect era la única fuente de **precio de mercado** por API, así
  que **A7 sube de S a M** y se reescribe —los precios salen de la búsqueda en
  sitios permitidos (`todocoleccion.net`, `ebay.es`/`ebay.com`), de la snippet o de
  la ficha, cada uno con su `kind`—, y casi todo lo que se encuentre serán ofertas,
  no ventas, cosa que la estimación dirá en `method` y `kind` en vez de disimular.
  **A6 cambia de papel**: Fesofi deja de ser «el primer escalón» y pasa a ser la
  espina de la identidad; el hueco de Edifil (2.761 sellos) deja de bloquear nada.
  **Serper deja de ser provisional**: sin Colnect es la puerta a los precios. Y el
  extra `httpx[http2]` se queda sin motivo —es inofensivo, pero se puede bajar a
  `httpx==0.28.1`. La forma de la respuesta no cambia: ya estaba pensada para no
  depender de una fuente concreta.
- [Today] AI API A6, primera rebanada: la serie se encuentra por **nombre parcial**.
  El fallo era de diseño: `site:… "navidad" "1986"` pedía dos frases literales y no
  encontraba nada aunque Google devuelva el enlace. Ahora `FesofiCatalogue`
  (`ai_api/sources/fesofi.py`) pregunta a la Store API por **atributo** —`Título
  Serie` (id 5) y `Año de Emisión` (id 22)—, cuyo buscador de términos es parcial y
  no distingue mayúsculas. El nombre se parte en palabras sin acentos ni stopwords,
  el año de cuatro cifras se separa como filtro, y los candidatos se prueban en
  orden de cobertura **hasta que uno tenga productos**: por eso `castillos de
  españa 2007` acaba en el término «Castillos», que es donde vive la serie de 2007.
  `SearchService` pasa a ser un localizador: catálogo primero, Serper de respaldo, y
  un fallo del catálogo se registra en vez de tumbar la búsqueda. Comprobado en
  real: `navidad 1986` → 2884/2883 (Edifil 2867 y 2868) y el scrape de 2884 da la
  serie entera (`Navidad`, 16 noviembre 1986, 2 sellos con códigos); `expo 92` →
  2960; `isabel ii 1850` → 5 páginas; `quijote 1998` → 3601 (por motivo, falta
  comprobar que sea el sello y no la hoja). **Bug propio encontrado al probarlo**:
  la caché de `HttpClient` (A2) indexaba por URL sin la query, así que todas las
  consultas a `/products` compartían entrada y «castillos» devolvía los sellos de
  Navidad; la query entra ya en la clave, con test. Y el nombre puede ser el
  **motivo** de un sello suelto, así que la búsqueda cubre también `Motivo Sello`
  (id 6): `la sagrada familia 1986` resuelve a 2883 por «La Sagrada Familia.
  Valladolid» y el scrape da «Navidad 1986» con Edifil 2867 y 2868. Cada candidato
  recuerda de qué atributo salió, y la consulta de productos filtra por ese mismo
  atributo. Y se arregló el corte de las descripciones: `desc_snippet` hacía
  `[:180] + "..."` siempre —también en textos cortos—, así que el modelo las leía
  como truncadas y escribía «(texto truncado en la fuente)». Ahora el tope es 2.000
  y el `…` sólo aparece cuando de verdad no cabe; las fichas reales llegan enteras
  (1.223 y 728 caracteres). 29 tests nuevos, 1.693 verdes. A6 sigue abierta: leer
  los hechos del producto de la Store API, el matcher con `score` y los `gaps`.
- [Today] AI API A2: una sola puerta a la red. `ai_api/sources/` trae `HttpClient`
  (allowlist por host con subdominios, timeouts de conexión y lectura, reintentos con
  jitter sólo para 5xx/429, semáforo por host, caché TTL de los 200, User-Agent
  propio y un singleton de proceso para que la caché y los límites sirvan de algo),
  `errors.py` con un error por significado, `base.py` con el contrato de adaptador y
  `registry.py`. `SearchService` y `ScrapingService` pasan por él, y el scraping va
  **en paralelo**: la serie de 29 sellos baja de 7,0 s a **0,9 s** (0,31 s la segunda
  vez, con caché); la de 6, de 1,7 a 1,2 s. Con eso caen los defectos de §1 que
  quedaban: el SSRF (el atajo de URL ahora exige allowlist y un host no permitido da
  400), el timeout de Serper, el 422 muerto (los `ValueError` dejan de envolverse), el
  scrape vacío que reventaba como 500 (ahora 422 con motivo), una sola fuente de
  configuración y la lectura muerta de `serie_info` (`issue_name`/`issue_date`). Los
  errores se separan: 400 host no permitido, 404 «no hay nada», 422 contrato, 500
  configuración, 502 fuente caída. El defecto 9 se cierra **por decisión**: la vista
  sigue siendo master-key only. De paso, `elapsed_ms` en el log del proveedor,
  `httpx[http2]==0.28.1` en `requirements.base.txt` y `httpx`/`httpcore` a WARNING en
  `log_setup` (a DEBUG escriben cada byte del protocolo). 35 tests nuevos, todos por
  `httpx.MockTransport`, 1.664 verdes.
- [Today] AI API A1b verificado en real y fin de jornada. Con `glm-5.3-flash`, una
  extracción desde Swagger pasó la tubería entera y devolvió la forma de A1: precios a
  `null`, `valuation: null`, `description_source: "llm"` y una descripción sin
  cifras. Al usarlo se vio que tarda, y medido con el código del repo el scraping no
  es el culpable (6 sellos 1,7 s; 29 sellos 7,0 s): lo son las llamadas al modelo,
  `1 + ceil(n / LLM_BATCH_SIZE)` y en serie (6 sellos → 3; 57 → 13). Palanca gratis
  pendiente: subir el lote a 15. Para A2 quedan anotados cuatro hallazgos del primer
  uso: el scraping secuencial pide pool con límite por dominio y caché,
  `SearchService` se traga el fallo de Serper y lo cuenta como un 404, la vista lee
  `título serie` / `fecha de emisión` cuando el limpiador devuelve `issue_name` /
  `issue_date`, y falta `elapsed_ms` por llamada para dejar de adivinar.
- [Today] AI API A1b: opencode es ya el único proveedor y Gemini y Groq han salido
  del código. `opencode_provider.py` hace `POST /chat/completions` contra la API de
  inferencia del Console con `Bearer`, el modelo en el cuerpo, `response_format` JSON
  y timeout y `max_tokens` por configuración; en un error registra el código y el
  principio del cuerpo —que es lo que distingue una clave mala de un modelo no
  disponible de un límite— y en cada llamada el `usage` con su coste. De paso,
  `series_extract` subió a `BaseLLMProvider`: estaba duplicado palabra por palabra en
  los dos proveedores y habría sido la tercera copia. La factoría queda con una sola
  entrada y sin `LLM_PROVIDER`, porque con un único proveedor una variable que sólo
  admite un valor es una forma de romper un despliegue con un valor viejo. Fuera
  `gemini_provider.py`, `groq_provider.py`, sus tests, `test_batch_processing.py`
  (sus cinco tests del troceado ya estaban en `test_base_llm_provider.py`), el script
  de validación multi-proveedor y las dependencias `google-genai` y `groq`. 33 tests
  en tres archivos, 1.628 verdes. Queda pendiente la llamada real: no hay
  `OPENCODE_API_KEY` en el `.env`.
- [Today] AI API A1: el contrato deja de ser una promesa y pasa a ser evidencia.
  `SourceObservation` (source, external_id, url, issue/stamp, kind, price, currency,
  condition, observed_at, raw, raw_hash) guarda cada precio con la página que lo
  sostiene; el sujeto son dos FK y un `CheckConstraint` de exactamente una; `kind`
  tiene cuatro valores porque un precio de catálogo no es una oferta; y `raw_hash`
  deja la fecha fuera, así que ver el mismo precio dos veces no duplica y uno
  distinto queda como histórico. La respuesta gana `sources`, `observations`,
  `valuation` (estimate/min/max/currency/sample_size/method/sources/as_of), `gaps`
  y `description_source` — también por sello —, y los `market_value_*` quedan
  obsoletos: el endpoint los pone a `null` aunque el proveedor escriba algo, porque
  nada los sostiene todavía. Los prompts pierden la sección de valuación entera (la
  búsqueda imposible y el −25 %) y el «EXPANSION» con conocimiento interno; ahora el
  texto se escribe sólo con lo que trae la entrada y `notes` se queda vacío si no
  hay nada que decir. 22 tests nuevos (15 de modelo, 7 de contrato), 1.655 verdes,
  esquema sin avisos, migración aplicada y revertida.
- [Today] AI API: decisiones de arquitectura anotadas, sin tocar código. **opencode
  será el único proveedor** y Gemini y Groq se borran (nuevo paso **A1b**: un
  `OpenCodeProvider` detrás de `BaseLLMProvider`, el registro de la factoría con una
  sola entrada, y fuera `gemini_provider.py`, `groq_provider.py`, sus tests, sus
  claves en `settings.py` y `.env.example` y las dos dependencias). **El motor se
  elige más adelante** y viaja en la llamada, no en el código: hay 40 modelos bajo
  `opencode` y la comparación se hará con una tubería que ejecutar, midiendo campos
  inventados, huecos declarados, JSON válido y prosa. **Serper se queda de momento**
  (`SERPER_*` y `SearchService` intactos; A2 le pone el timeout que le falta) y se
  quitará en su propio paso si la búsqueda de precios no lo necesita. Anotado
  también el aviso que importa: cambiar de proveedor no cambia la epistemología —
  opencode sin herramientas puede inventar igual que Gemini; lo que lo arregla son
  las fuentes (A2/A3/A6).
- [Today] AI API A0: the source probe is done and its report is
  `memory-bank/ai-sources-spike.md`. `manage.py ai_sources_probe` walks five real
  series with `requests` (5 s between requests) and writes the raw evidence as JSON;
  `ai_api/probe.py` holds the pure parts (robots, challenge detection, parsers) with
  27 tests and no network. What it answered: Colnect **426 on HTTP/1.1 and 401
  `Invalid appId!` on HTTP/2** — the network reaches the CAPI, the key is what is
  missing — and its public catalogue sits behind **Anubis**, so the API is the only
  door; **Delcampe** works with `term=` (the first pass used `q=`, which it ignores
  and answers with the browse page, five irrelevant cards) and returns the right
  listing when the code is in the title, but `robots.txt` **disallows
  `/en_GB/collectables/search`**, so the scraper is discarded; **Iberphil** lists
  only the starting price in its sold-lots table, the hammer is on the lot page and
  only for some auctions (46 yes, 47 and 1 no), and no lot mentions a catalogue
  code; and **Fesofi**, which the plan did not include, exposes a public exact
  WooCommerce Store API (`?sku=`) that returns `Número EDIFIL`, series title, face
  value, print run, colour, perforation and printer — 4 of the 5 series resolved —
  which is the identity bridge A6 was going to build by guesswork. Two consequences
  worth carrying: A2 needs `httpx[http2]` (the container has `httpx` without `h2`),
  and `min(edifil)` ≠ `min(fesofi)` inside a series (Expo 92: Fesofi 3196 ↔ Edifil
  3188, minimum Edifil 3164), so matching is stamp by stamp. The user validated the
  spike the same day: Fesofi in, Iberphil out of the first version, Delcampe out of
  the plan; A0 is closed in the plan's step table and A1 is next.
- [Today] AI API: plan **saved and parked**, no code touched. Analysed `backend/ai_api/` end to end (99 tests green) and found the real defect behind the invented prices: the prompt tells the model to search Colnect, Delcampe and Iberphil and to "verify sold prices" without a search tool, while also forbidding internal knowledge — and then applies an invented −25%. Checked the three sources: Colnect has an official API with HMAC signing, HTTP/2 and `/market_prices` + `/item_sales` (free key on request, quotas); Delcampe's only official API is seller-side (no market search); Iberphil publishes hammer prices per **lot**, not per stamp. Plan A0–A10 in `memory-bank/ai-api-plan.md`, starting with a `ai_sources_probe` command that decides whether Delcampe can be used at all. Also recorded, for A2, the defects found along the way: SSRF behind `name` + `date: "0"`, Serper with no timeout, exceptions flattened into 500 so the 422 is dead in production, an empty scrape reported as a service error, `stamps` validated as free-form dicts, `StampDetailSerializer` unused, and the dead `issues_extraction` URL in the frontend.
- [Today] Normal-user collections: plan **closed and parked**. All decisions D0–D10 are settled (the user from the JWT, their own collections and copies, the collage card, the series figures, the order, the dimmed missing stamps) and the three mockups are in `memory-bank/mockups/`. Implementation has **not** started: step 1 (the `current_user(request)` helper plus ownership on the four collection views, which today return `all()`) is announced with its files and tests and waits for the go-ahead, with two questions for the user — close the item field whitelist in step 1 or in step 5, and whether the existing collection tests move to a real JWT header. Resume at plan §6 step 1.
- [Today] Normal-user collections: the plan was rewritten for the brief (viewing what a user owns; the user only edits their own copy) and three self-contained mockups were drawn with the real stamp pictures: collections overview, the collection's series with pagination, and the series detail with the stamp cards and the «Your copy» block. The old plan (creating collections + the catalogue picker with «Select All in Series») survives only as the later phase. Found while writing it: the collection endpoints return `all()` — every user's rows — and the `?username=` filter in the schema is ignored; the way in is the **JWT** the login returns (`HasSpecificKeyName` already understands it and the four collection views are already in `USER_VIEWS`; the Flet app just sends the master key, which is allowed everywhere), so step 1 is `current_user(request)` plus ownership before any screen. The mockups are in `memory-bank/mockups/`.
- [Today] DataDesk S38 (y su revisión): the month is a button that opens a grid of twelve, the native `select` list is gone, and a Today button sits next to "Clear the date". The panel follows the field on scroll instead of closing (it closed itself when the browser scrolled to reach it), and an outside click is decided with `composedPath()`: picking a month repaints the button that was clicked, so `contains()` said the click came from outside. 9 tests + 1 restored.
- [Today] DataDesk S38: the date is picked in a calendar of ours. `input[type=date]` gone — the native picker is the browser's, in the browser's language; now the field shows `12 may 1987` and keeps the ISO in `data-value`, with a month select, a year box, `‹`/`›` and a day grid whose weekday names the server rotates (Django's list is Monday-first, its `firstDay` counts from Sunday). Esc and a click outside close it. 8 tests.
- [Today] DataDesk S34 (formats): money, the print run and dates now read as the language writes them. `separators()` and `date_text()` live in `texts.py` (dot for Spanish thousands, month by name: `1 dic 1853` / `Dec 1, 1853`), the column definition says `format` instead of `money: True`, and the grouping happens in the script from the cell value so an edited number paints at once. The review panel formats too through `numberFields`. The strip's inputs stay raw on purpose: a number input cannot hold separators. 13 tests.
- [Today] DataDesk S37: the pane's controls now look like every other control. They already carried the right class; the style was scoped to `.dd-field`, so it never reached them — three copies of the same control block and the pane's fourth missing. Promoted to `.dd-input`, the two copies keep only their differences, and a textarea got the vertical padding it was missing everywhere. 3 pins.
- [Today] DataDesk S36: the list order inside a date. The default order was year, date, name, and there it stopped: two series of the same date with one name — which is how an emission is entered — were a tie for the database to break, and with OFFSET paging that repeats or skips rows. The real data has 419 repeated dates (15 series named «España 2000» on a single day). The tiebreak is now the series' catalogue code, taken from **Fesofi** with **Edifil** as the per-stamp fallback — Fesofi is present on 9,496 of 9,557 stamps, Edifil on 6,796 — compared by length then text (a four-digit sheet code before a seven-digit emission code) and closed with the `pk` so the order is total. Every column sort ends in the same keys and `issue_positions()` gained the annotation, so the workspace arrows and the position counter follow the visible list. 65 → 68 ms on the grid page; 2 → 8 ms on the positions, which the workspace loads on every open.
- [Today] DataDesk S35: the colours of a stamp are edited in the preview pane, which closes the gap tracked since S18. The writer already accepted `colors` on an update and S21's revert already restored them — what was missing was the door, and the row spoke names where the change set speaks ids: `serialize_stamp()` now sends `[pk, pk]` (ordered by name) and the palette ships for the chips' names and tones. The pane gains chips with their × and a typed field with a datalist and `+ Create "X"`, in both modes (in `edit` it syncs the change set and pushes a history step, in `new` it updates the draft); the column gets `patch: "colors"` in `edit` only and keeps its `list` editor in `new`. Three details that matter: the pane field is not a `data-lookup` (that would block the commit on a typed name), `flushTypedColour()` takes a colour typed but not confirmed before a commit, and a colourless stamp's cell now paints the `—` of S28 instead of nothing. 13 tests (8 for the page, 3 for the writer, 1 for the revert, 1 split in two); 558 datadesk / 1574 backend; Chromium with the 1976 series, a colourless series and `mode=new`.
- [Today] DataDesk S33: a stamp can be added to a series that already exists — the operation of every loose piece, and the last one `mode=edit` lacked. `+ Stamp` appends a **draft row** (`new-<n>`, name prefilled with the series name) that the change set sends as `op: "create"`; `sync()` has a draft branch because there is no `base` to diff against, the review lists it with a `NEW` chip and counts the row as one change, and `adoptDraft()` swaps in the real id, `updated_at` and the two per-row URLs after the commit — the URLs travel as a server-made shape (`url_template()` with `%(id)s`) because a row without an id cannot have them rendered. Clean commit reloads the same series instead of jumping to the workbench (which is what turns the draft into a stored row and keeps the retry-after-a-partial-commit path honest); `?focus=` survives as a manual deep link. Undo needed two history kinds (`create`/`remove`): one was enough to make undoing a removal remove again. Blank drafts are dropped on commit, the draft's × is local and undoable, and nothing about a `create` goes to `localStorage`. 16 tests; 545 datadesk / 1561 backend; Chromium with the 1976 series, including a partial commit and the × of an adopted row.
- [Today] DataDesk S30: the usage number of a reference row is now a door — a link to the workbench with that filter, above zero only — and the list says why it is filtered with one chip per active filter, each its own link, plus a clear-all. Five filters: `printer`, `artist`, `paper_type`, `print_type` as series columns and `color` as `Exists` (a join inflates `Count("stamps")`, pinned by a test with a two-colour stamp; the plan's `stamps__colors` + `distinct` was wrong). The link counts series, not stamps (`Count("stamps__issue", distinct=True)` in the same query), the cell title keeps the stamp count when they differ, and a year links with `year_min` + `year_max` because `Year.pk` is not the year. The chips are painted in the script from the form: the page reloads only the grid, so server-rendered chips went stale as soon as a filter was set from the bar (found in the browser). `filters_from()` is one function shared by the page and the grid endpoint now; the endpoint had a copy and the new filters would have stopped at the page. 16 tests; 509 datadesk / 1525 backend; Chromium: artist link → 1 series + chip → back to the list, colour "40 series" against "Used by 50 rows", chip appears without a reload.
- [Today] DataDesk S29: the series screen gains a preview pane on the right of the grid, tied to the selected row — `selectableRows: 1` plus `j`/`k`, which did not exist there — with the picture at 258px and `Stamp.description` editable underneath. The description is a hidden grid column (`visible: false`, `patch: "description"`) so the change set, the review panel ("Stamp description"), undo and the `localStorage` draft carry it with no new machinery, and moving the selection does not lose what was typed. `quietCell` stops the pane and the undo from pushing history, and the base comes from `previewStart` on focus because `cell.getOldValue()` is the page-load value. Both modes, pane stacks under the grid below 1100px. Two older bugs found in the check: `mode=new` painted nothing at all (`setData` in the same tick as Tabulator's build → `verticalFillMode` crash; waits for `tableBuilt` now, reproduced with `HEAD`'s JS) and `?rows=N` is never read by the view. 493 datadesk / 1509 backend; Chromium at 1366 and 1024.
- [Today] DataDesk S22 and the plan closed: `/`, `j`/`k` and `N` finish the keyboard contract with a line under each grid saying what it understands; `↺ Use last issue` names the values it would write and disables itself when the form already has them (the S11 follow-up); a test walks the scripts and fails on prose where text is painted; `--dd-soft` moved from 2.6:1 to 4.8:1 and focus is visible on links, buttons and summaries; sorting by date got the two tests that were missing; the README documents the keys, the backup, turning the flag off and what a revert cannot restore. 3 tests; 441 datadesk / 1457 backend; harnesses 79/74/14/6 checks.
- [Today] DataDesk S21: the audit trail gets a screen and an undo. `/datadesk/activity/` pages by commit (never by row), shows the changed columns per object and a state badge; `POST activity/<id>/revert` undoes the whole commit in one transaction with the ordering that makes it work (recreate parents first, delete children first), restores ids, FKs and colours, sets `updated_at` by hand after an `update()` because `auto_now` does not fire, refuses merges / already-reverted / objects that moved / id collisions, and writes itself as a new commit with `reverts_commit_id` plus `reverted_at` on the originals. Refusals re-render the page with the reason; success redirects with a banner. 30 tests; 438 datadesk / 1454 backend.
- [Today] DataDesk S20: the dashboard replaces the placeholder page — six cards, one per counter, each opening the workbench with its filter; stamp-level cards say how many series hold those stamps, and that number is the grid's own query. `service.QUEUES` maps counter → filter → label → unit and a test checks it both ways. On the way it fixed a real bug: `stamps_without_image` filtered on `Stamp.image` (empty everywhere) and matched 2.542 of 2.543 series against a counter of 1.177; now both use `picture_gaps()` (28 ms, 1.177 stamps in 1.044 series). 19 tests; 408 datadesk / 1424 backend.
- [Today] DataDesk S19: the eight reference tables get one screen and one grid — `/datadesk/lookups/` lists them with their size, `/datadesk/lookups/<key>/` shows usage annotated (`Count` per relation, two queries per page), inline rename whose duplicate answers 409 with the other row's id and opens the merge pre-filled, a transactional merge with `keep_name_from` (FK `update()` + explicit `updated_at`, colours through the junction table with `ignore_conflicts`, years move their series) that writes one `merge` audit row and cannot be undone, a delete only on rows nobody points at, and `Create the next 10 years`. Envelope and plurals moved to shared modules. 40 tests; 389 datadesk / 1405 backend.
- [Today] DataDesk S18: the strip's six lookups became typed fields with a datalist fed by `lookups/<key>/search` (50 rows, no table in the page) and a `+ Crear "X"` that only appears for an unknown name; ids stay the language of the form through two maps that also travel in the draft, an unresolved name blocks the commit instead of silently clearing the FK, and a created row is written at once so the review panel lists it as already saved. Colours get `New colour` in the grid toolbar and the create answers with the palette tone. 21 tests; 349 datadesk / 1365 backend; harness 73 new-mode + 74 edit-mode checks.
- [Today] DataDesk S17: cloning copies rows instead of re-entering them (`_copy_fields()` reads attnames, gaps travel, `year`/`date` overridable, `cloned_from` on the series' audit row only), and deleting is a preview plus a typed year checked in the transaction, which recounts there instead of trusting the dialog and audits one `delete` row per stamp with its full `before` for S21. `Clone`/`Delete` live in the strip of `mode=edit`, disabled while the buffer has edits, and the dialog shows the three counts and closes with `Esc`. 38 tests; 328 datadesk / 1344 backend; harness 62 edit-mode + 57 new-mode checks.
- [Today] DataDesk S16 (third milestone): `mode=new` writes. Create posts series + rows to `/datadesk/issues/create` (one transaction), empty untouched rows are dropped, `Shift+Enter` creates. After a clean create the strip and grid are hidden and the bar offers Open / `Create another in <year>`; the loop is a server-rendered `/datadesk/issues/new/?from=<pk>` — the browser still stores no draft — that repeats classification and perforation but clears name, date, print run, values and text. `Fill series` advances the letter (`2744a→2744b`, `z→aa`) or the number keeping padding, `Ctrl+D` duplicates under the cursor, TSV paste fills the visible columns from the caret, fast row (on) keeps the four typing columns, and colours gain a `list` multi-select editor in new mode only. 285 datadesk / 1301 backend tests; jsdom harness new mode 37 checks + edit mode 42.
- [Today] S16 after the first real use: rows can be removed from a draft (a `×` column whose deletion is a history entry, so `Ctrl+Z` restores the row and its place), colour cells paint one chip plus `+N` with the whole list in the title (a clipped cell said "..." and hid the only information it had), and `Fill series` numbers Edifil and Fesofi each from its own first code — both planned before any is written, an empty column skipped, a stuck one named in the message.
- [Today] S16 dates: a `mode=new` series of the current year opens with today's date, and the year follows the date and is read-only while a date is set — clearing the date hands the year back, so a year-only series is still possible. An older series starts undated on purpose (inventing a 1987 day is worse than a blank). The date carries the same 1800..year+2 bounds as the year. Consequence accepted: `↺ Use last issue` only changes the country when a date is set.
- [Today] S16 refusals point at the field: `dd-input-invalid` on the strip controls the server named (first one focused and scrolled into view, the whole-form ring only as a fallback), `dd-cell-invalid` on the exact grid cell, and the fast row switches off when the refused column was one it hides. Marks clear on the next edit of that field or on a retry. 290 datadesk / 1306 backend tests; harness 57 new-mode + 42 edit-mode checks.
- [Today] DataDesk S15: review panel (side drawer, grouped by model, `before → after` with server-provided field labels) with `Commit N changes` / `Ctrl+Enter` and `Discard` moved into it; the footer keeps Undo/Redo and opens it. Clean commit → workbench with `?focus=<id>`, page resolved by `page_of_issue()` over pks and the row selected/scrolled once. Partial rejection keeps the rejected rows with their message and opens the panel. `POST /datadesk/backup` runs `stamps_db_backup` (mode `stamps`) with a generated name, offered past 20 changes, never blocking the commit. Harness at 42 checks and it earned its keep: `refusal()` was receiving the errors object instead of the response body, so every refusal showed the generic text. 269 datadesk / 1285 backend tests green.
- [Today] Stamp pictures all showed `no_stamp.webp` after the rebuild — not an S13/S14 regression: with docker-outside-of-docker the bind source resolves on the host, where the workspace lives at a different path, so `../frontend/assets/stamps` became an empty directory with no error. `backend/docker-compose.dev.yml` now interpolates `${STAMP_IMAGES_DIR:-...}` and `stamps.sh` derives the host path from its own container's workspace mount; `images._scan()` warns when the folder is empty. Verified: 6.625 pairs indexed, 1.177 of 9.558 stamps without a picture. 1271 backend tests green.
- [Today] DataDesk S14: the grid stopped committing per row — edits buffer in the browser (one entry per object, diff against the loaded value, entries vanish when a field returns to its original). Footer with the field count, Undo/Redo/Discard/Save changes; undo is a value log with truncated redo; `Ctrl+Z` defers to the browser inside the strip's text fields. Draft in `localStorage` per issue with `schemaVersion`, offered on return and never auto-restored (`persist()` specifically does not delete a draft that is still being offered); `mode=new` persists nothing but keeps an in-memory undo. `storage` event → "another tab" banner. Plurals via `ngettext` and the i18n test now understands `msgstr_plural`. Kept "Save changes" (batch) so the step stays usable — S15 adds the review panel in front of it. Verified with a throwaway jsdom harness (33 checks, not committed: no Node in the repo). 254 datadesk / 1270 backend tests green.
- [Today] DataDesk S13 (second milestone): the strip became a form sharing S11's 15 field definitions and the grid got editors on the fields a stamp owns. `Shift+Enter`/Save commits one row to `/apply` after blurring the open editor (Tabulator only writes the typed value on blur); `updated_at` travels as row data and `/apply` now returns `data.rows [{index, id, updated_at}]` so the baseline moves without a reload. Refusal reverts the cell and marks the row red; the strip keeps what was typed. `Esc` blurs a field instead of leaving. The strip no longer formats by locale (inputs show stored values) — `issue_metadata()`, `_display()` and the formatting tests are gone; S22 owns a read-only view. 14 tests; 1262 backend tests green.
- [Today] DataDesk S12: write core — `create_series()` (all or nothing), `apply_changes()` (savepoint per row, `select_for_update()` before the conflict check) and `create_lookup()`, behind three plain JSON endpoints. Decisions: typed year resolved with `get_or_create` and not audited, colours applied with one `set()` outside the serializer, `delete` → 409, partial rejection → 200 with `{index, errors}`, messages stay English until the screens translate them, and no repo-wide `black` (the repo is not black-clean; the cosmetic reformat of `workspace.py` was reverted). 56 tests; 1250 backend tests green.
- [Today] Devcontainer: `opencode upgrade --major` in `setup.sh` replaced by `curl -fsSL https://opencode.ai/v2/install | bash -s -- --version 2.3.2`. `/install` only serves 1.x and refuses 2.x, so 1.x's major upgrade re-ran an installer that rejects the target — not a missing flag. Version is pinned now, so a rebuild cannot swap the agent underneath a session.
- [Today] DataDesk S11: `/datadesk/issues/new/` in dry mode — the series form, `rows=N` (4 default, 1–100, only appends or trims untouched trailing rows), client-side `new-<n>` rows with `touched` following the series name, `↺ Use last issue` reapplying only `country`+`year`, `beforeunload` only when dirty, inert `Shift+Enter` with a fixed notice. Decisions D1–D5 written into the plan, S16's stale "editable inheritance" bullet corrected. 23 tests; 1189 backend tests green.
- [Today] DataDesk S10b: thumbnails from the mounted `<year>/<code>.webp` tree (88% coverage) behind a staff-gated image view with ETag, coloured chips from `palette.py`, inline SVG chevron + double-click to open, and inheritance shown as a tinted cell with an inner bar plus a plain hint under the strip. Queue cost fixed: 11.5 s → 36 ms after passing the cached index to bulk callers. 30 tests; 1167 backend tests green.
- [Today] DataDesk S10: read-only issue workspace at `/datadesk/issues/<id>/` — series strip formatted by locale, stamp grid with server-resolved inheritance (`inherited: {field: bool}`), `↗` link and `Enter` from the workbench, `Esc` back with filters. Fixed `<html lang>` (always said `en`). Measured: 57-stamp series in 14 ms with 3 queries. 21 tests; 1137 backend tests green.
- [Today] DataDesk S9: measured the read layer on the real data and wrote `memory-bank/datadesk-perf.md`. Verdict: **no index** — the page cost is planning (42 ms) not scanning (24 ms), `icontains` cannot use a btree, the year filter already uses the FK index, and the stamp queues are cheap semi joins. Worst p95 84 ms; queries stay at 2 for any `size`. Longest real series is 57 stamps (not 24), so S10's acceptance was corrected.
- [Today] Stamp color selection UX: replaced nested modal dialog color picker in `StampForm` with an inline Material 3 multi-select dropdown and removable chips. Fixed overlay position (`BOTTOM_LEFT`, height `200`). Updated `stamp_form.py` and `test_stamp_form.py`. All 651 frontend tests passing.
- [Today] Normal User Collections Planning: Generated 3 UI mockup screens, designed hierarchical card structure (`Collection` → `Issues` → `Stamps`), designed catalog browser with "Select All in Series" feature, and saved full plan to `memory-bank/user-collections-plan.md` and mockups to `memory-bank/mockups/`.