"""Database backup management command using Django's dumpdata."""

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
    """Backup database to a JSON fixture file.

    Usage:
        manage.py stamps_db_backup                    # interactive
        manage.py stamps_db_backup my_backup           # interactive for type
        manage.py stamps_db_backup my_backup --mode=stamps  # non-interactive

    The --mode flag controls which apps are included:
        system  - Django contrib tables only
        stamps  - Project app tables only (default)
        full    - Both system and stamps
    """

    help = "Backup database to a JSON fixture file."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "name",
            nargs="?",
            help="Backup name (prompts if omitted)",
        )
        parser.add_argument(
            "--mode",
            choices=list(MODE_MAP.keys()),
            default="stamps",
            help="What to backup: system, stamps, or full (default: stamps)",
        )

    @staticmethod
    def _parse_type_from_path(fp: Path) -> str:
        """Extract backup type (system/stamps/full) from filename stem.

        Filenames follow the pattern: {name}__{type}.json
        """
        stem: str = fp.stem
        parts: list[str] = stem.rsplit("__", 1)
        if len(parts) == 2 and parts[1] in MODE_MAP:
            return parts[1]
        return "unknown"

    @staticmethod
    def _parse_name_from_path(fp: Path) -> str:
        """Extract backup name from filename stem, stripping the type suffix."""
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

        self.stdout.write(self.style.WARNING("Existing backups:"))
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

    def _validate_name(self, name: str) -> str:
        """Validate and return a sanitized backup name, or raise CommandError."""
        cleaned: str = name.strip().replace(" ", "_")
        if not cleaned:
            raise CommandError("Backup name cannot be empty.")
        for ch in cleaned:
            if not ch.isalnum() and ch not in ("-", "_", "."):
                raise CommandError(
                    f"Invalid character {ch!r} in backup name. "
                    "Use only letters, numbers, hyphens, underscores, and dots."
                )
        return cleaned

    def _prompt_mode(self, default: str) -> str:
        """Interactively prompt for backup mode."""
        self.stdout.write()
        self.stdout.write("Backup types:")
        self.stdout.write("  1) System   — Django contrib tables (admin, auth, etc.)")
        self.stdout.write("  2) Stamps   — Project app tables (default)")
        self.stdout.write("  3) Full     — Both")
        choice: str = input(f"Select type [{default}]: ").strip().lower()
        if choice in ("", default):
            return default
        if choice in ("1", "system"):
            return "system"
        if choice in ("2", "stamps"):
            return "stamps"
        if choice in ("3", "full"):
            return "full"
        self.stdout.write(self.style.ERROR(f"Invalid choice: {choice}"))
        return self._prompt_mode(default)

    def handle(self, *args, **options) -> None:
        mode: str = options["mode"]
        name: str | None = options.get("name")

        BACKUP_DIR.mkdir(parents=True, exist_ok=True)

        # Interactive name prompt
        if name is None:
            self._list_backups()
            mode = self._prompt_mode(mode)
            ts: str = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_name: str = f"backup_{ts}"
            raw: str = input(f"Backup name [{default_name}]: ").strip()
            name = raw if raw else default_name

        name = self._validate_name(name)
        filepath: Path = BACKUP_DIR / f"{name}__{mode}.json"

        if filepath.exists():
            overwrite: str = input(
                f'Backup "{name}__{mode}" already exists. Overwrite? [y/N]: '
            ).strip()
            if overwrite.lower() != "y":
                self.stdout.write("Backup cancelled.")
                return

        # Run dumpdata
        apps: list[str] = MODE_MAP[mode]
        self.stdout.write(f"Backing up {len(apps)} app(s) ({mode}) ...")

        with open(filepath, "w", encoding="utf-8") as f:
            call_command(
                "dumpdata",
                *apps,
                stdout=f,
                indent=2,
                natural_foreign=True,
            )

        size: int = filepath.stat().st_size
        self.stdout.write(
            self.style.SUCCESS(f"Backup saved: {filepath} ({size:,d} bytes)")
        )
