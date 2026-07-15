from __future__ import annotations

from django.core.management.base import BaseCommand

from apps.certs.jobs.cadence_heartbeat import run_cadence_heartbeat, serialize_utc


class Command(BaseCommand):
    help = "Stamp the Certs cadence heartbeat after an hourly cadence run."

    def handle(self, *args, **options):
        result = run_cadence_heartbeat()
        self.stdout.write(
            self.style.SUCCESS(
                f"cadence_heartbeat last_cadence_heartbeat={serialize_utc(result.last_heartbeat_at)}"
            )
        )
