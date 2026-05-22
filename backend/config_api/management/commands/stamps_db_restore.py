"""Database restore management command using Django's loaddata."""

from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.core.management import BaseCommand, call_command
from django.core.management.base import CommandError


SYSTEM_APPS: list[str] = [
    "admin",
    "auth",
    "contenttypes",
    "sessions",
    "rest_framework_api_key",
]

STAMPS_APPS: list[str] = [
    "config_api",
    "stamp_types_api",
    "locations_api",
    "print_types_api",
    "countries_api",
    "colors_api",
    "stamps_api",
    "issues_api",
    "years_api",
    "collections_api",
    "collection_items_api",
    "condition_types_api",
    "users_api",
    "artists_api",
    "paper_types_api",
    "printers_api",
    "ai_api",
    "health_api",
]

MODE_MAP: dict[str, list[str]] = {
    "system": SYSTEM_APPS,
    "stamps": STAMPS_APPS,
    "full": SYSTEM_APPS + STAMPS_APPS,
}

BACKUP_DIR: Path = settings.BASE_DIR / "backups"


class Command(BaseCommand):
    """Restore database from a JSON fixture file.

    Usage:
        manage.py stamps_db_restore                    # interactive
        manage.py stamps_db_restore my_backup           # auto-select if unique

    Searches for matching backup files in backups/ using the pattern
    {name}__{type}.json. If multiple matches are found, prompts the
    user to choose.

    WARNING: Restoring overwrites existing data for the selected app
    group. A confirmation prompt is always shown.
    """

    help = "Restore database from a JSON fixture file."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "name",
            nargs="?",
            help="Backup name to restore (prompts if omitted)",
        )

    @staticmethod
    def _parse_type_from_path(fp: Path) -> str:
        """Extract backup type from filename stem."""
        stem: str = fp.stem
        parts: list[str] = stem.rsplit("__", 1)
        if len(parts) == 2 and parts[1] in MODE_MAP:
            return parts[1]
        return "unknown"

    @staticmethod
    def _parse_name_from_path(fp: Path) -> str:
        """Extract backup name from filename stem."""
        stem: str = fp.stem
        parts: list[str] = stem.rsplit("__", 1)
        if len(parts) == 2 and parts[1] in MODE_MAP:
            return parts[0]
        return stem

    def _list_backups(self) -> list[Path]:
        """Print existing backups in a formatted table and return the file list."""
        if not BACKUP_DIR.exists():
            self.stdout.write("No backups found.")
            return []

        backups: list[Path] = sorted(BACKUP_DIR.glob("*.json"))
        if not backups:
            self.stdout.write("No backups found.")
            return []

        self.stdout.write(self.style.WARNING("Available backups:"))
        self.stdout.write(
            f"  {'Name':30s}  {'Type':8s}  {'Size':>10s}  {'Date':16s}"
        )
        self.stdout.write(
            f"  {'-' * 30}  {'-' * 8}  {'-' * 10}  {'-' * 16}"
        )
        for fp in backups:
            size: int = fp.stat().st_size
            mtime: str = datetime.fromtimestamp(fp.stat().st_mtime).strftime(
                "%Y-%m-%d %H:%M"
            )
            btype: str = self._parse_type_from_path(fp)
            bname: str = self._parse_name_from_path(fp)
            self.stdout.write(
                f"  {bname:30s}  {btype:8s}  {size:>10,d} B  {mtime:16s}"
            )

        return backups

    def _find_backup(self, name: str) -> Path:
        """Resolve a backup name to a single file path, or raise CommandError.

        Search order:
          1. Exact match: {name}__{type}.json
          2. Partial glob: *{name}*.json
          3. If multiple, prompt user to select.
        """
        # Exact match
        exact: list[Path] = sorted(BACKUP_DIR.glob(f"{name}__*.json"))
        if not exact:
            exact = sorted(BACKUP_DIR.glob(f"*{name}*.json"))

        if not exact:
            raise CommandError(f'No backup found matching "{name}".')

        if len(exact) == 1:
            return exact[0]

        # Multiple matches — prompt
        self.stdout.write(self.style.WARNING("Multiple backups match:"))
        for i, fp in enumerate(exact, 1):
            self.stdout.write(f"  {i}. {fp.stem}  ({fp.stat().st_size:,d} B)")
        choice: str = input("Enter number to restore: ").strip()
        try:
            idx: int = int(choice) - 1
            if idx < 0 or idx >= len(exact):
                raise ValueError
            return exact[idx]
        except (ValueError, IndexError):
            raise CommandError("Invalid selection.")

    def _confirm_restore(self, filepath: Path) -> bool:
        """Ask for confirmation before destructive restore."""
        confirm: str = input(
            f'\nThis will overwrite ALL current data from "{filepath.stem}".\n'
            "Continue? [y/N]: "
        ).strip()
        return confirm.lower() == "y"

    def handle(self, *args, **options) -> None:
        name: str | None = options.get("name")

        BACKUP_DIR.mkdir(parents=True, exist_ok=True)

        # Interactive mode
        if name is None:
            backups: list[Path] = self._list_backups()
            if not backups:
                return
            self.stdout.write()
            raw: str = input("Enter backup name to restore: ").strip()
            if not raw:
                self.stdout.write("Restore cancelled.")
                return
            name = raw

        filepath: Path = self._find_backup(name)

        if not self._confirm_restore(filepath):
            self.stdout.write("Restore cancelled.")
            return

        # Run loaddata
        self.stdout.write(f"Restoring from {filepath} ...")
        try:
            call_command("loaddata", str(filepath))
        except Exception as e:
            raise CommandError(f"Restore failed: {e}")

        self.stdout.write(
            self.style.SUCCESS(f"Restore complete: {filepath.name}")
        )
