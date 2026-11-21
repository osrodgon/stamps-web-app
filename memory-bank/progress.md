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
- [x] **S4 — i18n en/es** (2026-11-18): `.po` catalogs in `backend/datadesk/locale/`
      (en + es) compiled to `.mo` by `datadesk_make_messages` (polib, no `gettext`
      needed, `--check` for CI), `LocaleMiddleware` + `DATADESK_LANGUAGES`, and the
      EN/ES control in the topbar as a POST form hitting `/datadesk/language/`.
      Templates now use `{% translate %}`; the frontend `assets/locales/*.json` are
      untouched. 13 tests; 1053 backend tests green. Next: S5 (`updated_at`)
- [x] **S5 — `updated_at` on Issue and Stamp** (2026-11-18): `auto_now=True,
      null=True, db_index=True` in both models, migrations generated locally
      (`migrations/` is gitignored, CI builds the test schema from the models),
      `exclude = ["updated_at"]` in both response serializers (public API and
      OpenAPI schema unchanged), and `ModelAdmin` with `readonly_fields`. Verified
      on a scratch database: `migrate` applies and reverses, `loaddata` of the July
      backup installs 12.763 objects with the column NULL, and a later `save()`
      moves it. 8 tests; 1062 backend tests green.
      Next: S6 (`DataDeskChange` + audit writer)
- [x] **S6 — `DataDeskChange` + audit writer** (2026-11-18): `datadesk/models.py`
      with `commit_id`/`user`/`model_label`/`object_id`/`operation`/`before`/`after`
      plus `reverted_at` and `reverts_commit_id` for S21; `datadesk/audit.py` with
      `snapshot()` (attname keys so `Model(**snapshot)` rebuilds the row, `Decimal`
      as string, ISO dates, M2M as sorted ids) and `record()` (validates the
      operation, stores anonymous actors as NULL); read-only admin. 14 tests;
      1076 backend tests green. Next: S7 (lookup registry + read querysets)
- [x] **S7 — Lookup registry + read querysets** (2026-11-18): `datadesk/registry.py`
      with the 8 editable lookups (model, translatable label, name column, numeric
      flag, incoming refs for S19) and `datadesk/service.py` with
      `issue_queryset()` (7 `select_related` + `Count("stamps")`, order year / date
      nulls-last / name, 1 query), `stamp_queryset()` (2 queries with colors) and
      `missing_data_report()` (6 counters; `face_value` checked as `""` because the
      column is NOT NULL). Registry labels translated in both catalogs. 12 tests;
      1088 backend tests green. Next: S8 (read-only workbench, first milestone)
- [x] **S8 — Read-only workbench** (2026-11-18, first milestone): `GET
      /datadesk/grid/issues` (flat filters, `sort[0][field]`, page/size capped at
      200, decimals as strings, `last_page`/`total`/`data`) and `GET
      /datadesk/issues/` with year range, 300 ms debounced search, country, stamp
      type and the six "needs attention" filters. Filters live in the URL, the
      column choice in `localStorage`, column titles are rendered by Django as
      JSON so the JS holds no UI text. Gap badge from the row itself, no extra
      queries. Measured on the real data: 100-row page in **138 ms**. 27 tests;
      1115 backend tests green. Next: S9 (perf check on the real dataset + indexes)
- [x] **S9 — Performance check and indexes** (2026-11-18): measured on the real
      data (2.540 issues / 9.558 stamps, longest series 57 stamps) — first page
      68 ms, last page 67 ms (no OFFSET degradation), year filter 44 ms, name
      search 35 ms, worst queue `stamps_without_colors` 82 ms; p95 under 300 ms
      everywhere, 2 queries at any page size. `Planning Time` (42 ms) beats
      `Execution Time` (24 ms), so the cost is planning the 8-table join, not
      scanning. **No index added**: `icontains` compiles to
      `UPPER(name) LIKE UPPER('%q%')` (a btree is useless, would need `pg_trgm`
      + GIN), the year filter already uses the FK index, and the stamp-level
      queues are semi joins over 9.558 rows. Numbers and the rejected
      candidates written to `memory-bank/datadesk-perf.md`; one test fixes the
      query count. 100 datadesk tests green. Next: S10 (workspace `mode=edit`)
- [x] **S10 — Read-only issue workspace** (2026-11-18): `GET
      /datadesk/issues/<id>/` renders the series strip (15 fields, formatted by
      locale) and its stamps; the workbench opens it from a per-row `↗` link or
      `Enter`, and `Esc` returns with the filters intact. Rows travel in the
      page (no second
      endpoint); grid does not paginate (57 stamps is the real ceiling). Fixed
      `<html lang>` (it always said `en` because `LANGUAGE_CODE` is not in the
      context). Measured: 57-stamp series in 14 ms, 3 queries, 28 KB. 21 tests;
      1137 backend tests green. Next: S11 (`mode=new`, dry, nothing saved)
