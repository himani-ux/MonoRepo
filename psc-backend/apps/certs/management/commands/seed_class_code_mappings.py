from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction

from apps.certs.class_code_mapping_seed import (
    CLASS_CODE_MAPPING_ROWS,
    SEED_ACTOR_ID,
    seed_class_code_mappings,
)


class Command(BaseCommand):
    help = "Seed approved Certs class-code mappings into vims_certs_class_code_mapping."

    def add_arguments(self, parser) -> None:
        parser.add_argument("--apply", action="store_true", help="Persist missing class-code mappings.")
        parser.add_argument(
            "--society",
            choices=sorted({row.class_society.upper() for row in CLASS_CODE_MAPPING_ROWS}),
            help="Limit the seed to one class society.",
        )

    def handle(self, *args, **options):
        apply_changes = bool(options["apply"])
        society = str(options.get("society") or "").upper()
        rows = tuple(row for row in CLASS_CODE_MAPPING_ROWS if not society or row.class_society.upper() == society)
        if not rows:
            raise CommandError(f"No class-code mapping seed rows found for society {society}.")

        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    IF OBJECT_ID(N'dbo.vims_certs_class_code_mapping', N'U') IS NULL
                    BEGIN
                        THROW 51000, 'dbo.vims_certs_class_code_mapping does not exist. Run certs migrations first.', 1;
                    END
                    IF OBJECT_ID(N'dbo.vims_certs_catalog_row', N'U') IS NULL
                    BEGIN
                        THROW 51000, 'dbo.vims_certs_catalog_row does not exist. Run certs migrations first.', 1;
                    END
                    IF OBJECT_ID(N'dbo.vims_certs_audit_log', N'U') IS NULL
                    BEGIN
                        THROW 51000, 'dbo.vims_certs_audit_log does not exist. Run certs migrations first.', 1;
                    END
                    """
                )
                result = seed_class_code_mappings(
                    cursor,
                    rows,
                    actor_id=SEED_ACTOR_ID,
                    dry_run=not apply_changes,
                )
                if result.missing_catalog_codes:
                    raise CommandError(
                        "Cannot seed class-code mappings because these catalog row(s) are missing: "
                        + ", ".join(result.missing_catalog_codes)
                    )

        scope = society or "all societies"
        if apply_changes:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Seeded {result.created_count} class-code mapping row(s) for {scope}; "
                    f"skipped {result.skipped_count} existing row(s)."
                )
            )
            return

        self.stdout.write(
            self.style.WARNING(
                f"Dry run only for {scope}. Would create {result.would_create_count} row(s) "
                f"and skip {result.would_skip_count} existing row(s). Re-run with --apply to persist."
            )
        )
