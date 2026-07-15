from __future__ import annotations

from django.core.management.base import BaseCommand

from apps.certs.jobs.cadence_heartbeat import run_cadence_deadman_check


class Command(BaseCommand):
    help = "Check the Certs cadence heartbeat and send the office Slack dead-man alert when stale."

    def handle(self, *args, **options):
        result = run_cadence_deadman_check()
        self.stdout.write(
            self.style.SUCCESS(
                "cadence_deadman "
                f"stale={result.stale} "
                f"alert_sent={result.alert_sent} "
                f"age_seconds={result.heartbeat_age_seconds} "
                f"reason={result.reason}"
            )
        )