- [x] **S10b — Workspace polish** (2026-11-18): stamp thumbnails from the
      mounted `<year>/<code>.webp` tree (8.419 of 9.558 stamps, 88%), served by
      a staff-gated `/datadesk/stamps/<id>/image` with ETag and private cache;
      the folder is a read-only bind (dev compose; prod defines its own mount in the
      single deployment compose), so adding a picture needs no rebuild. The listing is
      cached 60 s and passed to bulk callers, which took the "without image"
      queue from 11.5 s (one file-cache read per stamp) to 36 ms. Colour chips
      now carry a tone derived from the name (`palette.py`, Spanish keyword
      stems + stable md5 fallback); the open icon is an inline SVG chevron with
      double-click on the row. **The inheritance concept was removed entirely**
      after review: name, market values and print run belong to the stamp or to
      the set, never shared, so the `inherited` map, the tint, the legend and the
      ⟲ markers are gone; the strip keeps a one-line note that series values
      describe the whole set. `missing_data_report()` counts missing picture
      files, not the empty `Stamp.image`. 33 tests; 1170 backend tests green.
- [x] **S11 — `mode=new` en seco** (2026-11-19): `GET /datadesk/issues/new/`
      on the same template with `mode="new"` and the series form (15 fields);
      prefill of **`country` + `year` only** from the highest id, re-applied by
      `↺ Use last issue` from the page config; `rows=N` 1–100 (default 4) that
      appends and trims only untouched trailing rows; client rows `new-<n>` with
      `touched: false` following the series name until edited; `beforeunload`
      only when the form or the row set changed; inert `Shift+Enter` with a fixed
      notice; detail route switched to `int:` so `new` cannot be an id; the year
      is typed (`input[type=number]` + datalist) because a series usually
      opens a new year. 28 tests; 1194 backend tests green. Next: S12 (write
      core, no UI)
- [ ] **S11 follow-up — the prefill button looks dead**: `↺ Use last issue` only
      acts on `country` and `year`, which already hold those values on load, so
      clicking does nothing visible until one of them is changed. Label it with
      what it will set (`España · 1987`), disable it while nothing differs and
      flash the two controls on apply
- [x] **S12 — Write core** (2026-11-19): `datadesk/write.py` with
      `create_series()` (series + nested stamps, one transaction, all or nothing),
      `apply_changes()` (`create`/`update`, savepoint per row, `select_for_update()`
      before the `expected_updated_at` check) and `create_lookup()`
      (`get_or_create`, duplicate → `created: false`), plus
      `datadesk/views/write_api.py` for `POST issues/create`, `apply` and
      `lookups/<key>/create`. `year` arrives as a number and is resolved with
      `get_or_create` (the implicit `Year` is not audited); colours leave the
      serializer because DRF refuses an empty list and a colourless stamp is a
      gap, not an error; `""` on a nullable column becomes `None`; `image` is
      read-only; `delete` answers 409 `{needs_confirmation: true}`; 500 changes
      cap; one `commit_id` per request. Year bounds moved to `datadesk/rules.py`
      so form and writer cannot drift; `IssueCreateView` renamed `IssueNewView`.
      56 tests (38 writer + 18 HTTP); 1250 backend tests green. Next: S13
      (single-row commit from the grid)
- [x] **S13 — Single-row commit from the grid** (2026-11-19, second milestone):
      the series strip is now a form (same 15 fields and definitions as S11) and
      the stamp grid has editors on the columns a stamp owns (`patch` in the
      column definition). `Shift+Enter` — or the Save button — commits **one**
      row to `/datadesk/apply`: the open editor is blurred first so Tabulator has
      already written the typed value into the row. `updated_at` travels as row
      data (not a column) and `/apply` returns `data.rows [{index, id,
      updated_at}]`, so the new baseline comes back without a reload. A refusal
      reverts the cell and marks the row red with the server's message; the strip
      keeps what was typed. `Esc` blurs a focused field instead of leaving.
      Consequence: the strip no longer formats numbers/dates by locale — inputs
      show the stored value; `issue_metadata()`, `_display()` and the formatting
      tests are gone (S22 owns a read-only view). 14 tests; 1262 backend tests
      green. **Fix from the first real use**: Save answered "nothing changed"
      on the strip because the click moved the focus out of the form before the
      target was decided; the target now falls back to "the strip is dirty" and
      the strip reports its unsaved state while typing.
