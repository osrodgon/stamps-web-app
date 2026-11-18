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
    paginationCounter: "rows",
    sortMode: "remote",
    layout: "fitDataStretch",
    height: "calc(100vh - 260px)",
    placeholder: config.emptyText,
    columns: config.columns.map(buildColumn),
  });

  /** Shows how many rows the current filters match. */
  const updateCount = () => {
    countLabel.textContent = `${total} ${config.counterText}`;
  };

  table.on("dataLoaded", updateCount);

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
