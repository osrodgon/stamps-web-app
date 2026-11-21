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

  const csrfToken = () => {
    const meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.content : "";
  };

  /** Marks the fields the server refused and returns the first of them. */
  const markFields = (form, errors) => {
    if (!errors || typeof errors !== "object" || Array.isArray(errors)) {
      return null;
    }
    let first = null;
    Object.keys(errors).forEach((field) => {
      const control = form.querySelector('[name="' + field + '"]');
      if (!control) {
        return;
      }
      control.classList.add("dd-input-invalid");
      first = first || control;
    });
    return first;
  };

  /** Clears every field mark: a new attempt starts from a clean strip. */
  const clearFieldMarks = (form) => {
    form.querySelectorAll(".dd-input-invalid").forEach((control) => {
      control.classList.remove("dd-input-invalid");
    });
  };

  /** Rings the strip as a whole, for a refusal that names no field. */
  const markStrip = (form, on) => {
    const meta = form.closest(".dd-meta");
    if (meta) {
      meta.classList.toggle("dd-meta-error", Boolean(on));
    }
  };

  /* ------------------------------------------------------------------ *
   * Reference fields: typed with completion instead of chosen.
   *
   * The strip would otherwise ship every artist, printer and colour with each
   * series, and those tables only grow. Instead the field asks
   * /datadesk/lookups/<key>/search as the user types, and the + button creates
   * the row nobody had yet. The API speaks ids and a person types names, so
   * these two maps are the dictionary between them: seeded with what the page
   * rendered, grown by every search and every row created from here.
   * ------------------------------------------------------------------ */

  const lookupById = new Map();
  const lookupByLabel = new Map();

  const lookupIdKey = (field, id) => field + ":" + String(id);
  const lookupLabelKey = (field, label) =>
    field + ":" + String(label).trim().toLowerCase();

  const rememberLookup = (field, id, label) => {
    if (id === null || id === undefined || String(id) === "") {
      return;
    }
    lookupById.set(lookupIdKey(field, id), label);
    lookupByLabel.set(lookupLabelKey(field, label), String(id));
  };

  /** The id behind a typed name, or "" when the name is new to the page. */
  const lookupIdOf = (field, label) =>
    lookupByLabel.get(lookupLabelKey(field, label)) || "";

  const lookupLabelOf = (field, id) =>
    lookupById.get(lookupIdKey(field, id)) || "";

  const lookupControls = () =>
    Array.from(document.querySelectorAll("[data-lookup]"));

  const lookupControl = (field) =>
    document.querySelector('[data-lookup="' + field + '"]');

  /** The value the API sees for a control: an id when the field is a lookup. */
  const formValue = (control) => {
    const field = control.dataset ? control.dataset.lookup : "";
    return field ? lookupIdOf(field, control.value) : control.value;
  };

  /** Writes a lookup control from an id, showing the name it identifies. */
  const setLookup = (control, field, id) => {
    control.value = lookupLabelOf(field, id) || "";
  };

  /** A typed name that matches no row: it cannot become an id by itself. */
  const unresolvedLookup = () =>
    lookupControls().find(
      (control) =>
        control.value.trim() !== "" &&
        !lookupIdOf(control.dataset.lookup, control.value)
    ) || null;

  /** What the modes plug into: a line of status, and a row worth reviewing. */
  const lookupHooks = { notice: () => {}, created: () => {} };
  const lookupTexts = config.lookupText || {};
  let lookupSearchTimer = null;

  lookupControls().forEach((control) => {
    if (control.value.trim() !== "" && control.dataset.value) {
      rememberLookup(control.dataset.lookup, control.dataset.value, control.value);
    }
  });

  /** The + button only makes sense for a name the page does not know. */
  const paintLookupButton = (control) => {
    const field = control.dataset.lookup;
    const button = document.querySelector('[data-create-for="' + field + '"]');
    if (!button) {
      return;
    }
    const name = control.value.trim();
    const known = name !== "" && lookupIdOf(field, name) !== "";
    button.hidden = name === "" || known;
    button.textContent = (lookupTexts.create || "+ %(name)s").replace(
      "%(name)s",
      name
    );
  };

  const renderLookupOptions = (field, rows) => {
    const list = document.getElementById("lookup-" + field);
    if (!list) {
      return;
    }
    list.textContent = "";
    rows.forEach((row) => {
      const option = document.createElement("option");
      option.value = row.label;
      list.append(option);
    });
  };

  const searchLookup = async (field, query) => {
    const endpoints = (config.lookups || {})[field] || {};
    if (!endpoints.search) {
      return;
    }
    try {
      const response = await fetch(
        endpoints.search + "?q=" + encodeURIComponent(query),
        { headers: { Accept: "application/json" } }
      );
      const body = await response.json();
      if (!body || !body.success) {
        return;
      }
      const rows = body.data.results || [];
      rows.forEach((row) => rememberLookup(field, row.value, row.label));
      renderLookupOptions(field, rows);
    } catch (error) {
      /* A search that fails leaves the list as it was: the field still takes a
       * name, it just cannot suggest one. */
    }
  };

  const requestLookupSearch = (field, query) => {
    window.clearTimeout(lookupSearchTimer);
    lookupSearchTimer = window.setTimeout(
      () => searchLookup(field, query),
      250
    );
  };

  /** Creates the row being typed, or returns the one that already existed. */
  const createLookupRow = async (field, name) => {
    const endpoints = (config.lookups || {})[field] || {};
    try {
      const response = await fetch(endpoints.create, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken(),
        },
        body: JSON.stringify({ value: name }),
      });
      const body = await response.json();
      if (!body || !body.success || !body.data) {
        lookupHooks.notice(
          (body && body.message) || lookupTexts.failed,
          "error"
        );
        return null;
      }
      rememberLookup(field, body.data.id, body.data.name);
      return body.data;
    } catch (error) {
      lookupHooks.notice(lookupTexts.failed, "error");
      return null;
    }
  };

  lookupControls().forEach((control) => {
    const field = control.dataset.lookup;
    control.addEventListener("focus", () => {
      paintLookupButton(control);
      searchLookup(field, control.value.trim());
    });
    control.addEventListener("input", () => {
      paintLookupButton(control);
      requestLookupSearch(field, control.value.trim());
    });
    control.addEventListener("change", () => paintLookupButton(control));
  });

  Array.from(document.querySelectorAll("[data-create-for]")).forEach((button) => {
    button.addEventListener("click", async () => {
      const field = button.dataset.createFor;
      const control = lookupControl(field);
      const name = control.value.trim();
      if (name === "") {
        return;
      }
      button.disabled = true;
      const row = await createLookupRow(field, name);
      button.disabled = false;
      if (!row) {
        return;
      }
      setLookup(control, field, row.id);
      control.dataset.value = String(row.id);
      paintLookupButton(control);
      lookupHooks.notice(lookupTexts.created, "ok");
      lookupHooks.created(field, row);
      /* The modes listen to their own events, so the change is remembered (and
       * becomes undoable) without either of them knowing how it was chosen. */
      control.dispatchEvent(new Event("input", { bubbles: true }));
      control.dispatchEvent(new Event("change", { bubbles: true }));
    });
  });

  /** The colour behind a cell value: `mode=edit` sends objects, `new` ids. */
  const colourOf = (value) => {
    if (value && typeof value === "object") {
      return value;
    }
    const known = (config.colours || []).find(
      (colour) => String(colour.value) === String(value)
    );
    return known ? { name: known.label, tone: known.tone } : null;
  };

  /** Renders the colours as tinted chips.
   *
   * A cell clips what does not fit and the browser answers with "...", which
   * says nothing: it paints one chip and a count of the rest instead, and the
   * whole list travels in the title. The editor is where the user reads them
   * all at once.
   */
  const colorsFormatter = (cell) => {
    const colors = (cell.getValue() || []).map(colourOf).filter(Boolean);
    if (!colors.length) {
      return "";
    }
    const box = document.createElement("span");
    box.className = "dd-chips";
    box.title = colors.map((color) => color.name).join(" · ");

    const chip = document.createElement("span");
    chip.className = `dd-chip dd-chip-${colors[0].tone}`;
    chip.textContent = colors[0].name;
    box.append(chip);

    if (colors.length > 1) {
      const more = document.createElement("span");
      more.className = "dd-chip dd-chip-more";
      more.textContent = "+" + (colors.length - 1);
      box.append(more);
    }
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
    /* A field with no column of its own still needs a cell: the preview pane
     * writes the description there, so the change set, the review panel and
     * the draft carry it without knowing the pane exists. */
    if (definition.hidden) {
      column.visible = false;
    }
    if (definition.mono) {
      column.cssClass = "dd-mono";
    }
    if (definition.patch) {
      column.editor = definition.editor === "number" ? "number" : "input";
    }
    if (definition.field === "colors") {
      column.formatter = colorsFormatter;
      /* Only `mode=new` offers the editor: there the colours are the row's and
       * travel as ids. In `mode=edit` the change set still carries no M2M, so
       * the cell stays read-only; the lookup screen of S19 owns that. */
      if ((config.colours || []).length) {
        column.editor = "list";
        column.editorParams = {
          multiselect: true,
          listOnEmpty: true,
          values: config.colours.map((colour) => ({
            label: colour.label,
            value: colour.value,
          })),
        };
      }
    }
    if (definition.field === "has_image") {
      column.formatter = imageFormatter;
      column.headerSort = false;
      column.cssClass = "dd-image-cell";
    }
    return column;
  };

  /** Removes one draft row. `mode=new` only: real rows are deleted by S17. */
  const removeColumn = {
    field: "remove",
    title: "",
    width: 34,
    headerSort: false,
    hozAlign: "center",
    cssClass: "dd-remove-cell",
    formatter: () => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "dd-remove";
      button.textContent = "×";
      button.title = ((config.texts || {}).removeRow) || "";
      button.setAttribute("aria-label", button.title);
      return button;
    },
  };

  /** What a row's delete button does, wired by the mode that understands it. */
  let deleteStampRow = null;

  /** Deleting a real stamp: a dialog, not a change in the buffer. */
  const stampDeleteColumn = {
    field: "delete_stamp",
    title: "",
    width: 40,
    headerSort: false,
    hozAlign: "center",
    cssClass: "dd-remove-cell",
    formatter: (cell) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "dd-remove dd-stamp-delete";
      button.textContent = "×";
      button.title = ((config.texts || {}).deleteStamp) || "";
      button.setAttribute("aria-label", button.title);
      button.addEventListener("click", (event) => {
        event.stopPropagation();
        if (deleteStampRow) {
          deleteStampRow(cell.getRow().getData());
        }
      });
      return button;
    },
  };

  const grid = new Tabulator("#stamp-grid", {
    data: config.data,
    columns: [
      ...config.columns.map(buildColumn),
      ...(config.mode === "new" ? [removeColumn] : []),
      ...(config.mode === "edit" ? [stampDeleteColumn] : []),
    ],
    layout: "fitColumns",
    height: false,
    /* The preview pane follows the selection, and `j`/`k` move it: a row is
     * something the user can be "on", not only something they can edit. */
    selectableRows: 1,
    placeholder: config.emptyText,
  });

  /* --------------------------------------------------------------------- *
   * The preview pane.
   *
   * The 26px thumbnail is a colour swatch, and the description has no column.
   * The pane follows the selected row — no hover, no click on the picture — and
   * edits the description in place. The value is written into a hidden cell, so
   * it travels with the row instead of with the pane: selecting another stamp
   * does not lose what was typed.
   * ------------------------------------------------------------------- */

  const previewBody = document.getElementById("preview-body");
  const previewEmpty = document.getElementById("preview-empty");
  const previewImage = document.getElementById("preview-image");
  const previewMissing = document.getElementById("preview-missing");
  const previewIdentity = document.getElementById("preview-identity");
  const previewDescription = document.getElementById("preview-description");

  /** What each mode does with a description typed here. */
  const previewHooks = { input: () => {}, commit: () => {} };
  /** A value written by the pane or by undo is not a new edit. */
  let quietCell = null;
  /** The description the field had when it took the focus: one undo step. */
  let previewStart = "";

  const selectedRow = () => {
    const rows = grid.getSelectedRows();
    return rows.length ? rows[0] : null;
  };

  const descriptionCell = (row) => row.getCell("description");

  const descriptionValue = (row) => {
    const cell = descriptionCell(row);
    const value = cell ? cell.getValue() : row.getData().description;
    return value === null || value === undefined ? "" : String(value);
  };

  /** Writes a cell without the edit events: a keystroke is not an undo step. */
  const writeCell = (cell, value) => {
    if (!cell) {
      return;
    }
    quietCell = cell;
    try {
      cell.setValue(value, true);
    } finally {
      quietCell = null;
    }
  };

  const paintPreview = (row) => {
    previewBody.hidden = !row;
    previewEmpty.hidden = Boolean(row);
    if (!row) {
      return;
    }
    const data = row.getData();
    previewImage.src = data.image_url || config.fallbackImage;
    previewImage.classList.toggle("dd-thumb-missing", !data.image_url);
    previewMissing.hidden = Boolean(data.image_url);
    previewIdentity.textContent =
      [data.edifil, data.name].filter(Boolean).join(" · ") || String(data.id);
    /* Assigning `.value` moves the caret to the end even when the text is the
     * same, which would fight the user in the middle of a sentence. */
    const description = descriptionValue(row);
    if (previewDescription.value !== description) {
      previewDescription.value = description;
    }
  };

  const moveSelection = (direction) => {
    const rows = grid.getRows();
    if (!rows.length) {
      return;
    }
    const current = selectedRow();
    /* By id: two calls return two components for the same row, and comparing
     * them by identity would always miss. */
    const currentId = current ? current.getData().id : null;
    const index = rows.findIndex((row) => row.getData().id === currentId);
    const next =
      index === -1
        ? direction > 0
          ? 0
          : rows.length - 1
        : clamp(index + direction, 0, rows.length - 1);
    rows[next].select();
    grid.scrollToRow(rows[next], "nearest", false);
  };

  /* The event carries the row: `getSelectedRows()` still holds the old one for
   * a moment while the selection changes, and reading it here painted the
   * previous stamp. */
  grid.on("rowSelected", (row) => paintPreview(row));
  grid.on("rowDeselected", () => {
    if (!grid.getSelectedRows().length) {
      paintPreview(null);
    }
  });
  /* Clicking the row that is already selected deselects it, which would empty
   * the pane: the current row is where you are, not a toggle. The click has
   * already been processed here, so this is a repair and not a fight. */
  grid.on("rowClick", (event, row) => {
    if (!row.isSelected()) {
      row.select();
    }
  });

  /* The strip of the workspace has no search to focus with `/`; the rows are
   * what the keyboard moves, and a field keeps its own letters. */
  document.addEventListener("keydown", (event) => {
    if (event.ctrlKey || event.metaKey || event.altKey) {
      return;
    }
    if (event.key !== "j" && event.key !== "k") {
      return;
    }
    const target = event.target;
    if (target instanceof Element && target.closest("input, select, textarea")) {
      return;
    }
    /* A dialog owns the keyboard while it is open. */
    if (
      document.querySelector(
        ".dd-dialog-backdrop:not([hidden]), .dd-review:not([hidden])"
      )
    ) {
      return;
    }
    event.preventDefault();
    moveSelection(event.key === "j" ? 1 : -1);
  });

  previewDescription.addEventListener("focus", () => {
    const row = selectedRow();
    previewStart = row ? descriptionValue(row) : "";
  });

  previewDescription.addEventListener("input", () => {
    const row = selectedRow();
    if (row) {
      previewHooks.input(row, previewDescription.value);
    }
  });

  previewDescription.addEventListener("change", () => {
    const row = selectedRow();
    if (row) {
      previewHooks.commit(row, previewDescription.value);
    }
  });

  /* A series opens on its first stamp: the pane would otherwise be a hint until
   * the user clicks, and `j`/`k` would start from nowhere. A new series starts
   * unselected on purpose — its rows are placeholders, not stamps. */
  grid.on("tableBuilt", () => {
    if (config.mode !== "edit") {
      return;
    }
    const rows = grid.getRows();
    if (rows.length) {
      rows[0].select();
    }
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
    const reviewButton = document.getElementById("review-button");
    const reviewPanel = document.getElementById("review-panel");
    const reviewBody = document.getElementById("review-body");
    const reviewClose = document.getElementById("review-close");
    const backupButton = document.getElementById("backup-button");
    const backupStatus = document.getElementById("backup-status");
    const cloneButton = document.getElementById("clone-button");
    const deleteButton = document.getElementById("delete-button");
    const deletePanel = document.getElementById("delete-panel");
    const deleteClose = document.getElementById("delete-close");
    const deleteCancel = document.getElementById("delete-cancel");
    const deleteConfirm = document.getElementById("delete-confirm");
    const deleteConfirmLabel = document.getElementById("delete-confirm-label");
    const deleteConfirmButton = document.getElementById("delete-confirm-button");
    const deleteWarning = document.getElementById("delete-warning");
    const deleteStatus = document.getElementById("delete-status");
    const deleteCounts = {
      stamps: document.getElementById("delete-stamps"),
      items: document.getElementById("delete-items"),
      collections: document.getElementById("delete-collections"),
    };
    const stampPanel = document.getElementById("stamp-delete-panel");
    const stampClose = document.getElementById("stamp-delete-close");
    const stampCancel = document.getElementById("stamp-delete-cancel");
    const stampConfirm = document.getElementById("stamp-delete-confirm");
    const stampWarning = document.getElementById("stamp-delete-warning");
    const stampIdentity = document.getElementById("stamp-delete-identity");
    const stampStatus = document.getElementById("stamp-delete-status");
    const stampItems = document.getElementById("stamp-delete-items");
    const stampCollections = document.getElementById("stamp-delete-collections");
    const badge = document.getElementById("stamp-count");
    const texts = config.texts || {};
    const commitLabel = saveButton.textContent;

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
    /** Reference rows created while editing: they are saved, so they are not
     * changes, but the review panel says which ones it was. */
    const createdLookups = [];

    const keyOf = (model, id) => model + ":" + id;

    /** The label the editor uses for a field: the server sends the map. */
    const fieldLabel = (model, field) =>
      ((config.fieldLabels || {})[model] || {})[field] || field;

    const controlOf = (field) =>
      form.querySelector('[name="' + field + '"]');

    const readValue = (model, id, field) => {
      if (model === "issue") {
        const control = controlOf(field);
        return control ? formValue(control) : undefined;
      }
      const row = grid.getRow(id);
      const cell = row && fieldOf[field] ? row.getCell(fieldOf[field]) : null;
      return cell ? cell.getValue() : undefined;
    };

    const writeValue = (model, id, field, value) => {
      if (model === "issue") {
        const control = controlOf(field);
        if (!control) {
          return;
        }
        /* A lookup is shown by its name and sent by its id, so undo and redo
         * write the name the map remembers for that id. */
        if (control.dataset.lookup) {
          setLookup(control, field, value);
        } else {
          control.value = value === null || value === undefined ? "" : value;
        }
        return;
      }
      const row = grid.getRow(id);
      const cell = row && fieldOf[field] ? row.getCell(fieldOf[field]) : null;
      if (cell) {
        /* Quietly: replaying a value is not a new edit, and an edit event here
         * would push the undo it is performing back onto the stack. */
        writeCell(cell, value);
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
        values[control.name] = formValue(control);
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

    /** What the panel shows for a value: a lookup reads better by its name. */
    const displayValue = (model, field, value) => {
      if (value === null || value === undefined || value === "") {
        return "—";
      }
      if (model !== "issue") {
        return String(value);
      }
      const label = lookupLabelOf(field, value);
      return label === "" ? String(value) : label;
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
      entry.error = "";
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

    const refusal = (body, fallback) =>
      firstError(body.errors) || body.message || fallback;


    lookupHooks.notice = (message, kind) => setStatus(message, kind);
    lookupHooks.created = (field, row) => {
      createdLookups.push({ field, name: row.name });
      paint();
    };

    /** A typed name with no row behind it cannot be sent as an id. */
    const refuseUnresolved = () => {
      const control = unresolvedLookup();
      if (!control) {
        return false;
      }
      control.classList.add("dd-input-invalid");
      setStatus(
        (lookupTexts.unresolved || "%(name)s").replace(
          "%(name)s",
          control.value.trim()
        ),
        "error"
      );
      control.focus();
      control.scrollIntoView({ block: "nearest" });
      return true;
    };

    /** Rings the cells a refused row names, so the row is not the only hint. */
    const markStampCells = (row, errors) => {
      if (!row || !errors || typeof errors !== "object") {
        return;
      }
      Object.keys(errors).forEach((name) => {
        const cell = fieldOf[name] ? row.getCell(fieldOf[name]) : null;
        if (cell) {
          cell.getElement().classList.add("dd-cell-invalid");
        }
      });
    };

    const clearStampMarks = () => {
      grid.getRows().forEach((row) => {
        row.getCells().forEach((cell) => {
          cell.getElement().classList.remove("dd-cell-invalid");
        });
      });
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
              /* The ids a draft carries mean nothing without their names: a
               * lookup change restored into a page that never searched it would
               * show an id and undo into an empty box. */
              lookups: Array.from(lookupById.entries()),
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

    /** One entry per object, grouped by model, with every field that differs. */
    const renderReview = () => {
      const groups = { issue: [], stamp: [] };
      buffer.forEach((entry, key) => {
        const fields = Object.keys(entry.patch);
        if (!fields.length) {
          return;
        }
        groups[entry.model].push({ key, entry, fields });
      });

      reviewBody.textContent = "";
      ["issue", "stamp"].forEach((model) => {
        if (!groups[model].length) {
          return;
        }
        const group = document.createElement("div");
        group.className = "dd-review-group";
        const title = document.createElement("span");
        title.className = "dd-review-model";
        title.textContent = (config.modelLabels || {})[model] || model;
        group.append(title);

        groups[model].forEach(({ entry, fields }) => {
          const item = document.createElement("div");
          item.className = "dd-review-item";

          const name = document.createElement("span");
          name.className = "dd-review-name";
          name.textContent = rowName(entry);
          item.append(name);

          fields.forEach((field) => {
            const line = document.createElement("div");
            line.className = "dd-review-diff";

            const label = document.createElement("span");
            label.className = "dd-review-field";
            label.textContent = fieldLabel(model, field);

            const from = document.createElement("span");
            from.className = "dd-review-from";
            from.textContent = displayValue(
              model,
              field,
              (bases.get(keyOf(model, entry.object_id)) || {})[field]
            );

            const arrow = document.createElement("span");
            arrow.className = "dd-review-arrow";
            arrow.textContent = "→";

            const to = document.createElement("span");
            to.className = "dd-review-to";
            to.textContent = displayValue(model, field, entry.patch[field]);

            line.append(label, from, arrow, to);
            item.append(line);
          });

          if (entry.error) {
            const problem = document.createElement("div");
            problem.className = "dd-review-error";
            problem.textContent = entry.error;
            item.append(problem);
          }

          group.append(item);
        });

        reviewBody.append(group);
      });

      /* Reference rows were written when they were created, so they are not
       * pending: they are listed apart, with the reason they are not. */
      if (createdLookups.length) {
        const group = document.createElement("div");
        group.className = "dd-review-group";
        const title = document.createElement("span");
        title.className = "dd-review-model";
        title.textContent = lookupTexts.newRows || "";
        group.append(title);

        createdLookups.forEach((row) => {
          const item = document.createElement("div");
          item.className = "dd-review-item";
          const name = document.createElement("span");
          name.className = "dd-review-name";
          name.textContent =
            ((config.lookupLabels || {})[row.field] || row.field) +
            " · " +
            row.name;
          item.append(name);

          const note = document.createElement("div");
          note.className = "dd-review-diff dd-review-note";
          note.textContent = lookupTexts.savedRow || "";
          item.append(note);
          group.append(item);
        });

        reviewBody.append(group);
      }
    };

    /** How a row is named in the panel: what the user recognises it by. */
    const rowName = (entry) => {
      if (entry.model === "issue") {
        const control = controlOf("name");
        return control && control.value ? control.value : String(entry.object_id);
      }
      const row = grid.getRow(entry.object_id);
      if (!row) {
        return String(entry.object_id);
      }
      const data = row.getData();
      return [data.edifil, data.name].filter(Boolean).join(" · ") || String(entry.object_id);
    };

    const paint = () => {
      const count = changeCount();
      counter.textContent = count ? plural("changes", count) : "";
      undoButton.disabled = pointer === 0;
      redoButton.disabled = pointer >= history.length;
      reviewButton.disabled = count === 0 && createdLookups.length === 0;
      saveButton.disabled = count === 0;
      saveButton.textContent = count ? plural("commit", count) : commitLabel;
      discardButton.disabled = count === 0;
      backupButton.hidden = count < (config.backupThreshold || 0);
      /* Copying and deleting are decisions about the row, not edits to it: a
       * copy is made from the database and a deletion ignores the screen, so
       * neither can run while there is something waiting to be committed. */
      cloneButton.disabled = count > 0;
      deleteButton.disabled = count > 0;
      cloneButton.title = count > 0 ? texts.commitFirst || "" : "";
      deleteButton.title = count > 0 ? texts.commitFirst || "" : "";
      /* The per-row delete cannot run with a change set open; dimming it is
       * the cue, refusing on click is the rule. */
      document
        .getElementById("stamp-grid")
        .classList.toggle("dd-grid-locked", count > 0);
      paintRows();
      /* Undo and a restored draft can change the description under the pane. */
      paintPreview(selectedRow());
      if (!reviewPanel.hidden) {
        renderReview();
      }
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
      /* The pane writes the description into this cell, and undo replays values
       * through it: neither is a user edit, and neither may push history. */
      if (quietCell === cell) {
        return;
      }
      const row = cell.getRow();
      const id = row.getData().id;
      const field = patchOf[cell.getField()];
      const from = cell.getOldValue();
      const to = cell.getValue();

      cell.getElement().classList.remove("dd-cell-invalid");

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
        previous[control.name] = formValue(control);
      }
    });

    form.addEventListener("input", (event) => {
      const control = event.target;
      if (!control.name) {
        return;
      }
      /* The ring described the value that was sent, not the one on screen. */
      control.classList.remove("dd-input-invalid");
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
      const value = formValue(control);
      push({
        model: "issue",
        id: config.series.id,
        field: control.name,
        from: control.name in previous ? previous[control.name] : loaded[control.name],
        to: value,
      });
      previous[control.name] = value;
    });

    /* The description is edited in the pane, not in a cell. Its value lives in
     * the hidden column, so from here on it behaves like any other field.
     * `previewStart` is the value the field had when it took the focus: a
     * cell's `getOldValue()` is the value it had when the page was built, not
     * the one the user is editing. */
    previewHooks.input = (row, value) => {
      const id = row.getData().id;
      remember("stamp", id, "description", previewStart);
      writeCell(descriptionCell(row), value);
      sync("stamp", id);
      paint();
    };

    previewHooks.commit = (row, value) => {
      if (same(previewStart, value)) {
        return;
      }
      push({
        model: "stamp",
        id: row.getData().id,
        field: "description",
        from: previewStart,
        to: value,
      });
    };

    /* ---------------------------------------------------------------- *
     * Committing and discarding.
     * -------------------------------------------------------------- */

    const commit = async () => {
      if (refuseUnresolved()) {
        return;
      }

      const changes = Array.from(buffer.values()).filter(
        (entry) => Object.keys(entry.patch).length
      );
      if (!changes.length) {
        setStatus(texts.noChanges, "");
        return;
      }

      clearStampMarks();
      clearFieldMarks(form);
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
          const control = markFields(form, problem.errors);
          markStrip(form, !control);
          if (control) {
            control.focus();
            control.scrollIntoView({ block: "nearest" });
          }
          return;
        }
        const row = grid.getRow(change.object_id);
        if (row) {
          row.getElement().classList.add("dd-row-error");
          markStampCells(row, problem.errors);
        }
      });

      if (rows.length) {
        loaded = formValues();
      }

      rejected.forEach((problem) => {
        const change = changes[problem.index];
        const entry = buffer.get(keyOf(change.model, change.object_id));
        if (entry) {
          entry.error = firstError(problem.errors) || texts.rejected;
        }
      });

      if (rejected.length) {
        setStatus(firstError(rejected[0].errors) || texts.rejected, "error");
        openReview();
        paint();
        return;
      }

      /* Everything landed: the workbench is where the next series is, with the
       * one just saved in front of the user. */
      window.location.assign(config.issuesUrl + "?focus=" + config.series.id);
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
      reviewPanel.hidden = true;
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
        if (event.ctrlKey || event.metaKey) {
          return;
        }
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

    const openReview = () => {
      reviewPanel.hidden = false;
      renderReview();
    };

    reviewButton.addEventListener("click", openReview);
    reviewClose.addEventListener("click", () => {
      reviewPanel.hidden = true;
    });

    backupButton.addEventListener("click", async () => {
      backupButton.disabled = true;
      backupStatus.textContent = texts.saving;
      try {
        const response = await fetch(config.backupUrl, {
          method: "POST",
          headers: { "X-CSRFToken": csrfToken() },
        });
        const body = await response.json();
        if (!body.success) {
          throw new Error(body.message || texts.backupFailed);
        }
        backupStatus.textContent = texts.backupSaved.replace(
          "%(file)s",
          body.data.file
        );
      } catch (error) {
        backupStatus.textContent = texts.backupFailed;
      } finally {
        backupButton.disabled = false;
      }
    });

    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && !reviewPanel.hidden) {
        reviewPanel.hidden = true;
        event.stopImmediatePropagation();
        return;
      }
      if (event.key === "Enter" && (event.ctrlKey || event.metaKey)) {
        event.preventDefault();
        commitTarget();
      }
    });

    /* [ and ] walk the list the user came from. The arrows are links in the
     * page, so the keyboard and the mouse cannot disagree about the neighbour;
     * a field keeps its brackets. */
    document.addEventListener("keydown", (event) => {
      if (event.ctrlKey || event.metaKey || event.altKey) {
        return;
      }
      if (event.key !== "[" && event.key !== "]") {
        return;
      }
      const target = event.target;
      if (
        target instanceof Element &&
        target.closest("input, select, textarea")
      ) {
        return;
      }
      const link = document.getElementById(
        event.key === "[" ? "nav-previous" : "nav-next"
      );
      if (link && link.href) {
        event.preventDefault();
        window.location.assign(link.href);
      }
    });

    /* ---------------------------------------------------------------- *
     * Deleting one stamp: its own preview, its own dialog.
     *
     * It is not an edit, so it cannot queue behind the change set: with
     * something pending the button refuses and says why, the same rule the
     * series-level Clone and Delete follow.
     * -------------------------------------------------------------- */

    let deletingStamp = null;

    const closeStampDelete = () => {
      stampPanel.hidden = true;
      deletingStamp = null;
    };

    const openStampDelete = async (row) => {
      if (changeCount() > 0) {
        setStatus(texts.commitFirst, "error");
        return;
      }

      deletingStamp = row;
      stampPanel.hidden = false;
      stampWarning.textContent = "";
      stampIdentity.textContent = "";
      stampStatus.textContent = "";
      stampItems.textContent = "·";
      stampCollections.textContent = "·";
      stampConfirm.disabled = true;

      let body = null;
      try {
        const response = await fetch(row.dependencies_url, {
          headers: { Accept: "application/json" },
        });
        body = await response.json();
      } catch (error) {
        body = null;
      }
      if (!body || !body.success || !body.data) {
        stampStatus.textContent = (body && body.message) || texts.previewFailed;
        return;
      }

      const data = body.data;
      stampItems.textContent = data.items;
      stampCollections.textContent = data.collections;
      stampWarning.textContent = data.warning;
      stampIdentity.textContent = [data.code, data.name].filter(Boolean).join(" · ");
      stampConfirm.disabled = false;
    };

    const confirmStampDelete = async () => {
      if (!deletingStamp) {
        return;
      }
      const row = deletingStamp;
      stampConfirm.disabled = true;
      stampStatus.textContent = texts.deleting;

      let body = null;
      try {
        body = await post(row.delete_url, {});
      } catch (error) {
        body = null;
      }
      if (!body || !body.success) {
        stampConfirm.disabled = false;
        stampStatus.textContent =
          firstError(body && body.errors) ||
          (body && body.message) ||
          texts.stampDeleteFailed;
        return;
      }

      closeStampDelete();
      const gridRow = grid.getRow(row.id);
      if (gridRow) {
        gridRow.delete();
      }
      if (badge) {
        badge.textContent = String(Math.max(grid.getRows().length, 0));
      }
      setStatus(texts.stampDeleted, "ok");
    };

    deleteStampRow = openStampDelete;
    stampClose.addEventListener("click", closeStampDelete);
    stampCancel.addEventListener("click", closeStampDelete);
    stampConfirm.addEventListener("click", confirmStampDelete);
    stampPanel.addEventListener("click", (event) => {
      if (event.target === stampPanel) {
        closeStampDelete();
      }
    });
    stampPanel.addEventListener("keydown", (event) => {
      if (event.key === "Escape") {
        event.stopPropagation();
        closeStampDelete();
      }
    });

    /* ---------------------------------------------------------------- *
     * Cloning and deleting: the two things that end this series.
     * -------------------------------------------------------------- */

    /** Posts a JSON body and reads the answer whatever the status is. */
    const post = async (url, body) => {
      const response = await fetch(url, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken(),
        },
        body: JSON.stringify(body || {}),
      });
      return response.json().catch(() => ({ success: false }));
    };

    /* A copy is a new series: whatever the user does next happens to it, so the
     * workspace moves there instead of leaving them on the origin wondering
     * which of the two they are editing. */
    cloneButton.addEventListener("click", async () => {
      cloneButton.disabled = true;
      setStatus(texts.cloning, "pending");
      let body = null;
      try {
        body = await post(config.cloneUrl, {});
      } catch (error) {
        body = null;
      }
      if (!body || !body.success || !body.data || !body.data.url) {
        cloneButton.disabled = false;
        setStatus((body && body.message) || texts.cloneFailed, "error");
        return;
      }
      window.location.assign(body.data.url);
    });

    const closeDelete = () => {
      deletePanel.hidden = true;
      deleteStatus.textContent = "";
    };

    /* The numbers come from the server when the dialog opens, not from the page
     * the user loaded minutes ago: a collection item added since would make the
     * preview a lie, and this is the one dialog where that matters. */
    const openDelete = async () => {
      deletePanel.hidden = false;
      deleteStatus.textContent = "";
      deleteConfirm.value = "";
      deleteWarning.textContent = "";
      Object.keys(deleteCounts).forEach((key) => {
        deleteCounts[key].textContent = "·";
      });
      deleteConfirmButton.disabled = true;
      deleteConfirm.focus();

      let body = null;
      try {
        const response = await fetch(config.dependenciesUrl, {
          headers: { Accept: "application/json" },
        });
        body = await response.json();
      } catch (error) {
        body = null;
      }
      if (!body || !body.success || !body.data) {
        deleteStatus.textContent =
          (body && body.message) || texts.previewFailed;
        return;
      }

      const data = body.data;
      Object.keys(deleteCounts).forEach((key) => {
        deleteCounts[key].textContent = data[key];
      });
      deleteWarning.textContent = data.warning;
      if (texts.confirmYear) {
        deleteConfirmLabel.textContent = texts.confirmYear.replace(
          "%(year)s",
          data.year
        );
      }
      deleteConfirmButton.disabled = false;
    };

    const confirmDelete = async () => {
      deleteConfirmButton.disabled = true;
      deleteStatus.textContent = texts.deleting;
      let body = null;
      try {
        body = await post(config.deleteUrl, { confirm: deleteConfirm.value });
      } catch (error) {
        body = null;
      }
      if (!body || !body.success) {
        deleteConfirmButton.disabled = false;
        deleteStatus.textContent =
          firstError(body && body.errors) ||
          (body && body.message) ||
          texts.deleteFailed;
        return;
      }
      /* The row this page was showing does not exist anymore. */
      window.location.assign(config.issuesUrl);
    };

    deleteButton.addEventListener("click", openDelete);
    deleteClose.addEventListener("click", closeDelete);
    deleteCancel.addEventListener("click", closeDelete);
    deleteConfirmButton.addEventListener("click", confirmDelete);
    deletePanel.addEventListener("click", (event) => {
      if (event.target === deletePanel) {
        closeDelete();
      }
    });
    deleteConfirm.addEventListener("keydown", (event) => {
      if (event.key === "Enter") {
        event.preventDefault();
        confirmDelete();
      }
    });
    /* Esc closes the dialog and goes no further: leaving the page with the
     * dialog open would be the wrong escape. */
    deletePanel.addEventListener("keydown", (event) => {
      if (event.key === "Escape") {
        event.stopPropagation();
        closeDelete();
      }
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
        (draft.lookups || []).forEach(([key, label]) => {
          const split = key.indexOf(":");
          rememberLookup(key.slice(0, split), key.slice(split + 1), label);
        });
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

  /* --------------------------------------------------------------------- *
   * mode=new: the rows live here and the page writes them once.
   *
   * The rows exist only in this tab until Create is pressed: no request, no
   * database row, so reloading throws the draft away on purpose. The one thing
   * that survives is the "Create another" loop, and it survives because the
   * server renders the next page with the values of the series just saved.
   * ------------------------------------------------------------------- */

  const newMode = () => {
    const nameInput = document.getElementById(config.nameInput);
    const rowsInput = document.getElementById(config.rowsInput);
    const badge = document.getElementById(config.countBadge);
    const fillButton = document.getElementById(config.fillButton);
    const fastToggle = document.getElementById(config.fastToggle);
    const createButton = document.getElementById(config.createButton);
    const createStatus = document.getElementById(config.createStatus);
    const createdBar = document.getElementById(config.createdBar);
    const createdText = document.getElementById(config.createdText);
    const createdOpen = document.getElementById(config.createdOpen);
    const createdAgain = document.getElementById(config.createdAgain);
    const form = document.getElementById("series-form");
    const texts = config.texts || {};
    let nextId = 1;
    let created = false;
    /** Where the caret last was: Ctrl+D and a paste both start from there. */
    let current = null;

    /** Row field -> model field, taken from the same definitions the grid uses. */
    const patchOf = {};
    config.columns.forEach((column) => {
      if (column.patch) {
        patchOf[column.field] = column.patch;
      }
    });

    const editableFields = () =>
      grid
        .getColumns()
        .filter((column) => column.isVisible() && patchOf[column.getField()])
        .map((column) => column.getField());

    const setStatus = (message, kind) => {
      createStatus.textContent = message || "";
      createStatus.className = kind ? "dd-hint dd-status-" + kind : "dd-hint";
    };

    /** The label the form uses, sent by the server like every other text. */
    const labelOf = (field) =>
      ((config.fieldLabels || {}).issue || {})[field] || field;

    /* A mark disappears as soon as that field is edited: it describes what the
     * server said about the value it was sent, not the value on screen now. */
    form.addEventListener("input", (event) => {
      markStrip(form, false);
      if (event.target.classList) {
        event.target.classList.remove("dd-input-invalid");
      }
    });

    /** Rings the cells the server refused and returns how many it marked. */
    const markCells = (stampErrors, draft) => {
      const gridFieldOf = {};
      Object.entries(patchOf).forEach(([field, name]) => {
        gridFieldOf[name] = field;
      });
      const row = draft ? grid.getRow(draft.id) : null;
      if (!row || !stampErrors || typeof stampErrors !== "object") {
        return 0;
      }
      let marked = 0;
      Object.keys(stampErrors).forEach((name) => {
        const cell = gridFieldOf[name] ? row.getCell(gridFieldOf[name]) : null;
        if (!cell) {
          return;
        }
        cell.getElement().classList.add("dd-cell-invalid");
        marked += 1;

        /* A bad value in a column the fast row hides has nowhere to show the
         * ring, so the grid opens up: the message would point at nothing. */
        const column = cell.getColumn ? cell.getColumn() : null;
        if (column && !column.isVisible() && fastToggle && fastToggle.checked) {
          fastToggle.checked = false;
          applyFastRow();
        }
      });
      return marked;
    };

    const clearCellMarks = () => {
      grid.getRows().forEach((row) => {
        row.getCells().forEach((cell) => {
          cell.getElement().classList.remove("dd-cell-invalid");
        });
      });
    };

    /** A row as a new stamp starts: name only, and empty everything else. */
    const emptyRow = () => ({
      id: config.rowIdPrefix + nextId++,
      edifil: "",
      fesofi: "",
      name: nameInput.value,
      description: "",
      face_value: "",
      colors: [],
      total_printed: null,
      mnh: null,
      used: null,
      has_image: false,
      image_url: null,
      touched: false,
    });

    /** Whether a row carries anything the user typed into it. */
    const touched = (row) =>
      row.name !== nameInput.value ||
      ["edifil", "fesofi", "face_value", "total_printed", "mnh", "used",
       "description"].some(
        (field) =>
          row[field] !== null && row[field] !== undefined && row[field] !== ""
      ) ||
      (row.colors || []).length > 0;

    /** Paints the grid from the drafts and keeps the counter honest. */
    const render = () => {
      /* `setData` replaces every row, and with them the selection: the pane
       * goes back to the same draft if it still exists. */
      const current = selectedRow();
      const selectedId = current ? current.getData().id : null;
      grid.setData(drafts);
      const again = selectedId ? grid.getRow(selectedId) : null;
      if (again) {
        again.select();
      } else {
        paintPreview(null);
      }
      badge.textContent = String(drafts.length);
      rowsInput.value = String(drafts.length);
    };

    /** Adds or trims rows to reach N, never touching one already edited.
     *
     * Growing appends; shrinking drops untouched rows from the bottom and
     * stops at the first touched one, so lowering N cannot destroy work.
     */
    const resize = () => {
      const requested =
        Number.parseInt(rowsInput.value, 10) || config.rows.default;
      const target = clamp(requested, config.rows.min, config.rows.max);

      while (drafts.length < target) {
        drafts.push(emptyRow());
      }
      while (drafts.length > target && !touched(drafts[drafts.length - 1])) {
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

    /* ---------------------------------------------------------------- *
     * Fast row: four columns while typing, everything once the series exists.
     * -------------------------------------------------------------- */

    const applyFastRow = () => {
      const only = new Set((config.fastRow || {}).fields || []);
      if (!fastToggle || !only.size) {
        return;
      }
      grid.getColumns().forEach((column) => {
        /* A field with no column of its own stays hidden whatever the mode. */
        if (column.getDefinition().visible === false) {
          return;
        }
        const field = column.getField();
        if (fastToggle.checked) {
          if (!only.has(field)) {
            grid.hideColumn(field);
          }
        } else {
          grid.showColumn(field);
        }
      });
    };

    if (fastToggle) {
      /* The server owns the default: the template ships the control checked so
       * the page does not flash a full grid before the script runs. */
      fastToggle.checked = (config.fastRow || {}).on !== false;
      /* applyFastRow(); */
      fastToggle.addEventListener("change", applyFastRow);
    }

    /* ---------------------------------------------------------------- *
     * Undo inside the session: the draft is never stored, but Ctrl+Z has to
     * work while the tab is open. Row id and field are kept instead of the cell
     * component: `render()` replaces the rows, so a held cell goes stale.
     * -------------------------------------------------------------- */

    const history = [];
    let pointer = 0;

    /** One undo step: the value a field had and the value it has now. */
    const record = (id, field, from, to) => {
      history.length = pointer;
      history.push({ id, field, from, to });
      while (history.length > (config.undoLimit || 200)) {
        history.shift();
      }
      pointer = history.length;
    };

    grid.on("cellEdited", (cell) => {
      /* The pane writes the description here, and undo replays values: neither
       * is a new edit. */
      if (quietCell === cell) {
        return;
      }
      const edited = cell.getRow().getData();
      const row = drafts.find((draft) => draft.id === edited.id);
      if (row) {
        row[cell.getField()] = cell.getValue();
        row.touched = touched(row);
      }
      cell.getElement().classList.remove("dd-cell-invalid");
      current = { id: edited.id, field: cell.getField() };
      record(edited.id, cell.getField(), cell.getOldValue(), cell.getValue());
    });

    grid.on("cellClick", (event, cell) => {
      if (cell.getField() === "remove") {
        removeRow(cell.getRow().getData().id);
        return;
      }
      current = { id: cell.getRow().getData().id, field: cell.getField() };
    });

    grid.on("cellEditing", (cell) => {
      current = { id: cell.getRow().getData().id, field: cell.getField() };
    });

    const step = (direction) => {
      const operation =
        direction < 0 ? history[pointer - 1] : history[pointer];
      if (!operation) {
        return;
      }

      /* A removed row comes back where it was, and goes away again. */
      if (operation.kind === "remove") {
        if (direction < 0) {
          drafts.splice(operation.index, 0, operation.row);
        } else {
          drafts.splice(drafts.indexOf(operation.row), 1);
        }
        pointer += direction;
        render();
        return;
      }

      const draft = drafts.find((row) => row.id === operation.id);
      const value = direction < 0 ? operation.from : operation.to;
      if (draft) {
        draft[operation.field] = value;
        draft.touched = touched(draft);
      }
      const gridRow = grid.getRow(operation.id);
      const cell = gridRow && gridRow.getCell(operation.field);
      if (cell) {
        writeCell(cell, value);
      }
      pointer += direction;
      /* The pane shows what the cell says: a replayed value is no exception. */
      paintPreview(selectedRow());
    };

    /* ---------------------------------------------------------------- *
     * Numbering, duplicating and pasting: the three ways to avoid typing
     * eight nearly identical rows by hand.
     * -------------------------------------------------------------- */

    /** a -> b, z -> aa: the letters move, the number stays. */
    const bumpLetters = (suffix) => {
      const letters = suffix.toLowerCase().split("");
      let index = letters.length - 1;
      while (index >= 0) {
        if (letters[index] === "z") {
          letters[index] = "a";
          index -= 1;
        } else {
          letters[index] = String.fromCharCode(letters[index].charCodeAt(0) + 1);
          return letters.join("");
        }
      }
      return "a" + letters.join("");
    };

    /** 2744 -> 2745, 2744a -> 2744b, 0069 -> 0070; null when not a code. */
    const nextCode = (code) => {
      const match = /^(.*?)(\d+)([a-z]*)$/i.exec(code);
      if (!match) {
        return null;
      }
      const [, prefix, digits, suffix] = match;
      if (suffix) {
        return prefix + digits + bumpLetters(suffix);
      }
      return prefix + String(Number(digits) + 1).padStart(digits.length, "0");
    };

    /** The column numbered from its first row: `codes`, `empty` or `stuck`. */
    const numbering = (field) => {
      const start = String((drafts[0] || {})[field] || "").trim();
      if (!start) {
        return { empty: true };
      }
      const codes = [start];
      for (let index = 1; index < drafts.length; index += 1) {
        const next = nextCode(codes[codes.length - 1]);
        if (!next) {
          return { stuck: true };
        }
        codes.push(next);
      }
      return { codes };
    };

    /** Numbers every code column that has a first value, or says why not.
     *
     * Both catalogues number the same set and a series usually carries one of
     * them, so an empty column is skipped in silence. Every column is planned
     * before any is written: a refusal on the second must not leave the first
     * half-numbered.
     */
    const fillSeries = () => {
      const plans = [];
      let stuck = null;
      let found = false;

      (config.fillColumns || []).forEach((column) => {
        const plan = numbering(column.field);
        if (plan.empty) {
          return;
        }
        found = true;
        if (plan.stuck) {
          stuck = stuck || column.label;
          return;
        }
        plans.push({ field: column.field, codes: plan.codes });
      });

      if (stuck) {
        setStatus(
          (texts.fillImpossible || "%(column)s").replace("%(column)s", stuck),
          "error"
        );
        return;
      }
      if (!found) {
        setStatus(texts.fillNeedsFirst, "error");
        return;
      }

      plans.forEach(({ field, codes }) => {
        codes.forEach((value, index) => {
          const gridRow = grid.getRow(drafts[index].id);
          const cell = gridRow && gridRow.getCell(field);
          if (cell && String(drafts[index][field] || "") !== value) {
            cell.setValue(value, false);
          }
        });
      });
      setStatus("", "");
    };

    if (fillButton) {
      fillButton.addEventListener("click", fillSeries);
    }

    /** Drops one row, remembering where it was so Ctrl+Z can put it back. */
    const removeRow = (id) => {
      const index = drafts.findIndex((row) => row.id === id);
      if (index === -1) {
        return;
      }
      const [row] = drafts.splice(index, 1);
      history.length = pointer;
      history.push({ kind: "remove", row, index });
      while (history.length > (config.undoLimit || 200)) {
        history.shift();
      }
      pointer = history.length;
      render();
      setStatus("", "");
    };

    /** Copies the row the caret is in, just below it. */
    const duplicate = () => {
      const anchor = current
        ? drafts.find((row) => row.id === current.id)
        : drafts[drafts.length - 1];
      if (!anchor) {
        return;
      }
      const copy = {
        ...anchor,
        id: config.rowIdPrefix + nextId++,
        colors: [...(anchor.colors || [])],
      };
      drafts.splice(drafts.indexOf(anchor) + 1, 0, copy);
      render();
      setStatus("", "");
    };

    /** Spreads a block of tab-separated values from the caret onwards. */
    const pasteAt = (startId, startField, text) => {
      const fields = editableFields();
      const column = Math.max(fields.indexOf(startField), 0);
      let rowIndex = Math.max(
        drafts.findIndex((row) => row.id === startId),
        0
      );

      text
        .replace(/\r\n?/g, "\n")
        .replace(/\n$/, "")
        .split("\n")
        .forEach((line) => {
          const values = line.split("\t");
          const draft = drafts[rowIndex];
          if (draft) {
            values.forEach((value, offset) => {
              const field = fields[column + offset];
              const gridRow = grid.getRow(draft.id);
              const cell = gridRow && field ? gridRow.getCell(field) : null;
              if (cell) {
                cell.setValue(value.trim(), false);
              }
            });
          }
          rowIndex += 1;
        });
    };

    const gridElement = document.getElementById("stamp-grid");
    gridElement.addEventListener("paste", (event) => {
      const data = event.clipboardData || window.clipboardData;
      const text = data ? data.getData("text/plain") : "";
      /* One value is a normal paste into the open editor. */
      if (!text || (!text.includes("\t") && !text.includes("\n"))) {
        return;
      }
      event.preventDefault();
      const anchor = current || {
        id: drafts.length ? drafts[0].id : "",
        field: "edifil",
      };
      pasteAt(anchor.id, anchor.field, text);
    });

    /* ---------------------------------------------------------------- *
     * Creating the series.
     * -------------------------------------------------------------- */

    /** The series as the form has it: only what was filled, in model names. */
    const seriesPayload = () => {
      const issue = {};
      Array.from(form.querySelectorAll("[name]")).forEach((control) => {
        const value = String(formValue(control)).trim();
        if (value !== "") {
          issue[control.name] = value;
        }
      });
      return issue;
    };

    /** One row as a stamp, keyed by model field, empty values left out. */
    const stampPayload = (row) => {
      const stamp = {};
      Object.entries(patchOf).forEach(([field, name]) => {
        const value = row[field];
        if (value === null || value === undefined || value === "") {
          return;
        }
        stamp[name] = value;
      });

      const colours = (row.colors || [])
        .map((colour) =>
          colour && typeof colour === "object" ? colour.value : colour
        )
        .filter((id) => id !== null && id !== undefined && id !== "");
      if (colours.length) {
        stamp.colors = colours;
      }
      return stamp;
    };

    /** A row nobody typed in is not a stamp: `rows=4` is a starting point. */
    const isBlank = (row) =>
      !row.touched &&
      !row.edifil &&
      !row.fesofi &&
      !row.face_value &&
      !(row.colors || []).length;

    /** Explains a refusal: the strip first, then the stamp that caused it. */
    const refuse = (body, chosen) => {
      const errors = (body && body.errors) || {};
      const stamps = errors.stamps;
      const issue = errors.issue;

      /* A refused series names its field and rings it: "Year: This field is
       * required." plus the year input in red, so the message is not a hunt. */
      if (issue && typeof issue === "object" && !Array.isArray(issue)) {
        const field = Object.keys(issue)[0];
        const control = markFields(form, issue);
        markStrip(form, !control);
        if (control) {
          control.focus();
          control.scrollIntoView({ block: "nearest" });
        }
        setStatus(labelOf(field) + ": " + firstError(issue[field]), "error");
        return;
      }

      if (stamps && typeof stamps === "object" && !Array.isArray(stamps)) {
        const index = Object.keys(stamps)[0];
        const draft = chosen[Number(index)];
        markStrip(form, false);
        if (draft) {
          const gridRow = grid.getRow(draft.id);
          if (gridRow) {
            gridRow.getElement().classList.add("dd-row-error");
          }
          markCells(stamps[index], draft);
        }
        setStatus(
          (texts.rowRefused || "%(row)s %(message)s")
            .replace("%(row)s", String(Number(index) + 1))
            .replace("%(message)s", firstError(stamps[index])),
          "error"
        );
        return;
      }

      markStrip(form, false);
      setStatus(
        firstError(errors) || (body && body.message) || texts.rejected || "",
        "error"
      );
    };

    /** Stops the workspace: the series is written and the loop takes over. */
    const showCreated = (data) => {
      created = true;
      const series = (data || {}).issue || {};
      const year = (document.getElementById("field-year") || {}).value || "";

      createdText.textContent = texts.saved || "";
      createdOpen.href = config.issuesUrl + series.id + "/";
      createdAgain.href = config.newUrl + "?from=" + series.id;
      if (year.trim() !== "") {
        createdAgain.textContent = (texts.createAnother || "").replace(
          "%(year)s",
          year.trim()
        );
      }
      createdBar.hidden = false;
      document
        .querySelector(".dd-workspace-page")
        .classList.add("dd-created-page");
      grid.getRows().forEach((row) => {
        row.getElement().classList.remove("dd-row-error");
      });
      clearCellMarks();
      setStatus("", "");
    };

    /* ---------------------------------------------------------------- *
     * A colour typed for the first time.
     *
     * The cell editor is Tabulator's list, which takes no free text, so the
     * row is created from the toolbar and added to the list the editor will
     * offer next time it opens. Editing the cell is still the only way to
     * choose it: creating a colour is not the same as putting it on a stamp.
     * -------------------------------------------------------------- */

    const colourButton = document.getElementById("new-colour");
    const colourPanel = document.getElementById("colour-panel");
    const colourName = document.getElementById("colour-name");
    const colourStatus = document.getElementById("colour-status");
    const colourCreate = document.getElementById("colour-create");

    const closeColour = () => {
      colourPanel.hidden = true;
    };

    colourButton.addEventListener("click", () => {
      colourPanel.hidden = false;
      colourName.value = "";
      colourStatus.textContent = "";
      colourStatus.className = "dd-hint";
      colourName.focus();
    });
    document.getElementById("colour-close").addEventListener("click", closeColour);
    document.getElementById("colour-cancel").addEventListener("click", closeColour);
    colourPanel.addEventListener("click", (event) => {
      if (event.target === colourPanel) {
        closeColour();
      }
    });
    colourPanel.addEventListener("keydown", (event) => {
      if (event.key === "Escape") {
        event.stopPropagation();
        closeColour();
      }
      if (event.key === "Enter") {
        event.preventDefault();
        colourCreate.click();
      }
    });

    colourCreate.addEventListener("click", async () => {
      const name = colourName.value.trim();
      if (name === "") {
        colourName.focus();
        return;
      }
      colourCreate.disabled = true;
      colourStatus.textContent = texts.saving;
      colourStatus.className = "dd-hint dd-status-pending";
      const row = await createLookupRow("color", name);
      colourCreate.disabled = false;
      if (!row) {
        colourStatus.textContent = lookupTexts.failed;
        colourStatus.className = "dd-hint dd-status-error";
        return;
      }

      /* The chip takes its tone from the palette entry, so the new colour has
       * to exist both in the page configuration and in the list the open
       * editor holds. */
      config.colours.push({
        value: row.id,
        label: row.name,
        tone: row.tone || "neutral",
      });
      const column = grid.getColumn("colors");
      const params = column && column.getDefinition().editorParams;
      if (params && params.values) {
        params.values.push({ label: row.name, value: row.id });
      }
      closeColour();
      setStatus(lookupTexts.created, "ok");
    });

    lookupHooks.notice = (message, kind) => setStatus(message, kind);

    /** A typed name with no row behind it cannot be sent as an id. */
    const refuseUnresolved = () => {
      const control = unresolvedLookup();
      if (!control) {
        return false;
      }
      control.classList.add("dd-input-invalid");
      setStatus(
        (lookupTexts.unresolved || "%(name)s").replace(
          "%(name)s",
          control.value.trim()
        ),
        "error"
      );
      control.focus();
      control.scrollIntoView({ block: "nearest" });
      return true;
    };

    const create = async () => {
      if (created) {
        return;
      }
      if (refuseUnresolved()) {
        return;
      }
      const chosen = drafts.filter((row) => !isBlank(row));

      /* A new attempt starts clean: the previous marks described the values
       * that were sent then, and the user has changed some of them. */
      clearFieldMarks(form);
      clearCellMarks();
      createButton.disabled = true;
      setStatus(texts.saving, "pending");

      let body = null;
      try {
        const response = await fetch(config.createUrl, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrfToken(),
          },
          body: JSON.stringify({
            issue: seriesPayload(),
            stamps: chosen.map(stampPayload),
          }),
        });
        body = await response.json();
      } catch (error) {
        body = null;
      }

      if (!body || !body.success) {
        createButton.disabled = false;
        refuse(body, chosen);
        return;
      }

      showCreated(body.data);
    };

    /* The open editor has to lose the focus first: Tabulator writes the typed
     * value into the row on blur, and the payload reads the row. */
    const createTarget = async () => {
      const active = document.activeElement;
      if (active && active !== document.body) {
        active.blur();
      }
      await Promise.resolve();
      create();
    };

    document.addEventListener("keydown", (event) => {
      if (event.key === "Enter" && event.shiftKey) {
        if (event.ctrlKey || event.metaKey) {
          return;
        }
        event.preventDefault();
        createTarget();
        return;
      }
      if (!(event.ctrlKey || event.metaKey)) {
        return;
      }
      const key = event.key.toLowerCase();
      if (key === "d") {
        event.preventDefault();
        duplicate();
        return;
      }
      if (key !== "z") {
        return;
      }
      /* Inside the strip the browser's own undo is the one the user means;
       * a cell editor is not in the form, so row undo works there. */
      if (event.target && form.contains(event.target)) {
        return;
      }
      event.preventDefault();
      step(event.shiftKey ? 1 : -1);
    });

    if (createButton) {
      createButton.addEventListener("click", createTarget);
    }

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

    /* The date decides the year: a series is dated once, not twice. While a
     * date is set the year follows it and cannot be typed over — "1987" with a
     * 2026 date is not a series anyone meant. Clearing the date hands the year
     * back, which is how a series with no exact date is still entered. */
    const dateInput = document.getElementById("field-date");
    const syncYearFromDate = () => {
      if (!dateInput || !yearInput) {
        return;
      }
      const iso = dateInput.value.trim();
      const dated = /^\d{4}-\d{2}-\d{2}$/.test(iso);
      if (dated) {
        yearInput.value = iso.slice(0, 4);
      }
      yearInput.readOnly = dated;
      yearInput.classList.toggle("dd-input-derived", dated);
      yearInput.title = dated ? texts.yearFromDate || "" : "";
      syncYearHint();
    };

    if (dateInput) {
      dateInput.addEventListener("input", syncYearFromDate);
      dateInput.addEventListener("change", syncYearFromDate);
    }

    /** A field that just took its prefilled value says so for a moment. */
    const flash = (control) => {
      control.classList.add("dd-applied");
      window.setTimeout(() => control.classList.remove("dd-applied"), 900);
    };

    /** The value the prefill would put in one field. */
    const prefillValue = (value) =>
      value && typeof value === "object" ? String(value.value) : String(value);

    /** Whether any prefilled field differs from what the button would set. */
    const prefillDiffers = () =>
      Object.entries(config.prefill || {}).some(([field, value]) => {
        const control = document.getElementById("field-" + field);
        if (!control) {
          return false;
        }
        const current = control.dataset.lookup ? formValue(control) : control.value;
        return String(current) !== prefillValue(value);
      });

    const useLastIssue = document.getElementById("use-last-issue");
    const paintPrefill = () => {
      if (useLastIssue) {
        useLastIssue.disabled = !prefillDiffers();
      }
    };

    const applyPrefill = () => {
      const applied = [];
      Object.entries(config.prefill || {}).forEach(([field, value]) => {
        const control = document.getElementById("field-" + field);
        if (!control) {
          return;
        }
        const before = control.dataset.lookup ? formValue(control) : control.value;

        if (!control.dataset.lookup) {
          control.value = String(value);
        } else {
          /* A lookup travels as {value, label}: the id is what the API needs
           * and the name is what the box has to show. */
          const id = value && typeof value === "object" ? value.value : value;
          const label = value && typeof value === "object" ? value.label : "";
          rememberLookup(field, id, label);
          setLookup(control, field, id);
        }

        const after = control.dataset.lookup ? formValue(control) : control.value;
        if (String(before) !== String(after)) {
          applied.push(control);
        }
      });
      /* A prefilled year cannot win over a date the page already carries. */
      syncYearFromDate();
      applied.forEach(flash);
      paintPrefill();
    };

    if (useLastIssue) {
      useLastIssue.addEventListener("click", applyPrefill);
      form.addEventListener("input", paintPrefill);
      form.addEventListener("change", paintPrefill);
    }

    /* Tabulator builds asynchronously and `setData` inside the same tick finds
     * no layout yet and throws, so the rows wait for the table. */
    grid.on("tableBuilt", () => {
      resize();
    });
    syncYearFromDate();
    paintPrefill();

    /* Dirty means the series form changed or the row set did. The guard only
     * fires then: warning someone off an empty form teaches them to ignore it,
     * and a created series has nothing left to lose. */
    const snapshot = () =>
      JSON.stringify({
        fields: Array.from(form.querySelectorAll("[name]")).map(
          (control) => control.value
        ),
        rows: drafts.map((row) => row.id),
      });
    const initial = snapshot();

    window.addEventListener("beforeunload", (event) => {
      if (created || snapshot() === initial) {
        return;
      }
      event.preventDefault();
      event.returnValue = "";
    });

    /* The description is typed in the pane; the value lands in the hidden
     * column so the draft and the create payload carry it like any other. */
    previewHooks.input = (row, value) => {
      const cell = descriptionCell(row);
      writeCell(cell, value);
      const draft = drafts.find((item) => item.id === row.getData().id);
      if (draft) {
        draft.description = value;
        draft.touched = touched(draft);
      }
    };

    previewHooks.commit = (row, value) => {
      if (previewStart === value) {
        return;
      }
      record(row.getData().id, "description", previewStart, value);
    };
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
