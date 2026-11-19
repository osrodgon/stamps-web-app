/* Issue workspace grid.
 *
 * One template, two modes. `edit` paints one series and its stamps, read-only.
 * `new` starts from blank rows that exist only in this browser: no request, no
 * database row, so reloading throws the draft away on purpose.
 *
 * Titles, colours, picture URLs and even the element ids come from the page
 * configuration, so this file holds no interface text and no DOM convention it
 * was not told about.
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
  }

  /** Esc returns to the workbench with its filters, like the back button. */
  document.addEventListener("keydown", (event) => {
    if (event.key !== "Escape") {
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
