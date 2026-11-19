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
  const columnsBox = document.getElementById("workbench-columns");
  const FILTER_NAMES = [
    "year_min",
    "year_max",
    "q",
    "country",
    "stamp_type",
    "attention",
  ];
  const COLUMNS_KEY = "datadesk.workbench.columns";
  const DEBOUNCE_MS = 300;

  let total = 0;
  let debounceTimer = null;

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
    if (definition.field === "gaps") {
      column.formatter = gapFormatter;
      column.headerSort = false;
      column.width = 90;
    }
    return column;
  };

  /** Absolute-ish URL of the workspace of a row. */
  const issueUrl = (row) => `${config.issueUrlPrefix}${row.id}/`;

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
    layout: "fitDataStretch",
    height: "calc(100vh - 260px)",
    placeholder: config.emptyText,
    selectableRows: 1,
    columns: [openColumn, ...config.columns.map(buildColumn)],
  });

  /** Double click opens the row: what people try before finding the chevron. */
  table.on("rowDblClick", (event, row) => {
    window.location.assign(issueUrl(row.getData()));
  });

  /** `Enter` opens the selected row, unless the focus is in a control. */
  document.addEventListener("keydown", (event) => {
    if (event.key !== "Enter") {
      return;
    }
    const target = event.target;
    if (
      target instanceof Element &&
      target.closest("input, select, textarea, button, a")
    ) {
      return;
    }
    const selected = table.getSelectedRows();
    if (selected.length === 1) {
      window.location.assign(issueUrl(selected[0].getData()));
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
    table.setData();
  };

  form.addEventListener("change", reload);

  form.elements.q.addEventListener("input", () => {
    window.clearTimeout(debounceTimer);
    debounceTimer = window.setTimeout(reload, DEBOUNCE_MS);
  });

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
