from __future__ import annotations

from django.core.management.base import BaseCommand

from apps.certs.jobs.daily_alerts import run_daily_cert_alerts


class Command(BaseCommand):
    help = "Dispatch due Certs expiry and survey-window alerts. Dry-run by default."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Actually create notifications. Without this flag the command only previews counts.",
        )
        parser.add_argument(
            "--include-pending-first-upload",
            action="store_true",
            help="Include pending-first-upload/PDF-missing rows. Use with --max-alerts to avoid a large burst.",
        )
        parser.add_argument(
            "--max-alerts",
            type=int,
            default=100,
            help="Maximum due rows to process in one run.",
        )

    def handle(self, *args, **options):
        result = run_daily_cert_alerts(
            apply=bool(options["apply"]),
            include_pending_first_upload=bool(options["include_pending_first_upload"]),
            max_alerts=max(0, int(options["max_alerts"])),
        )
        mode = "dry_run" if result.dry_run else "applied"
        self.stdout.write(
            self.style.SUCCESS(
                f"certs_daily_alerts {mode} scanned={result.scanned} due={result.due} "
                f"dispatched={result.dispatched} skipped_no_recipients={result.skipped_no_recipients} "
                f"skipped_already_sent={result.skipped_already_sent} max_alerts_reached={result.max_alerts_reached} "
                f"config_seeded={len(result.config_seeded)} settings_seeded={result.settings_seeded} "
                f"heartbeat_stamped={result.heartbeat_stamped_at is not None}"
            )
        )
        for event in result.events[:10]:
            target = event.target_date.isoformat() if event.target_date else "n/a"
            self.stdout.write(
                f"{event.trigger_event}: {event.vessel_name} - {event.certificate_name} "
                f"target={target} days={event.days_to_go}"
            )
        if len(result.events) > 10:
            self.stdout.write(f"... {len(result.events) - 10} more due alert(s)")