- [x] **S14 — Client change set, footer, undo, draft recovery** (2026-11-19):
      edits accumulate in the browser instead of being sent one row at a time:
      one entry per object with `patch`/`base`/`expected_updated_at`, the diff
      recomputed against the value the page loaded, and an entry that disappears
      when a field returns to its original value. Footer with the count (fields,
      not objects), Undo/Redo/Discard/Save changes, `Shift+Enter` commits the
      buffer. Undo/redo is a log of values (200 ops) with redo truncated on a
      new edit; `Ctrl+Z` yields to the browser inside the strip's text fields.
      Draft in `localStorage` (`datadesk:buffer:edit:<id>`, `schemaVersion`,
      400 ms debounce), offered on return and never auto-restored; `mode=new`
      persists nothing and keeps its undo in memory. A `storage` event shows the
      "another tab" banner without blocking. Plurals resolved server-side with
      `ngettext`. Kept a batch "Save changes" because a step must leave the app
      usable: S15 puts the review panel in front of it. Supersedes S13's
      single-row commit. 9 tests added; 254 datadesk and 1270 backend tests
      green, plus a throwaway jsdom harness (33 checks) for the browser logic.
- [x] **S15 — Review panel + batch commit + pre-commit backup** (2026-11-19):
      a side drawer (hidden by default, `Review changes` in the footer) lists the
      change set grouped by model with `before → after` per field and the field
      names translated by the server (`fieldLabels` built from the same
      definitions the editor uses). `Commit N changes` (`Ctrl+Enter`, and
      `Shift+Enter` stays) posts the whole set: applied rows leave the buffer,
      rejected ones **stay** with their message on the entry and open the panel.
      A clean commit redirects to the workbench with `?focus=<id>`; the page is
      resolved server-side by `page_of_issue()` (over pks, not the grid join) and
      the grid selects and scrolls to the row once. `POST /datadesk/backup` runs
      the existing `stamps_db_backup` command (mode `stamps`) and names the dump;
      the button appears past 20 changes and a failing backup never blocks the
      commit. 14 tests added; 269 datadesk and 1285 backend tests green; the jsdom
      harness is at 42 checks and caught a real bug (`refusal()` was given the
      errors object instead of the response body, so every refusal showed the
      generic text).
- [x] **S16 — `mode=new` completo** (2026-11-19, third milestone): the form
      writes. Create posts the series and its rows to `/datadesk/issues/create`
      in one transaction; empty rows are dropped so `rows=4` does not force four
      stamps; `Shift+Enter` creates too. After a clean create the workspace stops
      editing (fields and grid hidden) and offers `Open the series` plus
      `Create another in <year>`, which is `/datadesk/issues/new/?from=<pk>` —
      the server pre-fills the form, so `mode=new` still stores nothing in
      `localStorage`. The loop repeats the classification and perforation of the
      series just written but clears name, date, print run, market values and
      free text. `Fill series` moves the letter (`2744a → 2744b`) or the number
      (`0069 → 0070`) and refuses a first code with no digits; `Ctrl+D`
      duplicates the row under the cursor; a TSV paste fills the visible
      columns from the caret. Fast row (on by default) keeps edifil, fesofi,
      face value and colours. The colours get their `list` multi-select editor
      in new mode only (`autocomplete` disables `multiselect` in Tabulator 6).
      15 tests added; 285 datadesk and 1301 backend tests green; new-mode jsdom
      harness at 37 checks. First real use added three fixes: a `×` column to
      remove a row (undoable with `Ctrl+Z`, since the row and its position go
      into the history), colour cells that paint one chip plus `+N` and keep the
      full list in the title instead of being cut, and `Fill series` numbering
      Edifil and Fesofi together — each column planned before any is written, an
      empty one skipped and a stuck one named. A refusal now also rings the
      field or the cell the server named (and turns the fast row off if that
      column was hidden), not just the whole form or row; the mark clears on the
      next edit. A new series of the current year now starts dated today and the
      year follows the date (read-only while a date is set, freed when it is
      cleared); an older series still starts undated rather than inventing a
      day. 5 tests added; 290 datadesk and 1306 backend tests green.
