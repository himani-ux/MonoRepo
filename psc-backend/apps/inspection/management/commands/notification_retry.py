from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError

from apps.inspection.audit.jobs.notification_retry import run_notification_retry


class Command(BaseCommand):
    help = "Retry queued Audit email and Slack notification deliveries."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--limit",
            type=int,
            default=100,
            help="Maximum queued/retrying rows to scan per channel.",
        )

    def handle(self, *args, **options):
        limit = int(options["limit"])
        if limit < 1:
            raise CommandError("--limit must be at least 1.")

        result = run_notification_retry(limit=limit)
        self.stdout.write(
            self.style.SUCCESS(
                "notification_retry "
                f"email_scanned={result.email.scanned} email_sent={result.email.sent} "
                f"email_retrying={result.email.retrying} "
                f"email_failed_permanent={result.email.failed_permanent} "
                f"slack_scanned={result.slack.scanned} slack_sent={result.slack.sent} "
                f"slack_retrying={result.slack.retrying} "
                f"slack_failed_permanent={result.slack.failed_permanent}"
            )
        )
