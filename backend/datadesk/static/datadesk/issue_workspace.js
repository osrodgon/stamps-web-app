/* Issue workspace grid (read-only).
 *
 * One series, its stamps, no paging: the largest series in the database has a
 * few dozen rows, and the rows travel with the page. The colour tones and the
 * picture URLs are resolved by Django, so this file only paints what it is
 * told.
 */
(() => {
  "use strict";

  const config = JSON.parse(
    document.getElementById("stamp-config").textContent
  );

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

  new Tabulator("#stamp-grid", {
    data: config.data,
    columns: config.columns.map(buildColumn),
    layout: "fitColumns",
    height: false,
    placeholder: config.emptyText,
  });

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
