/* Activity screen.
 *
 * The commits are rendered by the server, dialog and all, because every line in
 * them is interface text. This file only opens and closes those dialogs: the
 * revert button is a submit inside the dialog, so nothing happens by accident.
 */
(() => {
  "use strict";

  const panelOf = (id) => document.getElementById("revert-" + id);

  const closeAll = (except) => {
    document.querySelectorAll(".dd-dialog-backdrop").forEach((panel) => {
      if (panel !== except) {
        panel.hidden = true;
      }
    });
  };

  document.querySelectorAll("[data-revert]").forEach((button) => {
    button.addEventListener("click", () => {
      const panel = panelOf(button.dataset.revert);
      if (!panel) {
        return;
      }
      closeAll(panel);
      panel.hidden = false;
      const submit = panel.querySelector('button[type="submit"]');
      if (submit) {
        submit.focus();
      }
    });
  });

  document.querySelectorAll("[data-revert-close]").forEach((button) => {
    button.addEventListener("click", () => {
      const panel = panelOf(button.dataset.revertClose);
      if (panel) {
        panel.hidden = true;
      }
    });
  });

  document.querySelectorAll(".dd-dialog-backdrop").forEach((panel) => {
    panel.addEventListener("click", (event) => {
      if (event.target === panel) {
        panel.hidden = true;
      }
    });
    panel.addEventListener("keydown", (event) => {
      if (event.key === "Escape") {
        event.stopPropagation();
        panel.hidden = true;
      }
    });
  });
})();
