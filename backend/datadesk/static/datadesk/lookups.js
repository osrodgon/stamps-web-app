/* Reference tables screen.
 *
 * One grid for the eight lookups: the server sends the column titles, every
 * text this file shows and the URLs, so nothing here is a string a person
 * reads. The rows come paginated with their usage counts, which is what makes
 * "delete" honest: a row in use cannot be deleted, it has to be merged.
 */
(() => {
  "use strict";

  const config = JSON.parse(
    document.getElementById("lookup-config").textContent
  );
  const texts = config.texts || {};
  const plurals = config.plurals || {};

  const search = document.getElementById("lookup-search");
  const countLabel = document.getElementById("lookup-count");
  const status = document.getElementById("lookup-status");
  const mergeButton = document.getElementById("merge-button");
  const mergePanel = document.getElementById("merge-panel");
  const mergeRows = document.getElementById("merge-rows");
  const mergeWarning = document.getElementById("merge-warning");
  const mergeStatus = document.getElementById("merge-status");
  const mergeConfirm = document.getElementById("merge-confirm");
  const deletePanel = document.getElementById("delete-panel");
  const deleteWarning = document.getElementById("delete-warning");
  const deleteStatus = document.getElementById("delete-status");
  const deleteConfirm = document.getElementById("delete-confirm");
  const nextYears = document.getElementById("next-years");

  const DEBOUNCE_MS = 300;
  let total = 0;
  let timer = null;
  /** The two rows the merge dialog is talking about, if it is open. */
  let merging = null;
  /** The row the delete dialog is talking about, if it is open. */
  let deleting = null;

  /** Resolves a plural template with one number, both from the server. */
  const plural = (kind, count) => {
    const forms = plurals[kind];
    if (!forms) {
      return String(count);
    }
    const template = count === 1 ? forms.one : forms.other;
    return template.replace("%(count)s", String(count));
  };

  const setStatus = (message, kind) => {
    status.textContent = message || "";
    status.className = kind ? "dd-hint dd-status-" + kind : "dd-hint";
  };

  /** Posts JSON and reads the answer whatever the status is. */
  const post = async (url, body) => {
    const meta = document.querySelector('meta[name="csrf-token"]');
    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": meta ? meta.content : "",
      },
      body: JSON.stringify(body || {}),
    });
    return response.json().catch(() => ({ success: false }));
  };

  /** "Used by 3 rows", with the count left to the translator. */
  const usageFormatter = (cell) => plural("usage", cell.getValue() || 0);

  /** Delete, or the reason there is no delete: it is in use. */
  const deleteFormatter = (cell) => {
    const row = cell.getRow().getData();
    if (row.usage > 0) {
      const note = document.createElement("span");
      note.className = "dd-hint";
      note.textContent = texts.inUse;
      return note;
    }
    const button = document.createElement("button");
    button.type = "button";
    button.className = "dd-row-delete";
    button.textContent = texts.delete;
    button.addEventListener("click", () => openDelete(row));
    return button;
  };

  const table = new Tabulator("#lookup-grid", {
    ajaxURL: config.rowsUrl,
    ajaxParams: () => {
      const query = search.value.trim();
      return query ? { q: query } : {};
    },
    ajaxResponse: (url, params, response) => {
      total = response.total;
      return { last_page: response.last_page, data: response.data };
    },
    pagination: true,
    paginationMode: "remote",
    paginationSize: config.pageSize,
    paginationCounter: "rows",
    layout: "fitColumns",
    height: "calc(100vh - 300px)",
    placeholder: texts.empty,
    selectableRows: 2,
    index: "id",
    columns: [
      {
        field: "name",
        title: texts.name,
        editor: config.numeric ? "number" : "input",
        headerSort: false,
        widthGrow: 3,
      },
      {
        field: "usage",
        title: texts.usage,
        formatter: usageFormatter,
        headerSort: false,
        hozAlign: "right",
        width: 170,
      },
      {
        field: "delete",
        title: "",
        formatter: deleteFormatter,
        headerSort: false,
        hozAlign: "center",
        width: 150,
      },
    ],
  });

  table.on("dataLoaded", () => {
    countLabel.textContent = plural("rows", total);
  });

  /* ---------------------------------------------------------------- *
   * Renaming: a taken name is the offer to merge, not an error.
   * -------------------------------------------------------------- */

  table.on("cellEdited", async (cell) => {
    if (cell.getField() !== "name") {
      return;
    }
    const row = cell.getRow().getData();
    const typed = cell.getValue();
    cell.getElement().classList.remove("dd-cell-invalid");

    const body = await post(config.renameUrl, { id: row.id, name: typed });
    if (body.success) {
      setStatus(texts.saved, "ok");
      table.replaceData();
      return;
    }

    /* Put the old name back: the row is still called what it was. */
    cell.setValue(cell.getOldValue(), true);

    if (body.error === "duplicate_name") {
      setStatus(texts.duplicate, "error");
      openMerge(
        { id: row.id, name: cell.getOldValue() },
        { id: body.existing_id, name: body.existing_name }
      );
      return;
    }
    setStatus(body.message || texts.failed, "error");
  });

  /* ---------------------------------------------------------------- *
   * Merging: two rows, one of them disappears, and one name survives.
   * -------------------------------------------------------------- */

  const openMerge = (source, target) => {
    merging = { from: source, to: target };
    mergeRows.textContent = "";

    /* "a" is the surviving row's name and "b" the deleted one's: the dialog
     * only asks which of the two names should remain. */
    [
      { role: "to", row: target, note: texts.survivor, keep: true },
      { role: "from", row: source, note: texts.removed, keep: false },
    ].forEach((block) => {
      const label = document.createElement("label");
      label.className = "dd-merge-row";

      const radio = document.createElement("input");
      radio.type = "radio";
      radio.name = "merge-keep";
      radio.value = block.role === "to" ? "a" : "b";
      radio.checked = block.keep;

      const name = document.createElement("span");
      name.className = "dd-merge-name";
      name.textContent = block.row.name;

      const note = document.createElement("span");
      note.className = "dd-hint";
      note.textContent = block.note;

      label.append(radio, name, note);
      mergeRows.append(label);
    });

    mergeWarning.textContent = texts.mergeWarning;
    mergeStatus.textContent = "";
    mergeConfirm.disabled = false;
    mergePanel.hidden = false;
  };

  const closeMerge = () => {
    mergePanel.hidden = true;
    merging = null;
  };

  mergeButton.addEventListener("click", () => {
    const chosen = table.getSelectedRows().map((row) => row.getData());
    if (chosen.length !== 2) {
      setStatus(texts.selectTwo, "error");
      return;
    }
    /* The first selected survives: deleting the other one is the exception,
     * and the dialog lets it be chosen either way. */
    openMerge(chosen[1], chosen[0]);
  });

  mergeConfirm.addEventListener("click", async () => {
    if (!merging) {
      return;
    }
    const keep = mergePanel.querySelector('input[name="merge-keep"]:checked');
    mergeConfirm.disabled = true;
    mergeStatus.textContent = texts.saved;

    const body = await post(config.mergeUrl, {
      table: config.key,
      from_id: merging.from.id,
      to_id: merging.to.id,
      keep_name_from: keep ? keep.value : "a",
    });
    if (!body.success) {
      mergeConfirm.disabled = false;
      mergeStatus.textContent = body.message || texts.failed;
      return;
    }

    closeMerge();
    table.deselectRow();
    table.replaceData();
    setStatus(plural("moved", body.moved || 0), "ok");
  });

  table.on("rowSelectionChanged", (data) => {
    mergeButton.disabled = data.length !== 2;
  });

  /* ---------------------------------------------------------------- *
   * Deleting: only what nothing points at.
   * -------------------------------------------------------------- */

  const openDelete = (row) => {
    deleting = row;
    deleteWarning.textContent = row.name;
    deleteStatus.textContent = "";
    deleteConfirm.disabled = false;
    deletePanel.hidden = false;
  };

  const closeDelete = () => {
    deletePanel.hidden = true;
    deleting = null;
  };

  deleteConfirm.addEventListener("click", async () => {
    if (!deleting) {
      return;
    }
    deleteConfirm.disabled = true;
    deleteStatus.textContent = texts.saved;

    const body = await post(config.deleteUrl, { id: deleting.id });
    if (!body.success) {
      deleteConfirm.disabled = false;
      deleteStatus.textContent = body.message || texts.failed;
      return;
    }

    closeDelete();
    table.replaceData();
    setStatus(texts.deleted, "ok");
  });

  /* ---------------------------------------------------------------- *
   * Years: the next decade, which is what keeps the year field useful.
   * -------------------------------------------------------------- */

  if (nextYears) {
    nextYears.addEventListener("click", async () => {
      nextYears.disabled = true;
      const body = await post(config.nextYearsUrl, { count: config.nextYears });
      nextYears.disabled = false;
      if (!body.success) {
        setStatus(body.message || texts.failed, "error");
        return;
      }
      table.replaceData();
      setStatus(plural("created", body.created || 0), "ok");
    });
  }

  /* ---------------------------------------------------------------- *
   * Dialogs and the search box.
   * -------------------------------------------------------------- */

  const wireDialog = (panel, close) => {
    panel.addEventListener("click", (event) => {
      if (event.target === panel) {
        close();
      }
    });
    panel.addEventListener("keydown", (event) => {
      if (event.key === "Escape") {
        event.stopPropagation();
        close();
      }
    });
  };

  wireDialog(mergePanel, closeMerge);
  wireDialog(deletePanel, closeDelete);
  document.getElementById("merge-close").addEventListener("click", closeMerge);
  document.getElementById("merge-cancel").addEventListener("click", closeMerge);
  document.getElementById("delete-close").addEventListener("click", closeDelete);
  document.getElementById("delete-cancel").addEventListener("click", closeDelete);

  search.addEventListener("input", () => {
    window.clearTimeout(timer);
    timer = window.setTimeout(() => table.setData(), DEBOUNCE_MS);
  });

  /** True when the keystroke belongs to a control and not to the screen. */
  const typing = (event) => {
    const target = event.target;
    return (
      target instanceof Element &&
      Boolean(target.closest("input, select, textarea, button, a"))
    );
  };

  /** Moves the selection one row: the two-row limit is for merging, and the
   * keyboard moves one cursor, so the previous row lets go first. */
  const moveSelection = (step) => {
    const rows = table.getRows();
    if (!rows.length) {
      return;
    }
    const current = table.getSelectedRows()[0];
    const index = current ? rows.indexOf(current) : -1;
    const next = Math.min(Math.max(index + step, 0), rows.length - 1);
    table.deselectRow();
    rows[next].select();
    rows[next].getElement().scrollIntoView({ block: "nearest" });
  };

  document.addEventListener("keydown", (event) => {
    if (typing(event) || event.ctrlKey || event.metaKey || event.altKey) {
      return;
    }
    if (event.key === "/") {
      event.preventDefault();
      search.focus();
      return;
    }
    if (event.key === "j" || event.key === "k") {
      event.preventDefault();
      moveSelection(event.key === "j" ? 1 : -1);
    }
  });
})();
