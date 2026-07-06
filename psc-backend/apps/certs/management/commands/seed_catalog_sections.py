from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import connection, transaction

from apps.certs.catalog_section_seed import CATALOG_SECTIONS


class Command(BaseCommand):
    help = "Seed the 9 fixed Certs catalog sections into vims_certs_catalog_section."

    def handle(self, *args, **options):
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    IF OBJECT_ID(N'dbo.vims_certs_catalog_section', N'U') IS NULL
                    BEGIN
                        THROW 51000, 'dbo.vims_certs_catalog_section does not exist. Run certs migrations first.', 1;
                    END
                    """
                )

                for section in CATALOG_SECTIONS:
                    cursor.execute(
                        """
                        UPDATE dbo.vims_certs_catalog_section
                        SET display_name = %s,
                            sort_order = %s
                        WHERE section_code = %s
                        """,
                        [section.display_name, section.sort_order, section.section_code],
                    )
                    if cursor.rowcount:
                        continue

                    cursor.execute(
                        """
                        SET IDENTITY_INSERT dbo.vims_certs_catalog_section ON;
                        INSERT INTO dbo.vims_certs_catalog_section
                            (section_id, section_code, display_name, sort_order, created_by)
                        VALUES
                            (%s, %s, %s, %s, %s);
                        SET IDENTITY_INSERT dbo.vims_certs_catalog_section OFF;
                        """,
                        [
                            section.section_id,
                            section.section_code,
                            section.display_name,
                            section.sort_order,
                            "seed_catalog_sections",
                        ],
                    )

                cursor.execute("SELECT COUNT(*) FROM dbo.vims_certs_catalog_section")
                row_count = int(cursor.fetchone()[0])

        self.stdout.write(
            self.style.SUCCESS(f"Seeded {len(CATALOG_SECTIONS)} catalog section definitions; table has {row_count} row(s).")
        )

