from __future__ import annotations

from django.core.management.base import BaseCommand

from apps.certs.services.iws_age_gate import recompute_iws_age_gate


class Command(BaseCommand):
    help = "Recompute Class IWS Survey age-gate disabled state for all vessels."

    def handle(self, *args, **options):
        result = recompute_iws_age_gate()
        self.stdout.write(
            self.style.SUCCESS(
                "IWS age-gate recompute complete: "
                f"evaluated={result.evaluated_count}, "
                f"disabled={result.disabled_count}, "
                f"enabled={result.enabled_count}, "
                f"overrides_preserved={result.override_preserved_count}, "
                f"skipped={result.skipped_count}."
            )
        )

