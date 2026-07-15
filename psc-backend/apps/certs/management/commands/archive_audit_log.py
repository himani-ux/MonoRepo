from __future__ import annotations

from datetime import timezone as datetime_timezone

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from apps.certs.jobs.audit_archiver import run_audit_archiver


class Command(BaseCommand):
    help = "Run the Certs audit-log hot/cold tiering and 5-year purge batch."

    def add_arguments(self, parser):
        parser.add_argument(
            "--now-utc",
            dest="now_utc",
            default=None,
            help="Override current UTC time for deterministic scheduler tests, ISO 8601.",
        )

    def handle(self, *args, **options):
        now = _parse_now(options.get("now_utc"))
        result = run_audit_archiver(now=now)
        self.stdout.write(
            self.style.SUCCESS(
                "Certs audit archiver complete: "
                f"cold_flipped={result.cold_flipped}, "
                f"purged={result.purged}, "
                f"audit_recorded={result.audit_recorded}, "
                f"reason={result.reason}"
            )
        )


def _parse_now(raw_value: str | None):
    if not raw_value:
        return timezone.now()
    parsed = parse_datetime(raw_value)
    if parsed is None:
        raise CommandError("--now-utc must be an ISO 8601 datetime")
    if parsed.tzinfo is None:
        parsed = timezone.make_aware(parsed, datetime_timezone.utc)
    return parsed.astimezone(datetime_timezone.utc)
