# Vendored assets

Files served as-is from `datadesk/static/datadesk/vendor/`. No CDN: DataDesk is
deployed on an external server, so the assets ship inside the backend image and
`collectstatic` copies them.

Update procedure: download the pinned file from the URL below, replace it, run
`sha256sum <file>` and update its hash here, then reload `/datadesk/` in a
browser to confirm nothing broke.

| File | Version | License | Source | SHA-256 |
| --- | --- | --- | --- | --- |
| `htmx.min.js` | 2.0.11 | BSD 2-Clause | https://cdn.jsdelivr.net/npm/htmx.org@2.0.11/dist/htmx.min.js | `d6fdc75f204e6bdefa99b69bf1e6d4ac69b8a364f77929f45c13476b4000f717` |
| `alpine.min.js` | 3.17.5 | MIT | https://cdn.jsdelivr.net/npm/alpinejs@3.17.5/dist/cdn.min.js | `b4036e9e9ac22fa6f6ae1ba292e015e1f3e9c85d0d79e73e4c8eb9bb139b522e` |
| `tabulator.min.js` | 6.7.1 | MIT | https://cdn.jsdelivr.net/npm/tabulator-tables@6.7.1/dist/js/tabulator.min.js | `a5e826c23a4cff17c8dadf1dc8eced361a6155bfb794c58f4c10d209046823e7` |
| `tabulator.min.css` | 6.7.1 | MIT | https://cdn.jsdelivr.net/npm/tabulator-tables@6.7.1/dist/css/tabulator.min.css | `1a70eeb7c860cd62938e3a233c6536b0f177240e60e47cd9896a33a9dc2c90dc` |
| `inter-latin-var.woff2` | 4.001 | SIL OFL 1.1 | https://fonts.gstatic.com/s/inter/v20/UcC73FwrK3iLTeHuS_nVMrMxCp50SjIa1ZL7.woff2 | `3100e775e8616cd2611beecfa23a4263d7037586789b43f035236a2e6fbd4c62` |

`tabulator.min.css` is self-contained (icons are inline `data:` URIs), so no
extra image files are needed.

`inter-latin-var.woff2` is the **latin subset, variable** (`wght` 100–900, 518
glyphs) of Inter 4.001, exactly as Google Fonts serves it: the file it returns
for `family=Inter:wght@100..900` is byte-identical to this one. Spanish-only
characters (á, ñ, ¿, €) are inside the latin range, so there is no second file
to ship.

The two Tabulator files had their trailing `sourceMappingURL` comment stripped
because the `.map` files are not shipped: keeping the comment made
`collectstatic` warn about a missing referenced file. The hashes above are of
the stripped files.

Alpine is the CDN build (`cdn.min.js`), which bundles the runtime; there is no
separate `alpine.js` import.
