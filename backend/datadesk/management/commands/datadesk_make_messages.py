"""Compile the DataDesk translation catalogs without installing gettext.

Contributors edit the ``.po`` files and run this command; ``polib`` writes the
``.mo`` files Django reads at runtime. ``--check`` compares the compiled catalog
with its source so CI can fail when a ``.po`` changed and its ``.mo`` was not
rebuilt.
"""
from pathlib import Path

import polib
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

LOCALE_DIR = Path(settings.BASE_DIR) / "datadesk" / "locale"
CATALOG_GLOB = "*/LC_MESSAGES/django.po"


class Command(BaseCommand):
    """Builds (or verifies) the DataDesk `.mo` catalogs."""

    help = "Compile every DataDesk .po file into .mo using polib."

    def add_arguments(self, parser) -> None:
        """Adds the ``--check`` flag."""
        parser.add_argument(
            "--check",
            action="store_true",
            help="Fail if a .mo is missing or does not match its .po instead of compiling.",
        )

    def handle(self, *args, **options) -> None:
        """Compiles the catalogs, or reports the ones that are stale."""
        po_files = sorted(LOCALE_DIR.glob(CATALOG_GLOB))
        if not po_files:
            raise CommandError(f"No .po files found under {LOCALE_DIR}")

        if options["check"]:
            stale = [path for path in po_files if self._is_stale(path)]
            if stale:
                names = ", ".join(str(path.relative_to(LOCALE_DIR)) for path in stale)
                raise CommandError(
                    f"Stale catalogs: {names}. Run datadesk_make_messages."
                )
            self.stdout.write(self.style.SUCCESS("Catalogs are up to date."))
            return

        for po_path in po_files:
            polib.pofile(str(po_path)).save_as_mofile(str(po_path.with_suffix(".mo")))
            self.stdout.write(f"Compiled {po_path.relative_to(LOCALE_DIR)}")

        self.stdout.write(self.style.SUCCESS(f"Compiled {len(po_files)} catalogs."))

    @staticmethod
    def _is_stale(po_path: Path) -> bool:
        """Tells whether the ``.mo`` is missing or no longer matches its ``.po``.

        The comparison is on catalog content, not on file timestamps: a git
        checkout gives every file the same mtime in index order, so ``django.mo``
        can look older than ``django.po`` while being perfectly up to date.
        """
        mo_path = po_path.with_suffix(".mo")
        if not mo_path.exists():
            return True

        source = {entry.msgid: entry.msgstr for entry in polib.pofile(str(po_path))}
        compiled = {entry.msgid: entry.msgstr for entry in polib.mofile(str(mo_path))}
        return source != compiled
