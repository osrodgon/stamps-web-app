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
   * mode=edit: one row at a time.
   * ------------------------------------------------------------------- */

  const editMode = () => {
    const form = document.getElementById("series-form");
    const button = document.getElementById("commit-button");
    const status = document.getElementById("commit-status");
    const meta = document.querySelector(".dd-meta");
    const texts = config.texts || {};

    /** Model field behind each editable column, by row key. */
    const patchOf = {};
    config.columns.forEach((column) => {
      if (column.patch) {
        patchOf[column.field] = column.patch;
      }
    });

    /** The timestamp each row was read at, moved forward after every commit. */
    const baselines = new Map(config.data.map((row) => [row.id, row.updated_at]));

    /** Edited and still unsaved, per row: the cells to put back on a refusal. */
    const pending = new Map();
    let lastEdited = null;

    const setStatus = (message, kind) => {
      status.textContent = message;
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

    /** Posts one change; the answer is JSON whatever the status code is. */
    const apply = async (change) => {
      const response = await fetch(config.applyUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken(),
        },
        body: JSON.stringify({ changes: [change] }),
      });
      return response.json().catch(() => ({ success: false }));
    };

    const formValues = () => {
      const values = {};
      Array.from(form.querySelectorAll("[name]")).forEach((control) => {
        values[control.name] = control.value;
      });
      return values;
    };
    let seriesBase = formValues();

    /** Whether the strip holds something the database does not have yet. */
    const seriesDirty = () => {
      const values = formValues();
      return Object.keys(values).some((field) => values[field] !== seriesBase[field]);
    };

    /** The grid row waiting to be saved: the one just edited, or the selection. */
    const pendingRow = () =>
      (lastEdited !== null && grid.getRow(lastEdited)) ||
      grid.getSelectedRows()[0] ||
      grid.getRows().find((item) => pending.has(item.getData().id));

    const commitRow = async (row) => {
      const data = row.getData();
      const edits = pending.get(data.id);
      if (!edits) {
        setStatus(texts.noChanges, "");
        return;
      }

      const patch = {};
      edits.forEach((edit) => {
        patch[patchOf[edit.cell.getField()]] = edit.cell.getValue();
      });

      const body = await apply({
        model: "stamp",
        object_id: data.id,
        op: "update",
        patch,
        expected_updated_at: baselines.get(data.id),
      });
      const written = ((body.data || {}).rows || [])[0];
      const element = row.getElement();

      if (written) {
        baselines.set(data.id, written.updated_at);
        pending.delete(data.id);
        lastEdited = null;
        element.classList.remove("dd-row-dirty", "dd-row-error");
        element.classList.add("dd-row-saved");
        window.setTimeout(() => element.classList.remove("dd-row-saved"), 1200);
        setStatus(texts.saved, "ok");
        return;
      }

      /* Refused: every edited cell goes back to what the database still holds,
       * so nothing typed looks saved, and the row stays marked. */
      edits.forEach((edit) => edit.cell.setValue(edit.old, true));
      pending.delete(data.id);
      lastEdited = null;
      element.classList.remove("dd-row-dirty");
      element.classList.add("dd-row-error");
      setStatus(refusal(body, texts.rejected), "error");
    };

    const commitSeries = async () => {
      const values = formValues();
      const patch = {};
      Object.entries(values).forEach(([field, value]) => {
        if (value !== seriesBase[field]) {
          patch[field] = value;
        }
      });
      if (!Object.keys(patch).length) {
        setStatus(texts.noChanges, "");
        return;
      }

      const body = await apply({
        model: "issue",
        object_id: config.series.id,
        op: "update",
        patch,
        expected_updated_at: config.series.updated_at,
      });
      const written = ((body.data || {}).rows || [])[0];

      if (written) {
        config.series.updated_at = written.updated_at;
        seriesBase = values;
        meta.classList.remove("dd-meta-error");
        setStatus(texts.seriesSaved, "ok");
        return;
      }

      /* The strip keeps what was typed — a rejection is fixed here, not retyped
       * — while a single cell is reverted instead: one value is cheap to type
       * again, a half-filled form is not. */
      meta.classList.add("dd-meta-error");
      setStatus(refusal(body, texts.rejected), "error");
    };

    /** Shift+Enter and the button commit what the user is working on.
     *
     * The open editor is closed first: Tabulator writes the typed value into
     * the row when its input loses the focus, and committing before that would
     * send the value the cell had. The blur is what an Enter would do anyway.
     */
    const commitTarget = async () => {
      const active = document.activeElement;
      /* The button is not inside the form, and clicking it moves the focus out
       * of the field, so "what has the focus" alone cannot decide the target:
       * the dirty strip is checked too, or Save on the series would answer
       * "nothing changed" while the strip holds an edit. */
      const inStrip = Boolean(active && form.contains(active));
      if (active && active !== document.body) {
        active.blur();
      }
      await Promise.resolve();

      if (inStrip && seriesDirty()) {
        commitSeries();
        return;
      }

      const row = pendingRow();
      if (row) {
        commitRow(row);
        return;
      }

      if (seriesDirty()) {
        commitSeries();
        return;
      }

      setStatus(texts.noChanges, "");
    };

    grid.on("cellEdited", (cell) => {
      const row = cell.getRow();
      const rowId = row.getData().id;
      if (!pending.has(rowId)) {
        pending.set(rowId, new Map());
      }
      const edits = pending.get(rowId);
      const field = cell.getField();
      if (!edits.has(field)) {
        edits.set(field, { cell, old: cell.getOldValue() });
      }
      lastEdited = rowId;

      const element = row.getElement();
      element.classList.add("dd-row-dirty");
      element.classList.remove("dd-row-error", "dd-row-saved");
      setStatus(texts.unsaved, "pending");
    });

    document.addEventListener("keydown", (event) => {
      if (event.key !== "Enter" || !event.shiftKey) {
        return;
      }
      event.preventDefault();
      commitTarget();
    });

    /* Typing in the strip says so straight away: otherwise the only clue that
     * the series has unsaved work is a status line that still reads "saved". */
    const showStripState = () => {
      if (seriesDirty()) {
        setStatus(texts.unsaved, "pending");
      } else {
        setStatus("", "");
      }
    };
    form.addEventListener("input", showStripState);
    form.addEventListener("change", showStripState);

    if (button) {
      button.addEventListener("click", commitTarget);
    }
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

    grid.on("cellEdited", (cell) => {
      const edited = cell.getRow().getData();
      const row = drafts.find((draft) => draft.id === edited.id);
      if (row) {
        row.touched = true;
      }
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
