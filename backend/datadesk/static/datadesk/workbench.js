/* Workbench grid.
 *
 * The page renders the filter controls and the column titles (translated), so
 * this file only wires Tabulator to the JSON endpoint, keeps the URL and
 * localStorage in sync and renders the gap badge.
 */
(() => {
  "use strict";

  const config = JSON.parse(
    document.getElementById("workbench-config").textContent
  );
  const form = document.getElementById("workbench-filters");
  const countLabel = document.getElementById("workbench-count");
  const chipsBox = document.getElementById("workbench-chips");
  const columnsBox = document.getElementById("workbench-columns");
  /* The server owns the list, so a filter added to `IssueFilters` cannot be
   * missing from the URL the page writes back. */
  const FILTER_NAMES = config.filterNames || [];
  const COLUMNS_KEY = "datadesk.workbench.columns";
  const DEBOUNCE_MS = 300;

  let total = 0;
  let debounceTimer = null;

  const csrfToken = () => {
    const meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.content : "";
  };

  /** The first message of a field-errors object, for the dialog's status line. */
  const firstErrorOf = (errors) => {
    if (!errors || typeof errors !== "object") {
      return "";
    }
    const key = Object.keys(errors)[0];
    if (!key) {
      return "";
    }
    const value = errors[key];
    return Array.isArray(value) ? String(value[0] || "") : String(value);
  };

  /** Reads the filters currently in the form. */
  const readFilters = () => {
    const params = new URLSearchParams();
    FILTER_NAMES.forEach((name) => {
      const field = form.elements[name];
      const value = (field?.value || "").trim();
      if (value !== "") {
        params.set(name, value);
      }
    });
    return params;
  };

  /** What the form shows for a filter: the name of the lookup, or the text. */
  const filterValue = (name) => {
    const field = form.elements[name];
    if (!field) {
      return "";
    }
    if (field.tagName === "SELECT") {
      const option = field.options[field.selectedIndex];
      return option && option.value ? option.textContent.trim() : "";
    }
    return (field.value || "").trim();
  };

  /** Paints the filters that are on, each with the link that removes it.
   *
   * From the form and not from the server-rendered page, so the chips and the
   * grid cannot disagree: changing a filter repaints both. The labels come from
   * the config, translated, because the script holds no interface text.
   */
  const paintChips = () => {
    if (!chipsBox) {
      return;
    }
    chipsBox.textContent = "";
    const params = readFilters();
    let shown = 0;

    FILTER_NAMES.forEach((name) => {
      const value = filterValue(name);
      if (value === "") {
        return;
      }
      shown += 1;

      const rest = new URLSearchParams(params);
      rest.delete(name);
      const query = rest.toString();
      const chip = document.createElement("a");
      chip.className = "dd-chip dd-filter-chip";
      chip.href = query
        ? `${window.location.pathname}?${query}`
        : window.location.pathname;
      chip.title = (config.chipsText || {}).remove || "";

      const key = document.createElement("span");
      key.className = "dd-filter-chip-key";
      key.textContent = `${(config.filterLabels || {})[name] || name}:`;
      const cross = document.createElement("span");
      cross.className = "dd-filter-chip-x";
      cross.setAttribute("aria-hidden", "true");
      cross.textContent = "×";

      chip.append(key, document.createTextNode(` ${value} `), cross);
      chipsBox.append(chip);
    });

    if (shown === 0) {
      chipsBox.hidden = true;
      return;
    }

    const title = document.createElement("span");
    title.className = "dd-label";
    title.textContent = (config.chipsText || {}).title || "";
    const clear = document.createElement("a");
    clear.className = "dd-btn dd-btn-ghost dd-filter-clear";
    clear.href = window.location.pathname;
    clear.textContent = (config.chipsText || {}).clearAll || "";

    chipsBox.prepend(title);
    chipsBox.append(clear);
    chipsBox.hidden = false;
  };

  /** Mirrors the filters into the URL so a reload or a shared link keeps them. */
  const syncUrl = () => {
    const query = readFilters().toString();
    const url = query ? `${window.location.pathname}?${query}` : window.location.pathname;
    window.history.replaceState(null, "", url);
  };

  /** Renders the three gap marks of a row. */
  const gapFormatter = (cell) => {
    const gaps = cell.getValue() || {};
    const marks = [];
    if (gaps.no_country) marks.push("◦ C");
    if (gaps.no_date) marks.push("◦ D");
    if (gaps.no_stamps) marks.push("◦ S");
    return marks.join(" ");
  };

  /** An empty cell gets a muted dash instead of a blank.
   *
   * Tabulator writes a non-breaking space for an empty value, so CSS `:empty`
   * never matches: the dash has to come from the formatter. Columns with a
   * formatter of their own (the gaps, the chevron) already say something.
   */
  const emptyFormatter = (cell) => {
    const value = cell.getValue();
    if (value === null || value === undefined || value === "") {
      const dash = document.createElement("span");
      dash.className = "dd-empty";
      dash.textContent = "\u2014";
      return dash;
    }
    return document.createTextNode(String(value));
  };

  /** Money is euros: the header says what the column is, the value says how
   * much of it. Kept out of the locale formatters on purpose (S28): this is a
   * unit, not a number format. */
  const moneyFormatter = (cell) => {
    const value = cell.getValue();
    if (value === null || value === undefined || value === "") {
      return emptyFormatter(cell);
    }
    return document.createTextNode(`${value} \u20ac`);
  };

  /** Builds one Tabulator column from the server-provided definition. */
  const buildColumn = (definition) => {
    const column = {
      field: definition.field,
      title: definition.title,
      visible: definition.visible,
      headerSort: true,
    };
    if (definition.align) {
      column.hozAlign = definition.align;
    }
    if (definition.width) {
      column.width = definition.width;
    }
    if (definition.grow) {
      column.widthGrow = definition.grow;
    }
    if (definition.min) {
      column.minWidth = definition.min;
    }
    if (definition.field === "gaps") {
      column.formatter = gapFormatter;
      column.headerSort = false;
      column.width = 90;
    }
    if (definition.money) {
      column.formatter = moneyFormatter;
    }
    if (!column.formatter) {
      column.formatter = emptyFormatter;
    }
    return column;
  };

  /** Absolute-ish URL of the workspace of a row, filters included.
   *
   * The workspace walks previous/next through the list it was opened from, so
   * the filters have to travel with the link or the arrows would walk the whole
   * table instead of the rows on screen.
   */
  const issueUrl = (row) => {
    const query = readFilters().toString();
    const suffix = query ? `?${query}` : "";
    return `${config.issueUrlPrefix}${row.id}/${suffix}`;
  };

  /** A chevron drawn inline: no icon font, no extra request. */
  const chevron = () => {
    const namespace = "http://www.w3.org/2000/svg";
    const svg = document.createElementNS(namespace, "svg");
    svg.setAttribute("viewBox", "0 0 24 24");
    svg.setAttribute("class", "dd-chevron");
    svg.setAttribute("aria-hidden", "true");
    const path = document.createElementNS(namespace, "path");
    path.setAttribute("d", "M9 6l6 6-6 6");
    svg.append(path);
    return svg;
  };

  /** The "open" affordance: one link per row; a single click only selects. */
  const openFormatter = (cell) => {
    const link = document.createElement("a");
    link.className = "dd-open";
    link.href = issueUrl(cell.getRow().getData());
    link.title = config.openText;
    link.setAttribute("aria-label", config.openText);
    link.append(chevron());
    return link;
  };

  /** Deleting from the list: the same dialog the workspace uses. */
  const deleteFormatter = (cell) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "dd-remove";
    button.textContent = "×";
    button.title = (config.texts || {}).deleteSeries || "";
    button.setAttribute("aria-label", button.title);
    button.addEventListener("click", (event) => {
      event.stopPropagation();
      openDelete(cell.getRow().getData());
    });
    return button;
  };

  const deleteColumn = {
    field: "delete",
    title: "",
    width: 34,
    headerSort: false,
    hozAlign: "center",
    cssClass: "dd-remove-cell",
    formatter: deleteFormatter,
  };

  const openColumn = {
    field: "open",
    title: "",
    width: 30,
    headerSort: false,
    hozAlign: "center",
    formatter: openFormatter,
  };

  const table = new Tabulator("#workbench", {
    ajaxURL: config.dataUrl,
    ajaxParams: () => Object.fromEntries(readFilters()),
    ajaxResponse: (url, params, response) => {
      total = response.total;
      return { last_page: response.last_page, data: response.data };
    },
    pagination: true,
    paginationMode: "remote",
    paginationSize: config.pageSize,
    paginationInitialPage: config.initialPage || 1,
    paginationCounter: "rows",
    sortMode: "remote",
    /* Columns share the card's width instead of asking for what their content
     * wants: fitting is what keeps the default nine visible without a
     * horizontal scrollbar. */
    layout: "fitColumns",
    /* The card is a column as tall as the window and the grid takes what the
     * filters leave: a fixed `100vh - 300px` was tuned to a two-row bar and put
     * the pagination below the fold as soon as a filter row appeared. */
    height: "100%",
    placeholder: config.emptyText,
    selectableRows: 1,
    columns: [openColumn, ...config.columns.map(buildColumn), deleteColumn],
  });

  /** Double click opens the row: what people try before finding the chevron. */
  table.on("rowDblClick", (event, row) => {
    window.location.assign(issueUrl(row.getData()));
  });

  /** True when the keystroke belongs to a control and not to the screen. */
  const typing = (event) => {
    const target = event.target;
    return (
      target instanceof Element &&
      Boolean(target.closest("input, select, textarea, button, a"))
    );
  };

  /** Moves the selection one row, stopping at the edges instead of wrapping. */
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

  /** The shortcuts the line under the grid promises, and nothing else. */
  document.addEventListener("keydown", (event) => {
    if (typing(event) || event.ctrlKey || event.metaKey || event.altKey) {
      return;
    }
    if (event.key === "/") {
      event.preventDefault();
      form.elements.q.focus();
      return;
    }
    if (event.key === "j" || event.key === "k") {
      event.preventDefault();
      moveSelection(event.key === "j" ? 1 : -1);
      return;
    }
    if (event.key === "Delete") {
      /* Supr opens the dialog for the selected series; it never deletes. */
      const selected = table.getSelectedRows();
      if (selected.length === 1) {
        event.preventDefault();
        openDelete(selected[0].getData());
      }
      return;
    }
    if (event.key.toLowerCase() === "n") {
      event.preventDefault();
      const newIssue = document.querySelector(".dd-new-issue");
      if (newIssue) {
        window.location.assign(newIssue.href);
      }
      return;
    }
    if (event.key !== "Enter") {
      return;
    }
    const selected = table.getSelectedRows();
    if (selected.length === 1) {
      window.location.assign(issueUrl(selected[0].getData()));
    }
  });

  /* ------------------------------------------------------------------ *
   * Deleting a series without opening it.
   *
   * The dialog is the workspace's, and so is the preview: the endpoint and the
   * POST already exist. This screen only fills the numbers and sends the year,
   * which is the server's to check.
   * ---------------------------------------------------------------- */

  const panel = document.getElementById("delete-panel");
  const confirmInput = document.getElementById("delete-confirm");
  const confirmButton = document.getElementById("delete-confirm-button");
  const confirmLabel = document.getElementById("delete-confirm-label");
  const warningText = document.getElementById("delete-warning");
  const statusText = document.getElementById("delete-status");
  const counts = {
    stamps: document.getElementById("delete-stamps"),
    items: document.getElementById("delete-items"),
    collections: document.getElementById("delete-collections"),
  };
  const banner = document.getElementById("workbench-banner");
  const texts = config.texts || {};
  let deleting = null;

  const closeDelete = () => {
    panel.hidden = true;
    deleting = null;
  };

  function openDelete(row) {
    deleting = row;
    panel.hidden = false;
    confirmInput.value = "";
    confirmButton.disabled = true;
    warningText.textContent = "";
    statusText.textContent = "";
    Object.keys(counts).forEach((key) => {
      counts[key].textContent = "·";
    });
    confirmInput.focus();

    fetch(row.dependencies_url, { headers: { Accept: "application/json" } })
      .then((response) => response.json())
      .catch(() => null)
      .then((body) => {
        if (!deleting || !body || !body.success || !body.data) {
          statusText.textContent = (body && body.message) || texts.previewFailed;
          return;
        }
        const data = body.data;
        Object.keys(counts).forEach((key) => {
          counts[key].textContent = data[key];
        });
        warningText.textContent = data.warning;
        confirmLabel.textContent = (texts.confirmYear || "%(year)s").replace(
          "%(year)s",
          data.year
        );
        confirmButton.disabled = false;
      });
  }

  const sendDelete = async () => {
    if (!deleting) {
      return;
    }
    const row = deleting;
    confirmButton.disabled = true;
    statusText.textContent = texts.deleting;

    let body = null;
    try {
      const response = await fetch(row.delete_url, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken(),
        },
        body: JSON.stringify({ confirm: confirmInput.value }),
      });
      body = await response.json();
    } catch (error) {
      body = null;
    }

    if (!body || !body.success) {
      confirmButton.disabled = false;
      statusText.textContent =
        firstErrorOf(body && body.errors) ||
        (body && body.message) ||
        texts.deleteFailed;
      return;
    }

    closeDelete();
    banner.textContent = texts.deleted;
    banner.hidden = false;
    table.setData();
  };

  confirmButton.addEventListener("click", sendDelete);
  confirmInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      sendDelete();
    }
  });
  document.getElementById("delete-close").addEventListener("click", closeDelete);
  document.getElementById("delete-cancel").addEventListener("click", closeDelete);
  panel.addEventListener("click", (event) => {
    if (event.target === panel) {
      closeDelete();
    }
  });
  panel.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      event.stopPropagation();
      closeDelete();
    }
  });

  /** Shows how many rows the current filters match. */
  const updateCount = () => {
    countLabel.textContent = `${total} ${config.counterText}`;
  };

  table.on("dataLoaded", updateCount);

  /* Coming back from a commit: the series that was just saved is selected and
   * scrolled into view, so the user does not have to hunt for it. */
  if (config.focus) {
    let focused = false;
    table.on("dataLoaded", () => {
      if (focused) {
        return;
      }
      const row = table.getRow(config.focus);
      if (!row) {
        return;
      }
      row.select();
      row.getElement().classList.add("dd-row-focus");
      row.getElement().scrollIntoView({ block: "center" });
      focused = true;
    });
  }

  /** Reloads the grid with the filters currently in the form. */
  const reload = () => {
    syncUrl();
    paintChips();
    table.setData();
  };

  form.addEventListener("change", reload);

  form.elements.q.addEventListener("input", () => {
    window.clearTimeout(debounceTimer);
    debounceTimer = window.setTimeout(reload, DEBOUNCE_MS);
  });

  /* The page arrives already filtered when the URL says so: the chips have to
   * say it before the first click. */
  paintChips();

  form.addEventListener("reset", () => {
    window.setTimeout(() => {
      window.clearTimeout(debounceTimer);
      reload();
    }, 0);
  });

  /** Restores the column selection saved in this browser. */
  const savedColumns = () => {
    try {
      return JSON.parse(window.localStorage.getItem(COLUMNS_KEY)) || {};
    } catch (error) {
      return {};
    }
  };

  /** Persists the column selection. */
  const saveColumns = (selection) => {
    window.localStorage.setItem(COLUMNS_KEY, JSON.stringify(selection));
  };

  const selection = savedColumns();

  config.columns.forEach((definition) => {
    const label = document.createElement("label");
    label.className = "dd-columns-item";

    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.checked =
      definition.field in selection
        ? selection[definition.field]
        : definition.visible;
    checkbox.addEventListener("change", () => {
      const next = { ...savedColumns(), [definition.field]: checkbox.checked };
      saveColumns(next);
      if (checkbox.checked) {
        table.showColumn(definition.field);
      } else {
        table.hideColumn(definition.field);
      }
    });

    label.append(checkbox, document.createTextNode(definition.title));
    columnsBox.append(label);

    if (definition.field in selection) {
      if (selection[definition.field]) {
        table.showColumn(definition.field);
      } else {
        table.hideColumn(definition.field);
      }
    }
  });
})();
