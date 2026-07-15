from __future__ import annotations

from datetime import timezone as datetime_timezone

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from apps.certs.jobs.blob_retention_sweeper import run_blob_retention_sweeper


class Command(BaseCommand):
    help = "Run the Certs PDF/blob retention sweeper."

    def add_arguments(self, parser):
        parser.add_argument(
            "--now-utc",
            dest="now_utc",
            default=None,
            help="Override current UTC time for deterministic scheduler tests, ISO 8601.",
        )

    def handle(self, *args, **options):
        result = run_blob_retention_sweeper(now=_parse_now(options.get("now_utc")))
        self.stdout.write(
            self.style.SUCCESS(
                "Certs blob retention sweeper complete: "
                f"soft_marked={result.soft_marked}, "
                f"hard_deleted={result.hard_deleted}, "
                f"files_deleted={result.files_deleted}, "
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
