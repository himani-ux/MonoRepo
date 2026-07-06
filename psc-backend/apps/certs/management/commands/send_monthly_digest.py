from __future__ import annotations

from django.core.management.base import BaseCommand

from apps.certs.jobs.digest_monthly import run_monthly_digest


class Command(BaseCommand):
    help = "Dispatch the Certs monthly fleet digest when the ICT monthly window is open."

    def handle(self, *args, **options):
        result = run_monthly_digest()
        self.stdout.write(
            self.style.SUCCESS(
                f"monthly_digest dispatched={result.dispatched} "
                f"reason={result.reason} recipients={len(result.recipient_ids)}"
            )
        )
