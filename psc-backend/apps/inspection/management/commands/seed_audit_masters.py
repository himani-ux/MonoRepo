from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError

from apps.inspection.audit.seeds import seed_audit_masters


class Command(BaseCommand):
    help = "Seed the Audit master reference tables from the DPA-reviewed CSVs."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--database",
            default="default",
            help="Database alias to seed. Defaults to 'default'.",
        )
        parser.add_argument(
            "--seed-dir",
            default=None,
            help="Path to the Audit seed CSV directory. Defaults to docs/seeds discovery.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Validate seed files and load order without writing rows.",
        )

    def handle(self, *args, **options):
        try:
            seed_audit_masters(
                using=options["database"],
                seed_dir=options["seed_dir"],
                dry_run=options["dry_run"],
                stdout=self.stdout,
            )
        except CommandError:
            raise
        except Exception as exc:
            raise CommandError(str(exc)) from exc
