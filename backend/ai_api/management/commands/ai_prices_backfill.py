"""Price the catalogue in batches and keep what was found (plan step A8).

The endpoint prices one series with a budget, because a request cannot wait for a
whole catalogue. This command is the other half: it walks the issues of the
database, asks the sources for their stamps' prices and **stores the observations**,
where a repeated run does not duplicate them.

Usage:
    python manage.py ai_prices_backfill --limit 10 --dry-run
    python manage.py ai_prices_backfill --source filatelia --only 842
    python manage.py ai_prices_backfill --stamps 3
"""

from __future__ import annotations

from typing import Dict, List

from django.core.management.base import BaseCommand
from django.db import IntegrityError, transaction
from django.utils import timezone

from ai_api.models import SourceObservation
from ai_api.sources.base import Observation
from ai_api.sources.filatelia import FilateliaCatalogue
from ai_api.sources.search_prices import SearchPrices
from common.log.logger import Logger


SOURCES = ("filatelia", "search")


class Command(BaseCommand, Logger):
    """Walk the issues and store the prices the sources return for their stamps."""

    help = "Price the stamps of the catalogue and store the observations (A8)."

    def add_arguments(self, parser) -> None:
        """Declare the flags the backfill needs."""
        parser.add_argument(
            "--limit",
            type=int,
            default=0,
            help="How many issues to walk (0 = all of them).",
        )
        parser.add_argument(
            "--source",
            action="append",
            choices=SOURCES,
            help="Price only this source (repeatable). Default: all of them.",
        )
        parser.add_argument(
            "--only",
            action="append",
            type=int,
            help="Walk only these issue ids (repeatable).",
        )
        parser.add_argument(
            "--stamps",
            type=int,
            default=0,
            help="How many stamps per issue to price (0 = all of them).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Ask the sources and report, but write nothing.",
        )

    def handle(self, *args, **options) -> None:
        """Run the backfill and print what it did."""
        sources = options["source"] or list(SOURCES)
        limit = options["limit"] or 0
        only = options["only"] or []
        max_stamps = options["stamps"] or 0
        dry_run = options["dry_run"]

        issues = self._issues(only)[:limit] if limit else self._issues(only)

        totals: Dict[str, int] = {
            "issues": 0,
            "stamps": 0,
            "observations": 0,
            "saved": 0,
            "duplicates": 0,
        }

        for issue in issues:
            totals["issues"] += 1
            year = str(issue.year.year) if issue.year_id else ""
            stamps = [stamp for stamp in issue.stamps.all() if stamp.edifil_code]
            if max_stamps:
                stamps = stamps[:max_stamps]

            for stamp in stamps:
                totals["stamps"] += 1
                observations = self._observations(sources, stamp, issue, year)
                totals["observations"] += len(observations)

                for observation in observations:
                    if dry_run:
                        continue
                    if self._store(observation, stamp):
                        totals["saved"] += 1
                    else:
                        totals["duplicates"] += 1

        self._report(totals, dry_run, sources)

    # ------------------------------------------------------------------
    # Work
    # ------------------------------------------------------------------

    @staticmethod
    def _issues(only: List[int]):
        """The issues to walk, oldest first, with their year and stamps ready."""
        from issues_api.models import Issue

        queryset = Issue.objects.select_related("year").prefetch_related("stamps")
        if only:
            queryset = queryset.filter(id__in=only)
        return queryset.order_by("id")

    def _observations(
        self, sources: List[str], stamp, issue, year: str
    ) -> List[Observation]:
        """Ask every source about one stamp, turning a failure into a log line."""
        found: List[Observation] = []

        if "filatelia" in sources:
            try:
                found.extend(FilateliaCatalogue().prices(stamp.edifil_code, year))
            except Exception as error:  # a source down must not stop the backfill
                self.log.warning(f"filatelia failed for {stamp.edifil_code}: {error}")

        if "search" in sources:
            try:
                found.extend(
                    SearchPrices().prices(stamp.edifil_code, issue.name, year)
                )
            except Exception as error:
                self.log.warning(f"search failed for {stamp.edifil_code}: {error}")

        return [
            observation
            if observation.subject_code
            else self._with_code(observation, stamp.edifil_code)
            for observation in found
        ]

    @staticmethod
    def _with_code(observation: Observation, code: str) -> Observation:
        """Return the observation carrying the code it prices."""
        from dataclasses import replace

        return replace(observation, subject_code=code)

    def _store(self, observation: Observation, stamp) -> bool:
        """Write one observation, or report it as a duplicate.

        `raw_hash` is the identity of an observation, so a second run over the same
        catalogue finds it and stops: running the command twice must not double the
        evidence behind a price.
        """
        row = SourceObservation(
            source=observation.source,
            external_id=observation.external_id,
            url=observation.url[:500],
            stamp=stamp,
            kind=observation.kind,
            price=observation.price,
            currency=observation.currency,
            condition=observation.condition,
            observed_at=observation.observed_at or timezone.now(),
            raw=observation.raw,
        )
        try:
            with transaction.atomic():
                row.save()
        except IntegrityError:
            return False
        return True

    # ------------------------------------------------------------------
    # Report
    # ------------------------------------------------------------------

    def _report(self, totals: Dict[str, int], dry_run: bool, sources: List[str]) -> None:
        """Print the run in one block, so it can be read in a log."""
        prefix = "[dry-run] " if dry_run else ""
        self.stdout.write(
            self.style.MIGRATE_HEADING(f"{prefix}AI prices backfill ({', '.join(sources)})")
        )
        self.stdout.write(f"  issues:       {totals['issues']}")
        self.stdout.write(f"  stamps:       {totals['stamps']}")
        self.stdout.write(f"  observations: {totals['observations']}")
        if not dry_run:
            self.stdout.write(f"  saved:        {totals['saved']}")
            self.stdout.write(f"  duplicates:   {totals['duplicates']}")
