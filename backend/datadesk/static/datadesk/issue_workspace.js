/* Issue workspace grid.
 *
 * One template, two modes. `edit` shows one series and its stamps and commits
 * one row at a time: Shift+Enter (or the Save button) sends the row being
 * edited to `/datadesk/apply`. `new` starts from blank rows that exist only in
 * this browser: no request, no database row, so reloading throws the draft away
 * on purpose.
 *
 * Titles, colours, picture URLs, the texts of the commit bar and even the
 * element ids come from the page configuration, so this file holds no interface
 * text and no DOM convention it was not told about.
 */
(() => {
  "use strict";

  const config = JSON.parse(
    document.getElementById("stamp-config").textContent
  );

  /** Keeps a number inside the bounds the server sent. */
  const clamp = (value, min, max) => Math.min(Math.max(value, min), max);

  /** Renders the colours as tinted chips. */
  const colorsFormatter = (cell) => {
    const colors = cell.getValue() || [];
    if (!colors.length) {
      return "";
    }
    const box = document.createElement("span");
    colors.forEach((color) => {
      const chip = document.createElement("span");
      chip.className = `dd-chip dd-chip-${color.tone}`;
      chip.textContent = color.name;
      box.append(chip);
    });
    return box;
  };

  /** The stamp's picture, or the "no picture" placeholder shipped with it. */
  const imageFormatter = (cell) => {
    const row = cell.getRow().getData();
    const picture = document.createElement("img");
    picture.className = row.image_url ? "dd-thumb" : "dd-thumb dd-thumb-missing";
    picture.src = row.image_url || config.fallbackImage;
    picture.alt = "";
    picture.loading = "lazy";
    return picture;
  };

  /** Builds one Tabulator column from the server-provided definition. */
  const buildColumn = (definition) => {
    const column = {
      field: definition.field,
      title: definition.title,
      headerSort: true,
      resizable: false,
    };
    if (definition.width) {
      column.width = definition.width;
    }
    if (definition.align) {
      column.hozAlign = definition.align;
    }
    if (definition.mono) {
      column.cssClass = "dd-mono";
    }
    if (definition.patch) {
      column.editor = definition.editor === "number" ? "number" : "input";
    }
    if (definition.field === "colors") {
      column.formatter = colorsFormatter;
    }
    if (definition.field === "has_image") {
      column.formatter = imageFormatter;
      column.headerSort = false;
      column.cssClass = "dd-image-cell";
    }
    return column;
  };

  const grid = new Tabulator("#stamp-grid", {
    data: config.data,
    columns: config.columns.map(buildColumn),
    layout: "fitColumns",
    height: false,
    placeholder: config.emptyText,
  });

  /* --------------------------------------------------------------------- *
   * mode=edit: a change set in the browser.
   *
   * Nothing is sent while typing: edits accumulate here and one request
   * commits them (S15 reviews them first). Ctrl+Z replays values, and the
   * draft survives a reload through localStorage — offered, never restored
   * behind the user's back.
   * ------------------------------------------------------------------- */

  const editMode = () => {
    const form = document.getElementById("series-form");
    const saveButton = document.getElementById("commit-button");
    const discardButton = document.getElementById("discard-button");
    const undoButton = document.getElementById("undo-button");
    const redoButton = document.getElementById("redo-button");
    const status = document.getElementById("commit-status");
    const counter = document.getElementById("change-count");
    const recovery = document.getElementById("recovery-bar");
    const recoveryText = document.getElementById("recovery-text");
    const recoverButton = document.getElementById("recover-button");
    const recoveryDiscard = document.getElementById("recovery-discard");
    const tabNotice = document.getElementById("tab-notice");
    const texts = config.texts || {};

    /** Row key -> model field, and back: the grid names differ from the column. */
    const patchOf = {};
    const fieldOf = {};
    config.columns.forEach((column) => {
      if (column.patch) {
        patchOf[column.field] = column.patch;
        fieldOf[column.patch] = column.field;
      }
    });

    /** The timestamp each row was read at, moved forward after every commit. */
    const baselines = new Map();
    config.data.forEach((row) => {
      baselines.set("stamp:" + row.id, row.updated_at);
    });
    baselines.set("issue:" + config.series.id, config.series.updated_at);

    /** The value each touched field had when the page loaded (`base`). */
    const bases = new Map();
    /** What has to be sent: one entry per object, only the fields that differ. */
    const buffer = new Map();
    /** Undo/redo as a log of values, so nothing has to be snapshotted. */
    const history = [];
    let pointer = 0;

    const keyOf = (model, id) => model + ":" + id;

    const controlOf = (field) =>
      form.querySelector('[name="' + field + '"]');

    const readValue = (model, id, field) => {
      if (model === "issue") {
        const control = controlOf(field);
        return control ? control.value : undefined;
      }
      const row = grid.getRow(id);
      const cell = row && fieldOf[field] ? row.getCell(fieldOf[field]) : null;
      return cell ? cell.getValue() : undefined;
    };

    const writeValue = (model, id, field, value) => {
      if (model === "issue") {
        const control = controlOf(field);
        if (control) {
          control.value = value === null || value === undefined ? "" : value;
        }
        return;
      }
      const row = grid.getRow(id);
      const cell = row && fieldOf[field] ? row.getCell(fieldOf[field]) : null;
      if (cell) {
        cell.setValue(value, true);
      }
    };

    /** Empty and null compare equal: a cleared number and an empty one are one. */
    const same = (left, right) => {
      const normalize = (value) =>
        value === null || value === undefined ? "" : String(value);
      return normalize(left) === normalize(right);
    };

    const formValues = () => {
      const values = {};
      Array.from(form.querySelectorAll("[name]")).forEach((control) => {
        values[control.name] = control.value;
      });
      return values;
    };
    let loaded = formValues();

    const entryFor = (model, id) => {
      const key = keyOf(model, id);
      let entry = buffer.get(key);
      if (!entry) {
        entry = {
          model,
          object_id: id,
          op: "update",
          patch: {},
          expected_updated_at: baselines.get(key) ?? null,
        };
        buffer.set(key, entry);
      }
      return entry;
    };

    /** Recomputes one object's patch against its base, and drops it when empty. */
    const sync = (model, id) => {
      const key = keyOf(model, id);
      const base = bases.get(key);
      if (!base) {
        return;
      }

      const entry = entryFor(model, id);
      entry.patch = {};
      entry.base = base;
      Object.keys(base).forEach((field) => {
        const current = readValue(model, id, field);
        if (!same(current, base[field])) {
          entry.patch[field] = current;
        }
      });

      if (!Object.keys(entry.patch).length) {
        buffer.delete(key);
      }
    };

    /** Remembers where a field started the first time it is touched. */
    const remember = (model, id, field, original) => {
      const key = keyOf(model, id);
      if (!bases.has(key)) {
        bases.set(key, {});
      }
      const base = bases.get(key);
      if (!(field in base)) {
        base[field] = original;
      }
    };

    const plural = (kind, count) => {
      const forms = (config.plurals || {})[kind];
      if (!forms) {
        return String(count);
      }
      const template = count === 1 ? forms.one : forms.other;
      return template.replace("%(count)s", String(count));
    };

    const changeCount = () =>
      Array.from(buffer.values()).reduce(
        (total, entry) => total + Object.keys(entry.patch).length,
        0
      );

    const setStatus = (message, kind) => {
      status.textContent = message || "";
      status.className = kind ? "dd-hint dd-status-" + kind : "dd-hint";
    };

    /** The first message the server sent, so a refusal is never silent. */
    const firstError = (errors) => {
      if (!errors) {
        return "";
      }
      if (Array.isArray(errors)) {
        return errors.length ? String(errors[0]) : "";
      }
      if (typeof errors === "object") {
        return firstError(Object.values(errors)[0]);
      }
      return String(errors);
    };

    const refusal = (body, fallback) =>
      firstError(body.errors) || body.message || fallback;

    const csrfToken = () => {
      const meta = document.querySelector('meta[name="csrf-token"]');
      return meta ? meta.content : "";
    };

    /** Posts a whole change set; the answer is JSON whatever the status is. */
    const apply = async (changes) => {
      const response = await fetch(config.applyUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken(),
        },
        body: JSON.stringify({ changes }),
      });
      return response.json().catch(() => ({ success: false }));
    };

    /* ---------------------------------------------------------------- *
     * Persistence: the draft outlives the tab, never the user's decision.
     * -------------------------------------------------------------- */

    let persistTimer = null;
    const persist = () => {
      window.clearTimeout(persistTimer);
      persistTimer = window.setTimeout(() => {
        try {
          if (!buffer.size) {
            /* A draft the user has not answered yet is not stale: removing it
             * here would delete yesterday's work 400 ms after opening the page. */
            if (recovery.hidden) {
              window.localStorage.removeItem(config.storageKey);
            }
            return;
          }
          window.localStorage.setItem(
            config.storageKey,
            JSON.stringify({
              schemaVersion: config.schemaVersion,
              savedAt: new Date().toISOString(),
              bases: Array.from(bases.entries()),
              entries: Array.from(buffer.values()).filter(
                (entry) => Object.keys(entry.patch).length
              ),
            })
          );
        } catch (error) {
          /* A full or blocked storage must not break the editor. */
        }
      }, 400);
    };

    const forget = (key) => {
      buffer.delete(key);
      bases.delete(key);
    };

    /* ---------------------------------------------------------------- *
     * Painting.
     * -------------------------------------------------------------- */

    const paintRows = () => {
      grid.getRows().forEach((row) => {
        const element = row.getElement();
        const key = keyOf("stamp", row.getData().id);
        element.classList.toggle(
          "dd-row-dirty",
          buffer.has(key) && Boolean(Object.keys(buffer.get(key).patch).length)
        );
      });
    };

    const paint = () => {
      const count = changeCount();
      counter.textContent = count ? plural("changes", count) : "";
      undoButton.disabled = pointer === 0;
      redoButton.disabled = pointer >= history.length;
      saveButton.disabled = count === 0;
      discardButton.disabled = count === 0;
      paintRows();
      persist();
    };

    /* ---------------------------------------------------------------- *
     * Undo and redo: replay values, not snapshots.
     * -------------------------------------------------------------- */

    const push = (operation) => {
      history.length = pointer;
      history.push(operation);
      while (history.length > (config.undoLimit || 200)) {
        history.shift();
      }
      pointer = history.length;
      paint();
    };

    const step = (direction) => {
      const operation =
        direction < 0 ? history[pointer - 1] : history[pointer];
      if (!operation) {
        return;
      }
      writeValue(
        operation.model,
        operation.id,
        operation.field,
        direction < 0 ? operation.from : operation.to
      );
      sync(operation.model, operation.id);
      pointer += direction;
      paint();
    };

    /* ---------------------------------------------------------------- *
     * Editing: the grid.
     * -------------------------------------------------------------- */

    grid.on("cellEdited", (cell) => {
      const row = cell.getRow();
      const id = row.getData().id;
      const field = patchOf[cell.getField()];
      const from = cell.getOldValue();
      const to = cell.getValue();

      remember("stamp", id, field, from);
      sync("stamp", id);
      push({ model: "stamp", id, field, from, to });
    });

    /* ---------------------------------------------------------------- *
     * Editing: the series strip.
     * -------------------------------------------------------------- */

    const previous = {};

    form.addEventListener("focusin", (event) => {
      const control = event.target;
      if (control.name) {
        previous[control.name] = control.value;
      }
    });

    form.addEventListener("input", (event) => {
      const control = event.target;
      if (!control.name) {
        return;
      }
      remember("issue", config.series.id, control.name, loaded[control.name]);
      sync("issue", config.series.id);
      paint();
    });

    /* `change` fires when the field is left, which is the right granularity for
     * one undo step: per keystroke would make Ctrl+Z spell out the typing. */
    form.addEventListener("change", (event) => {
      const control = event.target;
      if (!control.name) {
        return;
      }
      push({
        model: "issue",
        id: config.series.id,
        field: control.name,
        from: control.name in previous ? previous[control.name] : loaded[control.name],
        to: control.value,
      });
      previous[control.name] = control.value;
    });

    /* ---------------------------------------------------------------- *
     * Committing and discarding.
     * -------------------------------------------------------------- */

    const commit = async () => {
      const changes = Array.from(buffer.values()).filter(
        (entry) => Object.keys(entry.patch).length
      );
      if (!changes.length) {
        setStatus(texts.noChanges, "");
        return;
      }

      setStatus(texts.saving, "pending");
      const body = await apply(changes);
      const rows = (body.data || {}).rows || [];
      const rejected = body.rejected || [];

      rows.forEach((written) => {
        const change = changes[written.index];
        const key = keyOf(change.model, change.object_id);
        baselines.set(key, written.updated_at);
        if (change.model === "issue") {
          config.series.updated_at = written.updated_at;
        }
        forget(key);

        if (change.model === "stamp") {
          const row = grid.getRow(change.object_id);
          if (row) {
            const element = row.getElement();
            element.classList.remove("dd-row-dirty", "dd-row-error");
            element.classList.add("dd-row-saved");
            window.setTimeout(
              () => element.classList.remove("dd-row-saved"),
              1200
            );
          }
        }
      });

      rejected.forEach((problem) => {
        const change = changes[problem.index];
        if (change.model !== "stamp") {
          return;
        }
        const row = grid.getRow(change.object_id);
        if (row) {
          row.getElement().classList.add("dd-row-error");
        }
      });

      if (rows.length) {
        loaded = formValues();
      }

      if (rejected.length) {
        const problem = rejected[0];
        setStatus(
          refusal(problem.errors, texts.rejected) ||
            refusal(body, texts.rejected),
          "error"
        );
      } else {
        setStatus(texts.saved, "ok");
      }

      paint();
    };

    const discard = () => {
      Array.from(buffer.keys()).forEach((key) => {
        const base = bases.get(key) || {};
        Object.keys(base).forEach((field) => {
          const [model, id] = key.split(":");
          writeValue(model, Number(id), field, base[field]);
        });
      });
      buffer.clear();
      bases.clear();
      history.length = 0;
      pointer = 0;
      loaded = formValues();
      recovery.hidden = true;
      window.localStorage.removeItem(config.storageKey);
      setStatus("", "");
      paint();
    };

    /* Shift+Enter and the button commit the whole change set. */
    const commitTarget = async () => {
      const active = document.activeElement;
      if (active && active !== document.body) {
        active.blur();
      }
      await Promise.resolve();
      commit();
    };

    document.addEventListener("keydown", (event) => {
      if (event.key === "Enter" && event.shiftKey) {
        event.preventDefault();
        commitTarget();
        return;
      }

      if (!(event.ctrlKey || event.metaKey) || event.key.toLowerCase() !== "z") {
        return;
      }
      /* Inside a text field the browser's own undo is the one the user means. */
      if (event.target && form.contains(event.target)) {
        return;
      }
      event.preventDefault();
      step(event.shiftKey ? 1 : -1);
    });

    saveButton.addEventListener("click", commitTarget);
    discardButton.addEventListener("click", discard);
    undoButton.addEventListener("click", () => step(-1));
    redoButton.addEventListener("click", () => step(1));

    /* ---------------------------------------------------------------- *
     * Draft recovery and the other tab.
     * -------------------------------------------------------------- */

    const stored = () => {
      try {
        const raw = window.localStorage.getItem(config.storageKey);
        return raw ? JSON.parse(raw) : null;
      } catch (error) {
        return null;
      }
    };

    const offerRecovery = () => {
      const draft = stored();
      if (!draft) {
        return;
      }

      if (
        draft.schemaVersion !== config.schemaVersion ||
        !Array.isArray(draft.entries) ||
        !draft.entries.length
      ) {
        window.localStorage.removeItem(config.storageKey);
        return;
      }

      const count = draft.entries.reduce(
        (total, entry) => total + Object.keys(entry.patch || {}).length,
        0
      );
      if (!count) {
        window.localStorage.removeItem(config.storageKey);
        return;
      }

      recoveryText.textContent = plural("recover", count);
      recovery.hidden = false;

      recoverButton.addEventListener("click", () => {
        (draft.bases || []).forEach(([key, fields]) => bases.set(key, fields));
        draft.entries.forEach((entry) => {
          Object.entries(entry.patch || {}).forEach(([field, value]) => {
            writeValue(entry.model, entry.object_id, field, value);
            push({
              model: entry.model,
              id: entry.object_id,
              field,
              from: (bases.get(keyOf(entry.model, entry.object_id)) || {})[field],
              to: value,
            });
          });
          sync(entry.model, entry.object_id);
        });
        recovery.hidden = true;
        setStatus("", "");
        paint();
      });

      recoveryDiscard.addEventListener("click", () => {
        window.localStorage.removeItem(config.storageKey);
        recovery.hidden = true;
      });
    };

    window.addEventListener("storage", (event) => {
      if (event.key !== config.storageKey) {
        return;
      }
      tabNotice.hidden = false;
    });

    window.addEventListener("beforeunload", (event) => {
      if (!buffer.size) {
        return;
      }
      event.preventDefault();
      event.returnValue = "";
    });

    offerRecovery();
    paint();
  };
  /* --------------------------------------------------------------------- *
   * mode=new: the rows live here.
   * ------------------------------------------------------------------- */

  /** The draft rows, in grid order: the grid only mirrors this list. */
  let drafts = [];

  const newMode = () => {
    const nameInput = document.getElementById(config.nameInput);
    const rowsInput = document.getElementById(config.rowsInput);
    const badge = document.getElementById(config.countBadge);
    const form = document.getElementById("series-form");
    let nextId = 1;

    /** A row as a new stamp starts: name only, and empty everything else. */
    const emptyRow = () => ({
      id: config.rowIdPrefix + nextId++,
      edifil: "",
      fesofi: "",
      name: nameInput.value,
      face_value: "",
      colors: [],
      total_printed: null,
      mnh: null,
      used: null,
      has_image: false,
      image_url: null,
      touched: false,
    });

    /** Paints the grid from the drafts and keeps the counter honest. */
    const render = () => {
      grid.setData(drafts);
      badge.textContent = String(drafts.length);
    };

    /** Adds or trims rows to reach N, never touching one already edited.
     *
     * Growing appends; shrinking drops untouched rows from the bottom and
     * stops at the first touched one, so lowering N cannot destroy work. The
     * delete-row button (S13) is the way to remove the rest.
     */
    const resize = () => {
      const requested =
        Number.parseInt(rowsInput.value, 10) || config.rows.default;
      const target = clamp(requested, config.rows.min, config.rows.max);
      rowsInput.value = String(target);

      while (drafts.length < target) {
        drafts.push(emptyRow());
      }
      while (drafts.length > target && !drafts[drafts.length - 1].touched) {
        drafts.pop();
      }
      render();
    };

    rowsInput.addEventListener("change", resize);
    rowsInput.addEventListener("keydown", (event) => {
      if (event.key === "Enter") {
        event.preventDefault();
        resize();
      }
    });

    /* The name of the series is a default, not an inheritance: an untouched row
     * follows it, and stops following the moment the row is edited. */
    nameInput.addEventListener("input", () => {
      drafts.forEach((row) => {
        if (!row.touched) {
          row.name = nameInput.value;
        }
      });
      render();
    });

    /* Undo inside the session: the draft is never stored, but Ctrl+Z has to
     * work while the tab is open. Row id and field are kept instead of the cell
     * component: `render()` replaces the rows, so a held cell goes stale. */
    const history = [];
    let pointer = 0;

    grid.on("cellEdited", (cell) => {
      const edited = cell.getRow().getData();
      const row = drafts.find((draft) => draft.id === edited.id);
      if (row) {
        row.touched = true;
      }
      history.length = pointer;
      history.push({
        id: edited.id,
        field: cell.getField(),
        from: cell.getOldValue(),
        to: cell.getValue(),
      });
      while (history.length > (config.undoLimit || 200)) {
        history.shift();
      }
      pointer = history.length;
    });

    const step = (direction) => {
      const operation =
        direction < 0 ? history[pointer - 1] : history[pointer];
      if (!operation) {
        return;
      }
      const draft = drafts.find((row) => row.id === operation.id);
      const value = direction < 0 ? operation.from : operation.to;
      if (draft) {
        draft[operation.field] = value;
      }
      const gridRow = grid.getRow(operation.id);
      const cell = gridRow && gridRow.getCell(operation.field);
      if (cell) {
        cell.setValue(value, true);
      }
      pointer += direction;
    };

    document.addEventListener("keydown", (event) => {
      if (!(event.ctrlKey || event.metaKey) || event.key.toLowerCase() !== "z") {
        return;
      }
      if (event.target && event.target.tagName === "TEXTAREA") {
        return;
      }
      event.preventDefault();
      step(event.shiftKey ? 1 : -1);
    });

    /* A year no row holds is legitimate: it is created when the series is
     * saved. The notice says so, so a new year is not mistaken for a typo. */
    const yearInput = document.getElementById("field-year");
    const yearHint = document.getElementById("year-new-hint");
    const knownYears = () =>
      new Set(
        Array.from(document.querySelectorAll("#year-options option")).map(
          (option) => option.value
        )
      );
    const syncYearHint = () => {
      if (!yearInput || !yearHint) {
        return;
      }
      const typed = yearInput.value.trim();
      yearHint.hidden = typed === "" || knownYears().has(typed);
    };
    if (yearInput) {
      yearInput.addEventListener("input", syncYearHint);
    }

    const applyPrefill = () => {
      Object.entries(config.prefill || {}).forEach(([field, value]) => {
        const control = document.getElementById("field-" + field);
        if (control) {
          control.value = String(value);
        }
      });
      syncYearHint();
    };

    const useLastIssue = document.getElementById("use-last-issue");
    if (useLastIssue) {
      useLastIssue.addEventListener("click", applyPrefill);
    }

    resize();
    syncYearHint();

    /* Dirty means the series form changed or the row set did. The guard only
     * fires then: warning someone off an empty form teaches them to ignore it. */
    const snapshot = () =>
      JSON.stringify({
        fields: Array.from(form.querySelectorAll("[name]")).map(
          (control) => control.value
        ),
        rows: drafts.map((row) => row.id),
      });
    const initial = snapshot();

    window.addEventListener("beforeunload", (event) => {
      if (snapshot() === initial) {
        return;
      }
      event.preventDefault();
      event.returnValue = "";
    });

    /* Shift+Enter belongs to the commit that does not exist yet: it stays inert
     * and flashes the notice under the grid instead of promising anything. */
    const hint = document.getElementById("new-save-hint");
    document.addEventListener("keydown", (event) => {
      if (event.key !== "Enter" || !event.shiftKey) {
        return;
      }
      event.preventDefault();
      if (!hint) {
        return;
      }
      hint.classList.add("dd-hint-flash");
      window.setTimeout(() => hint.classList.remove("dd-hint-flash"), 1200);
    });
  };

  if (config.mode === "new") {
    newMode();
  } else {
    editMode();
  }

  /** Esc returns to the workbench with its filters, like the back button.
   *
   * Except when a field or a cell editor has the focus: there the first Esc
   * belongs to the control, and leaving the page would throw typed values away.
   */
  document.addEventListener("keydown", (event) => {
    if (event.key !== "Escape") {
      return;
    }
    const active = document.activeElement;
    if (active && ["INPUT", "SELECT", "TEXTAREA"].includes(active.tagName)) {
      active.blur();
      return;
    }
    const referrer = document.referrer;
    const fromWorkbench =
      referrer !== "" &&
      referrer.indexOf(window.location.origin) === 0 &&
      referrer.indexOf("/datadesk/issues/") !== -1;
    if (fromWorkbench) {
      window.history.back();
    } else {
      window.location.assign(config.issuesUrl);
    }
  });
})();
