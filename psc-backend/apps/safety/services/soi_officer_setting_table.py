from __future__ import annotations

from django.db import connection


TABLE_NAME = "vims_safety_soi_officer_setting"


def ensure_soi_officer_setting_table() -> None:
    if _table_exists():
        return
    if connection.vendor == "microsoft":
        _create_sql_server_table()
        return
    _create_generic_table()


def _table_exists() -> bool:
    with connection.cursor() as cursor:
        table_names = {str(name).lower() for name in connection.introspection.table_names(cursor)}
    return TABLE_NAME.lower() in table_names


def _create_sql_server_table() -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            f"""
            IF OBJECT_ID(N'dbo.{TABLE_NAME}', N'U') IS NULL
            BEGIN
                CREATE TABLE dbo.{TABLE_NAME} (
                    id BIGINT IDENTITY(1,1) NOT NULL
                        CONSTRAINT pk_{TABLE_NAME} PRIMARY KEY,
                    public_id CHAR(32) NOT NULL
                        CONSTRAINT df_{TABLE_NAME}_public_id DEFAULT REPLACE(CONVERT(CHAR(36), NEWID()), '-', ''),
                    vessel_id NVARCHAR(64) NOT NULL,
                    alternate_enabled BIT NOT NULL
                        CONSTRAINT df_{TABLE_NAME}_enabled DEFAULT 0,
                    alternate_so_crew_id NVARCHAR(64) NULL,
                    reason NVARCHAR(MAX) NULL,
                    enabled_by NVARCHAR(128) NULL,
                    enabled_at DATETIME2 NULL,
                    disabled_by NVARCHAR(128) NULL,
                    disabled_at DATETIME2 NULL,
                    schema_version INT NOT NULL
                        CONSTRAINT df_{TABLE_NAME}_schema DEFAULT 1,
                    created_by NVARCHAR(128) NULL,
                    created_date DATETIME2 NOT NULL
                        CONSTRAINT df_{TABLE_NAME}_created DEFAULT SYSUTCDATETIME(),
                    updated_by NVARCHAR(128) NULL,
                    updated_date DATETIME2 NULL
                );
                CREATE UNIQUE INDEX uq_{TABLE_NAME}_vessel
                    ON dbo.{TABLE_NAME} (vessel_id);
                CREATE UNIQUE INDEX uq_{TABLE_NAME}_public_id
                    ON dbo.{TABLE_NAME} (public_id);
                CREATE INDEX ix_safe_sois_vsl_enabled
                    ON dbo.{TABLE_NAME} (vessel_id, alternate_enabled);
            END
            """
        )


def _create_generic_table() -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                public_id VARCHAR(36) NOT NULL UNIQUE DEFAULT (lower(hex(randomblob(16)))),
                vessel_id VARCHAR(64) NOT NULL UNIQUE,
                alternate_enabled BOOLEAN NOT NULL DEFAULT 0,
                alternate_so_crew_id VARCHAR(64) NULL,
                reason TEXT NULL,
                enabled_by VARCHAR(128) NULL,
                enabled_at DATETIME NULL,
                disabled_by VARCHAR(128) NULL,
                disabled_at DATETIME NULL,
                schema_version INTEGER NOT NULL DEFAULT 1,
                created_by VARCHAR(128) NULL,
                created_date DATETIME NULL,
                updated_by VARCHAR(128) NULL,
                updated_date DATETIME NULL
            )
            """
        )
        cursor.execute(
            f"CREATE INDEX IF NOT EXISTS ix_safe_sois_vsl_enabled ON {TABLE_NAME} (vessel_id, alternate_enabled)"
        )
