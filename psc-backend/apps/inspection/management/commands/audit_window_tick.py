from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError
from django.utils.dateparse import parse_date

from apps.inspection.audit.jobs.audit_window import run_audit_window_tick


class Command(BaseCommand):
    help = "Run the daily Audit window tick. Dry-run by default."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Actually create next-cycle plan entries and update overdue statuses.",
        )
        parser.add_argument(
            "--today",
            default=None,
            help="Override today's date for deterministic scheduler tests, YYYY-MM-DD.",
        )

    def handle(self, *args, **options):
        today = None
        if options["today"]:
            today = parse_date(options["today"])
            if today is None:
                raise CommandError("--today must be a valid YYYY-MM-DD date.")

        result = run_audit_window_tick(today=today, apply=bool(options["apply"]))
        mode = "dry_run" if result.dry_run else "applied"
        self.stdout.write(
            self.style.SUCCESS(
                f"audit_window_tick {mode} scanned={result.scanned} due={result.due} "
                f"created_plans={result.created_plans} overdue={result.overdue_plans} "
                f"critical_overdue={result.critical_overdue_plans} "
                f"skipped_missing_rule={result.skipped_missing_rule}"
            )
        )
        for event in result.events[:10]:
            self.stdout.write(
                f"{event.event_type}: plan={event.plan_id} window_end={event.window_end.isoformat()} "
                f"days={event.days_from_window_end} recipient_group={event.recipient_group}"
            )
        if len(result.events) > 10:
            self.stdout.write(f"... {len(result.events) - 10} more audit window event(s)")
