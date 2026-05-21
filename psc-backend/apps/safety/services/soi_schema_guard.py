from __future__ import annotations

from django.db import connection

from apps.safety.services.soi_officer_setting_table import ensure_soi_officer_setting_table


SOI_INSPECTION_TABLE = "vims_safety_soi_inspection"
SOI_FINDING_TABLE = "vims_safety_soi_finding"
CHECKLIST_UNIQUE_NAME = "uq_vims_safety_soi_checklist_unique_id"


def ensure_soi_runtime_schema() -> None:
    """Keep SOI usable on live DBs that have not yet run the latest migrations."""
    ensure_soi_officer_setting_table()
    if connection.vendor == "microsoft":
        _ensure_sql_server_filtered_checklist_unique_index()
        _ensure_sql_server_finding_shell_tag_length()


def _ensure_sql_server_filtered_checklist_unique_index() -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            f"""
            IF OBJECT_ID(N'dbo.{SOI_INSPECTION_TABLE}', N'U') IS NOT NULL
            BEGIN
                IF EXISTS (
                    SELECT 1
                    FROM sys.key_constraints
                    WHERE name = N'{CHECKLIST_UNIQUE_NAME}'
                      AND parent_object_id = OBJECT_ID(N'dbo.{SOI_INSPECTION_TABLE}')
                )
                BEGIN
                    ALTER TABLE dbo.{SOI_INSPECTION_TABLE}
                    DROP CONSTRAINT {CHECKLIST_UNIQUE_NAME};
                END

                IF EXISTS (
                    SELECT 1
                    FROM sys.indexes
                    WHERE name = N'{CHECKLIST_UNIQUE_NAME}'
                      AND object_id = OBJECT_ID(N'dbo.{SOI_INSPECTION_TABLE}')
                      AND has_filter = 0
                )
                BEGIN
                    DROP INDEX {CHECKLIST_UNIQUE_NAME}
                    ON dbo.{SOI_INSPECTION_TABLE};
                END

                IF NOT EXISTS (
                    SELECT 1
                    FROM sys.indexes
                    WHERE name = N'{CHECKLIST_UNIQUE_NAME}'
                      AND object_id = OBJECT_ID(N'dbo.{SOI_INSPECTION_TABLE}')
                      AND has_filter = 1
                )
                BEGIN
                    CREATE UNIQUE INDEX {CHECKLIST_UNIQUE_NAME}
                    ON dbo.{SOI_INSPECTION_TABLE} (checklist_unique_id)
                    WHERE checklist_unique_id IS NOT NULL;
                END
            END
            """
        )


def _ensure_sql_server_finding_shell_tag_length() -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            f"""
            IF OBJECT_ID(N'dbo.{SOI_FINDING_TABLE}', N'U') IS NOT NULL
            AND EXISTS (
                SELECT 1
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = N'dbo'
                  AND TABLE_NAME = N'{SOI_FINDING_TABLE}'
                  AND COLUMN_NAME = N'shell_tag'
                  AND CHARACTER_MAXIMUM_LENGTH < 32
            )
            BEGIN
                ALTER TABLE dbo.{SOI_FINDING_TABLE}
                ALTER COLUMN shell_tag NVARCHAR(32) NULL;
            END
            """
        )