- [x] **S17 — Clone a series and delete one with a dependency preview**
      (2026-11-19): `datadesk/dependencies.py` counts what a deletion takes with
      it (stamps, `CollectionItem` rows, distinct user collections) and words the
      warning in three cases, no numbers and therefore no plurals;
      `clone_series()` copies rows instead of re-entering them, so a series with
      gaps clones as it is, keeps its colours and codes, accepts `year`/`date`
      overrides and records `cloned_from` on the series' audit row;
      `delete_series()` locks the series, checks the typed year itself, recounts
      inside the transaction and writes one `delete` row per stamp plus the
      series with the full `before` S21 needs. Endpoints: `POST
      /datadesk/issues/<pk>/clone` (answers the copy's URL), `GET
      /datadesk/issues/<pk>/dependencies` and `POST
      /datadesk/issues/<pk>/delete`. The workspace strip gains `Clone` and
      `Delete`, both disabled while the change set has edits, and the delete
      dialog shows the three numbers plus the year box (Esc closes it without
      leaving). 38 tests; 328 datadesk and 1344 backend tests green; the jsdom
      harness is at 62 edit-mode checks.
- [x] **S18 — Create a lookup from the workspace** (2026-11-19): the six
      reference fields of the strip stopped being selects — the page shipped the
      whole artist and colour tables with every series — and became typed fields
      that search `/datadesk/lookups/<key>/search?q=` (50 rows, `icontains` over
      the name column) with a `+ Crear "X"` button that appears only when the
      text is not a known row. The form keeps speaking ids: two maps translate
      between the name on screen and the id the API takes, seeded from the page
      and grown by searches and creations, and they travel in the `localStorage`
      draft so a restored change shows a name and undoes into one. A typed name
      with no row behind it blocks the commit with a message instead of clearing
      the field. A created row is written immediately (no temporary ids), so in
      `mode=edit` it is not a change: the review panel lists it in its own group
      as already saved. Colours get `New colour` in the grid toolbar (the
      Tabulator list editor takes no free text) and the create response carries
      the palette tone. 21 tests; 349 datadesk and 1365 backend tests green;
      jsdom harness at 73 (new) and 74 (edit) checks.
- [x] **S19 — Lookups screen, usage counts and merge** (2026-11-19):
      `/datadesk/lookups/` lists the eight reference tables with their size and
      `/datadesk/lookups/<key>/` is one grid for all of them: usage annotated with
      a `Count` per relation (accessor derived from the model field, `distinct`,
      two queries per page — never one per row), inline rename that answers 409
      `duplicate_name` with the id of the row that already has it and opens the
      merge, merge that moves references in one transaction (FK `update()` with an
      explicit `updated_at` because `auto_now` does not fire on `update()`; M2M
      through `bulk_create(ignore_conflicts=True)` + delete of the source rows so
      a stamp holding both colours ends with one; years move their series instead
      of cascading) with `keep_name_from` choosing which name survives, and a
      delete only when usage is 0 (otherwise 409 `in_use` with the count). One
      `operation="merge"` audit row with both counts; the dialog says the merge
      cannot be undone (S21 will refuse it). `Create the next 10 years` for the
      years. The JSON envelope moved to `datadesk/views/envelope.py` and the
      plurals to `datadesk/texts.py`, now shared with the workspace. 40 tests;
      389 datadesk and 1405 backend tests green.
- [x] **S20 — Dashboard and the "needs attention" queues** (2026-11-19):
      `/datadesk/` shows the six counters as cards that open the workbench with
      the filter already applied; the stamp-level ones carry the series count too
      ("1.177 · in 1.044 series") because the grid behind them counts series, and
      that number comes from `filter_issues()`, the same query the grid uses. One
      table (`service.QUEUES`) maps counter → filter → label → unit, checked both
      ways by a test so a new counter cannot be missing from the dashboard;
      counters at zero are listed apart instead of looking like work; numbers are
      grouped by the active language. **Bug fixed on the way**: the workbench's
      `stamps_without_image` filter still read `Stamp.image` (empty in all 9.560
      real rows) and matched 2.542 of 2.543 series while the counter said 1.177;
      both now come from `picture_gaps()`, one walk of the image index (1.177
      stamps in 1.044 series, 28 ms with the cache warm). 19 tests; 408 datadesk
      and 1424 backend tests green.
- [x] **S21 — Activity log and reverting a commit** (2026-11-19):
      `/datadesk/activity/` lists the commits newest first, paginated **by
      commit** (a batch of forty rows is one decision), with who, how many
      objects, each row's operation and the columns that changed, and a state
      badge (reversible / not revertible: it contains a merge / reverted on …).
      `POST /datadesk/activity/<id>/revert` undoes the whole commit in one
      transaction: creations are deleted children-first, updates get their full
      `before` written back with an explicit `updated_at`, deletions are
      recreated with their original ids, foreign keys and colours, and a merge is
      refused. Refusals (already reverted, merge, object changed after the
      commit, id or name collision) answer 409 and re-render the page with the
      reason; success redirects with a banner. The revert is itself a commit
      (`reverts_commit_id`) and the original rows get `reverted_at`. The dialog
      warns that the `CollectionItem` rows the cascade removed do not come back.
      30 tests; 438 datadesk and 1454 backend tests green.
- [x] **S22 — Close-out: keyboard, i18n, accessibility, tests, README**
      (2026-11-19): `/` focuses the search (workbench and lookup tables), `j`/`k`
      move the selection and `N` starts a new series, next to the keys that
      already existed; no shortcut fires while a control has the focus, and each
      grid says underneath what it understands. `↺ Use last issue` now names the
      values it would set (`España · 1987`), is disabled while the form already
      holds them and flashes the fields it writes — the S11 follow-up. A test
      walks `datadesk/static/datadesk/*.js` and fails on prose in the places
      that paint text (glyphs are allowed by definition), and `--dd-soft` went
      from 2.6:1 to 4.8:1 because the muted text was the one failing AA, with
      `:focus-visible` on links, buttons and `summary`. The last coverage gap in
      `service.py` (sorting by date, both directions, nulls last) is tested, which
      leaves that module at 100% and `datadesk` at 98%. The
      repo README gained the keyboard table, the pre-commit backup, how to turn
      DataDesk off and what a revert cannot restore. 3 tests added; 441 datadesk
      and 1457 backend tests green; jsdom harnesses at 79 (new), 74 (edit), 14
      (workbench keys) and 6 (lookup keys) checks. **DataDesk is complete.**
- [x] **S23 — The refused cell's ring is hidden by the next row** (2026-11-19):
      the mark is painted with `box-shadow: inset` and Tabulator paints the rows
      in order, so the one below covered the bottom pixel of the ring. The cell
      now carries `position: relative` + `z-index: 2` (3 inside a refused row):
      rows are positioned without a z-index, so they create no stacking context
      and the cell lifts above the next one. An `outline` was rejected — it is
      painted with the cell and gets covered the same way. Two tests pin the
      declaration so a tidy-up cannot remove it. 443 datadesk and 1459 backend
      tests green.
- [x] **S24 — Type scale and rhythm** (2026-11-19): six tokens (22 / 16 / 14 /
      13 / 12 / 11 px) and **all 52 `font-size` rules now go through them** — the
      stylesheet used to declare `--dd-base-size` and then hardcode twelve,
      twelve-and-a-half and nine-and-a-half everywhere. Body 14/1.5, grid 13 with
      36 px rows and 7/10 cells, topbar 48, the current screen as the title at
      16 px, page card flatter. The biggest change is not the size: the grid
      stopped wearing Tabulator's chrome (`1px solid #aaa` cells, `#efefef`
      zebra, `#9abcea` selection) and now uses `--tabulator-border`, a whisper of
      zebra and a grey-blue selection. The commit bar and the workbench toolbar
      wrap instead of overflowing at 1366, the review panel is 380 px for the new
      text, and long series names truncate in the breadcrumb. Four tests keep the
      scale honest: no literal size, every size from a token, nothing below 11,
      and the body using `--dd-text`. Seen on a 2560 screen, the wider type had
      pushed the workbench into a horizontal scroll, so the same step also: raised
      the card's cap to 1600, moved the workbench and the lookups grid to
      `fitColumns` with a per-column `grow` (name 4, lookups 2, numbers 1, name
      `minWidth: 180`) so columns share the width instead of demanding it, added
      `text-decoration: none` to `.dd-btn` (an `<a>` styled as a button was
      underlined while a `<button>` was not) and dropped the two local patches
      S17 had left, plus `calc(100vh - 300px)` for the grid height. Then the
      buttons themselves: they were not the same height and an `<a>`-styled one
      had its label on the text baseline instead of centred — `.dd-btn` is now
      `inline-flex` with a centred label, a `min-height: 32px` and padding that
      only sets the sides, so the ghost variant tightening its padding no longer
      makes it shorter than the dark button next to it. 451 datadesk and 1467
      backend tests green.
- [x] **S25 — Delete a stamp with a dependency preview** (2026-11-19): the
      change set refuses `delete` on purpose (S12) and S17 only solved it for a
      series. `stamp_dependencies()` counts collection items, their collections
      and the sibling stamps; `stamp_warning()` words the four cases (held or
      not, last of the series or not); `delete_stamp()` writes one `delete` row
      with the full snapshot, which is what S21 uses to bring the stamp back with
      its id and colours — the `CollectionItem` rows do not come back and the
      dialog says so. Per-row `×` in `mode=edit` with its own preview dialog, no
      typed confirmation (one row is not a set), dimmed and refusing while the
      change set has edits. 20 tests; 471 datadesk and 1487 backend tests green;
      the edit-mode harness is at 89 checks.
- [x] **S26 — New row in the reference tables** (2026-11-19): rename, merge and
      delete existed; creation lived only in the workspace's `+`. `New row` and
      `N` open a one-field dialog that posts to the existing create endpoint
      (numeric with the workspace's year bounds for the years), a duplicate
      selects the row that already existed instead of failing, and the new row is
      revealed — selected and flashed — even when the sort put it on another
      page, by searching for it. 4 tests; 475 datadesk and 1491 backend tests
      green; the lookups harness is at 12 checks.
- [x] **S27 — Move between series and delete from the list** (2026-11-19):
      `issue_positions()` shares the pk list `page_of_issue()` already walked, so
      `neighbours_of_issue()` answers previous/next/position/total in the same
      query; the filters travel from the workbench in the `↗`/`Enter` link, come
      back in the arrows, the counter and **Back to the issues workbench**, and a
      series outside the filter falls back to the whole list instead of leaving
      dead arrows. `[`/`]` do the same from the keyboard, with a field guard. In
      the list, a `×` column opens the **same dialog** as the workspace — now a
      shared partial, with the preview and POST that already existed — a banner
      says what went and `Supr` only opens the dialog. Rows carry their two URLs
      in the grid JSON. 13 tests; 488 datadesk and 1504 backend tests green;
      harnesses at 23 (workbench), 89 (edit), 79 (new) and 12 (lookups) checks.
- [x] **S28 — Visual polish: typeface, controls, elevation** (2026-11-21): the
      five changes are in. Inter 4.001 self-hosted (the latin variable file Google
      Fonts serves, byte-identical to the mockup's, pinned with its real version
      and sha256); 34px controls with `--dd-line-strong`, hover and a soft ring;
      120ms motion with `prefers-reduced-motion`; a borderless card on
      `--dd-shadow-rest`, `--dd-shadow-float` for what floats and a **light grid
      header** with the selection marked by a 2px left bar; a 4px rhythm, 38px
      rows and tabular numbers. The `—` of an empty cell needed a formatter:
      Tabulator writes `&nbsp;`, so `:empty` never matched. Column minimums were
      added so no header truncates at 1440 (and "Total printed" became "Printed"
      on the header only, with a `label` key so the review panel keeps the full
      name). 6 new pins in `test_layout`; 524 datadesk and 1540 backend green;
      screenshots of every screen at 1440x900 and 1366x768.
- [x] **S28b — Five things the review found** (2026-11-21): the workbench date
      column shrank because its `buildColumn` never copied `width` (now a fixed
      112, with width support added); the shortcuts line had no margin (it is a
      direct child of a card with `padding: 0`); Tabulator's root is `#888` and
      only rows painted over it, which left a grey band under a short series
      (both grids now set a surface background); the series card painted square
      corners because its strip has a background (the strip and the commit bar are
      rounded instead of clipping the card, which cut 12px off the colour editor's
      dropdown); and the market values had no currency (`money` flag plus a
      formatter for "1.20 €", and a `unit` in the strip fields and the review
      labels); and the workbench's × of delete was not centred: it used a class
      with no box of its own, so a 16px glyph sat at the top of a 38px row. It
      now uses the same `.dd-remove` as the stamp's × (the whole cell), and the
      open chevron is centred with flex for the same reason. 2 tests; 526
      datadesk and 1542 backend green.
- [x] **S29 — See a stamp's picture and its description** (2026-11-21): the
      thumbnail was a colour swatch and `Stamp.description` was shown nowhere, so
      the series screen gained a **preview pane on the right of the grid** tied to
      the selected row — no hover, no click on the picture. Selection did not exist
      there (`j`/`k` were the workbench's), so S29 adds `selectableRows: 1` and
      `j`/`k`. The description is **not a visible column** (prose in a 13px cell is
      an ellipsis) but a **hidden one** with `patch: "description"`, which puts it
      in the change set, the review panel ("Stamp description") and the
      `localStorage` draft with no new machinery; changing stamp does not lose what
      was typed. The pane writes with `quietCell` and undo does too, so a keystroke
      is not an undo step and undo no longer re-arms itself; the base comes from
      `previewStart` (value on focus), not `cell.getOldValue()`, which is the one
      from page load. It works in both modes, the pane stacks under the grid below
      1100px, and the S/M/L size selector is deliberately left out. 5 tests; 493
      datadesk and 1509 backend green. **Two older bugs found on the way**:
      `mode=new` painted no rows at all (`setData` in the same tick as Tabulator's
      build → `verticalFillMode` crash; now waits for `tableBuilt`, reproduced with
      `HEAD`'s JS too), and `?rows=N` is not read by the view at all
      (`NewRowSettings()` takes no argument), see known gaps.
- [x] **S30 — "See affected series" from a reference table** (2026-11-21): the
      usage number is a link to the workbench with that filter, above zero only, and
      the list says why it is filtered with one chip per active filter and a "clear
      all". Five filters added (`printer`, `artist`, `paper_type`, `print_type`,
      `color`); the four are series columns and the colour is `Exists`, **not** the
      `stamps__colors` + `distinct` the plan said: a join multiplies rows and
      inflates `Count("stamps")`, and a test with a two-colour stamp pins it. The
      link counts **series** (`Count("stamps__issue", distinct=True)` annotated in
      the same query) and the cell title still says the stamps when the two numbers
      differ; a year links with `year_min` + `year_max` because `Year.pk` is not the
      year. The chips are painted in the script from the form — the page reloads the
      grid without reloading itself, so server-rendered chips went stale the moment
      a filter was set from the bar (seen in the browser). `filters_from()` is now
      one function shared by the page and the grid endpoint; before, the endpoint had
      its own copy and the new filters would have stopped at the page. 16 tests; 509
      datadesk and 1525 backend green; checked in Chromium (link → 1 series + chip →
      back to 2.542; colour 40 series vs 50 stamps; chip appears without reload).
- [x] **S30b — The workbench fits the window again** (2026-11-21, found the same
      day by using it): the five new selects made the bar four rows tall (193px)
      and the grid kept `height: calc(100vh - 300px)`, a number S24 tuned to a
      two-row bar — at 1440×900 the pagination footer sat at y=899, outside the
      window. The card is now a column as tall as the window and the grid takes
      what the filters leave (`flex: 1` + `height: "100%"`), so the footer is
      always inside, closed (104px), open (221px) or with chips; checked at
      1440×900, 1366×768 and 1366×600. The empty chips strip also kept 17px
      because `display: flex` beat the `hidden` attribute: a global
      `[hidden] { display: none !important }` fixes it everywhere (dialogs and the
      review panel checked). The five new selects moved behind a "More filters"
      `<details>` that opens itself when one of them filters, so the bar is back to
      its old height. And the scare: "the filters don't work" was the previous
      `workbench.js` in the browser — the selects come from the template, the
      filtering from the script, so the page showed the new filters and filtered
      nothing while the URL was right. DataDesk's assets now carry `?v=` with the
      newest asset's mtime (`datadesk/context.py`), so the browser asks again when
      they change. 8 tests; 517 datadesk and 1533 backend green.
- [x] **S30c — The CI caught a `reverse` in the service layer** (2026-11-21):
      `lookup_page()` built each row's `filter_url` with
      `reverse("datadesk:issues")`, which only exists with the app mounted; in CI
      (`DATADESK_ENABLED` off) the fourteen tests that call the service directly
      died with `NoReverseMatch`, and locally `.env` hid it by leaving the app on.
      The service now returns `filter: {...}` and `views/lookups.py` composes the
      URL (`with_filter_url()`), where the namespace is guaranteed; `pytest.ini`
      pins `DATADESK_ENABLED=False` so the suite is CI-shaped by default. 1 test
      added for the endpoint contract; 518 datadesk with the flag on, 1534 backend
      with it off.
- [ ] **S31 — Backups screen** (planned 2026-11-20): `POST /datadesk/backup`
      already runs `stamps_db_backup` in `stamps` mode (S15). What is missing is the
      place: list what is in `backups/`, run one with a mode, and download it. The
      dumps live inside the container (`BACKUP_DIR = BASE_DIR/backups`), so without
      download — or a volume in the production compose — they die on the next
      deploy. Real size: 11.6 MB / 12.763 objects for stamps, 24 KB / 126 for
      system.
- [ ] **S32 — Restore with maintenance, a prior dump and sequences** (planned
      2026-11-20): `stamps_db_restore` is `loaddata` and nothing else. It overwrites
      by PK but does **not** delete what the dump lacks, so newer rows survive;
      `stamps_clear_data` resets sequences to 1 and `loaddata` does not advance
      them, so chaining the two breaks the next insert (`duplicate key`) until
      `sqlsequencereset` runs. Any real restore is pre-restore dump → maintenance
      mode (503 for the rest of `/datadesk/`) → clear + loaddata + sequencereset,
      with a typed confirmation, and only `stamps`/`full` in the panel: `system`
      resurrects closed sessions and a revoked API key.

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
- [ ] DataDesk: a stamp's colours cannot be edited in `mode=edit` — the colour
      cell is read-only there because the change set carries no M2M. Colours are
      chosen when creating a series (S16) and created/merged from the lookups
      screen (S19); correcting one on an existing stamp still needs admin. This
      is the one gap left after S22 closed the plan.
- [ ] DataDesk: `?rows=N` on `mode=new` does nothing — `NewRowSettings()` is built
      with no arguments in `views/workspace.py`, so the control always shows 4.
      Found while checking S29; S11's acceptance said `rows=1–100` works, so either
      the parameter was never wired or it was lost. Fix is reading `rows` from
      `request.GET` and clamping it into the settings.

---

## Completed

### Devcontainer — docker without a nested engine (2026-11-19)

- [x] Recreating the container left `docker` unusable for two reasons: `setup.sh`
      installed an engine inside the container and added the user to the `docker`
      group at postCreate (the running session could not open the socket), and that
      nested engine had to run with `storage-driver: vfs` because overlayfs cannot
      back another overlay2 — so pulls and builds failed.
- [x] `devcontainer.json`: added
      `ghcr.io/devcontainers/features/docker-outside-of-docker:1`, dropped
      `--privileged` and the unused `--add-host`. `--network=stamps-network` and
      `initializeCommand` stay: they are exactly what the host-daemon setup needs.
- [x] `setup.sh`: removed `curl get.docker.com | sh`, `service docker start`, the
      `usermod` and the unrelated yarn apt source; pip and opencode remain.
- [x] `stamps.sh`: the socket guard reads `${DOCKER_HOST:-/var/run/docker.sock}` and
      only re-execs through `sg docker` when the socket exists but is not writable.
- [x] The hand-made `/etc/docker/daemon.json` (vfs) disappears with the container and
      is no longer needed. Rebuild is required so the feature mounts the host socket;
      the CLI then refreshes `devcontainer-lock.json` with the new digest (commit it).

### Devcontainer — stamp pictures were an empty mount (2026-11-19)

- [x] Every thumbnail showed `no_stamp.webp` after the container rebuild. Cause:
      with docker-outside-of-docker a bind source is resolved on the **host**, and
      the workspace lives there at `/home/oscarro/Development/stamps-web-app`
      while inside the devcontainer it is `/workspaces/stamps-web-app`. The
      relative source `../frontend/assets/stamps` did not exist on the host, so
      Docker created an **empty directory** with no error and the image index came
      back empty. Nothing to do with S13/S14.
- [x] `backend/docker-compose.dev.yml` interpolates
      `${STAMP_IMAGES_DIR:-../frontend/assets/stamps}` and `stamps.sh` exports the
      host path, derived by asking docker where its own container mounts the
      project root (skipped when the paths match, and an explicit
      `STAMP_IMAGES_DIR` wins). Documented in `backend/.env.example`.
- [x] `images._scan()` now warns when the folder exists but is empty, naming the
      silent-empty-mount cause instead of leaving it to a guess. One test.
- [x] Verified in the running container: mount source is the host path, 6.625
      picture pairs indexed, 1.177 of 9.558 stamps without a picture (the 88%
      coverage from S10b). 1271 backend tests green.

### Devcontainer — OpenCode 2 in `setup.sh` (2026-11-19)

- [x] `setup.sh` ended with `opencode upgrade --major`, which failed on every rebuild.
      Cause: `https://opencode.ai/install` only serves the 1.x channel (currently
      1.19.6) and its lines 70–74 **refuse** `>= 2.0`; 1.x's `upgrade --major`
      re-runs that same installer with `VERSION` set, so it hit the guard. The flag
      is not missing, the path is closed.
- [x] Replaced both lines by
      `curl -fsSL https://opencode.ai/v2/install | bash -s -- --version 2.3.2`.
      The v2 installer writes the same `~/.opencode/bin` (plus the `opencode2` shim
      it generates), checks the version exists for the target before downloading,
      and `--version` pins it — an agent that upgrades itself on every rebuild is
      how a session gets lost.
- [x] Verified in a throwaway `HOME`: exit 0 and `opencode v2.3.2`, so the pinned
      version and asset resolution are fine without touching the live binary.
- [x] From 2.x on, `opencode upgrade` has no `--major` (only a positional target and
      `--method`), so no upgrade step goes back into the postCreate.

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
      **nothing**: series values describe the set (print run, value of the complete
      series), so no field of a stamp is inherited; decided after S10b
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