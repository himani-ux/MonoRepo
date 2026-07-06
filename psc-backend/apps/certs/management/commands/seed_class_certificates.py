from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import connection, transaction

from apps.certs.class_certificate_seed import SEED_ACTOR_ID, seed_class_certificate_rows


class Command(BaseCommand):
    help = "Seed the Phase 1.4 Class Certificates catalog baseline rows."

    def handle(self, *args, **options):
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(
                    """
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
                result = seed_class_certificate_rows(cursor, actor_id=SEED_ACTOR_ID)

        if result.created_count:
            self.stdout.write(
                self.style.SUCCESS(
                    "Seeded "
                    f"{result.created_count} Class Certificates row(s): {', '.join(result.created_codes)}. "
                    f"Skipped {result.skipped_count} existing row(s)."
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"No Class Certificates seed rows were missing; skipped {result.skipped_count} existing row(s)."
                )
            )

