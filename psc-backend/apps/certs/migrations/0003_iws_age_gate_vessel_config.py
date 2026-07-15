from __future__ import annotations

from django.db import migrations


ADD_COLUMNS_SQL = (
    (
        "iws_age_gate_disabled",
        """
        ALTER TABLE dbo.vims_certs_vessel_config
        ADD iws_age_gate_disabled BIT NOT NULL
            CONSTRAINT df_vims_certs_vessel_config_iws_disabled DEFAULT 0
        """,
    ),
    (
        "iws_age_gate_disabled_at",
        "ALTER TABLE dbo.vims_certs_vessel_config ADD iws_age_gate_disabled_at DATETIME2(7) NULL",
    ),
    (
        "iws_age_gate_disabled_reason",
        "ALTER TABLE dbo.vims_certs_vessel_config ADD iws_age_gate_disabled_reason NVARCHAR(256) NULL",
    ),
    (
        "iws_age_gate_last_age_years",
        "ALTER TABLE dbo.vims_certs_vessel_config ADD iws_age_gate_last_age_years SMALLINT NULL",
    ),
    (
        "iws_age_gate_last_evaluated_at",
        "ALTER TABLE dbo.vims_certs_vessel_config ADD iws_age_gate_last_evaluated_at DATETIME2(7) NULL",
    ),
    (
        "iws_manual_override_enabled",
        """
        ALTER TABLE dbo.vims_certs_vessel_config
        ADD iws_manual_override_enabled BIT NOT NULL
            CONSTRAINT df_vims_certs_vessel_config_iws_override DEFAULT 0
        """,
    ),
    (
        "iws_manual_override_reason",
        "ALTER TABLE dbo.vims_certs_vessel_config ADD iws_manual_override_reason NVARCHAR(MAX) NULL",
    ),
    (
        "iws_manual_override_by",
        "ALTER TABLE dbo.vims_certs_vessel_config ADD iws_manual_override_by NVARCHAR(64) NULL",
    ),
    (
        "iws_manual_override_at",
        "ALTER TABLE dbo.vims_certs_vessel_config ADD iws_manual_override_at DATETIME2(7) NULL",
    ),
)

INDEX_SQL = """
CREATE INDEX ix_vims_certs_vessel_config_iws_age_gate
ON dbo.vims_certs_vessel_config(iws_age_gate_disabled, iws_manual_override_enabled)
"""


def _table_exists(cursor) -> bool:
    cursor.execute("SELECT COUNT(*) FROM sys.tables WHERE object_id = OBJECT_ID(N'dbo.vims_certs_vessel_config')")
    return int(cursor.fetchone()[0] or 0) > 0


def _column_exists(cursor, column_name: str) -> bool:
    cursor.execute(
        """
        SELECT COUNT(*)
        FROM sys.columns
        WHERE object_id = OBJECT_ID(N'dbo.vims_certs_vessel_config')
          AND name = %s
        """,
        [column_name],
    )
    return int(cursor.fetchone()[0] or 0) > 0


def _index_exists(cursor, index_name: str) -> bool:
    cursor.execute(
        """
        SELECT COUNT(*)
        FROM sys.indexes
        WHERE object_id = OBJECT_ID(N'dbo.vims_certs_vessel_config')
          AND name = %s
        """,
        [index_name],
    )
    return int(cursor.fetchone()[0] or 0) > 0


def _drop_default_constraint(cursor, column_name: str) -> None:
    cursor.execute(
        """
        DECLARE @sql NVARCHAR(MAX) = N'';
        SELECT @sql = N'ALTER TABLE dbo.vims_certs_vessel_config DROP CONSTRAINT ' + QUOTENAME(dc.name)
        FROM sys.default_constraints dc
        INNER JOIN sys.columns c
            ON c.object_id = dc.parent_object_id
           AND c.column_id = dc.parent_column_id
        WHERE dc.parent_object_id = OBJECT_ID(N'dbo.vims_certs_vessel_config')
          AND c.name = %s;
        IF @sql <> N'' EXEC sp_executesql @sql;
        """,
        [column_name],
    )


def add_iws_age_gate_columns(apps, schema_editor) -> None:
    if schema_editor.connection.vendor != "microsoft":
        return

    with schema_editor.connection.cursor() as cursor:
        if not _table_exists(cursor):
            return
        for column_name, statement in ADD_COLUMNS_SQL:
            if not _column_exists(cursor, column_name):
                cursor.execute(statement)
        if not _index_exists(cursor, "ix_vims_certs_vessel_config_iws_age_gate"):
            cursor.execute(INDEX_SQL)


def drop_iws_age_gate_columns(apps, schema_editor) -> None:
    if schema_editor.connection.vendor != "microsoft":
        return

    with schema_editor.connection.cursor() as cursor:
        if not _table_exists(cursor):
            return
        if _index_exists(cursor, "ix_vims_certs_vessel_config_iws_age_gate"):
            cursor.execute("DROP INDEX ix_vims_certs_vessel_config_iws_age_gate ON dbo.vims_certs_vessel_config")
        for column_name, _statement in reversed(ADD_COLUMNS_SQL):
            if _column_exists(cursor, column_name):
                _drop_default_constraint(cursor, column_name)
                cursor.execute(f"ALTER TABLE dbo.vims_certs_vessel_config DROP COLUMN {column_name}")


class Migration(migrations.Migration):
    dependencies = [
        ("certs", "0002_iopp_variant_constraints"),
    ]

    operations = [
        migrations.RunPython(add_iws_age_gate_columns, drop_iws_age_gate_columns),
    ]

