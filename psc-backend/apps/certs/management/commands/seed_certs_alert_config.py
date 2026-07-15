from __future__ import annotations

from django.core.management.base import BaseCommand

from apps.certs.services.alert_config_seed import seed_default_alert_configs


class Command(BaseCommand):
    help = "Seed the default Certs alert configuration rows and settings singleton."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Persist missing default alert configuration rows.",
        )
        parser.add_argument(
            "--actor-id",
            default="seed_certs_alert_config",
            help="Actor id recorded in updated_by.",
        )

    def handle(self, *args, **options):
        result = seed_default_alert_configs(
            apply=bool(options["apply"]),
            actor_id=str(options["actor_id"]),
        )
        mode = "dry_run" if result.dry_run else "applied"
        self.stdout.write(
            self.style.SUCCESS(
                f"certs_alert_config {mode} created={len(result.created)} "
                f"existing={len(result.existing)} settings_created={result.settings_created}"
            )
        )
        if result.created:
            self.stdout.write("created: " + ", ".join(result.created))
