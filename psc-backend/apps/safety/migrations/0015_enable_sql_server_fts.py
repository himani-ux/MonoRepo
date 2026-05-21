from __future__ import annotations

from django.db import migrations


FULLTEXT_CATALOG = "safety_fts_catalog"
FULLTEXT_TABLES = {
    "vims_safety_incident": (
        "incident_number",
        "narrative",
        "closure_reason",
        "reporter_name",
    ),
    "vims_safety_scm_meeting": (
        "scm_number",
        "ad_hoc_trigger_reason",
        "office_comment",
        "location",
    ),
    "vims_safety_soi_finding": (
        "title",
        "description",
        "closure_note",
        "proposed_action",
    ),
}


def enable_sql_server_fts(apps, schema_editor) -> None:
    if schema_editor.connection.vendor != "microsoft":
        return

    existing_tables = set(schema_editor.connection.introspection.table_names())
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("SELECT FULLTEXTSERVICEPROPERTY('IsFullTextInstalled')")
        installed_row = cursor.fetchone()
        installed = int(installed_row[0] or 0) if installed_row else 0
        if installed != 1:
            return

        cursor.execute(
            f"""
            IF NOT EXISTS (
                SELECT 1
                FROM sys.fulltext_catalogs
                WHERE name = '{FULLTEXT_CATALOG}'
            )
            CREATE FULLTEXT CATALOG [{FULLTEXT_CATALOG}] AS DEFAULT
            """
        )

        for table_name, columns in FULLTEXT_TABLES.items():
            if table_name not in existing_tables:
                continue

            cursor.execute(
                """
                SELECT 1
                FROM sys.fulltext_indexes
                WHERE object_id = OBJECT_ID(%s)
                """,
                [f"dbo.{table_name}"],
            )
            if cursor.fetchone() is not None:
                continue

            cursor.execute(
                """
                SELECT TOP 1 idx.name
                FROM sys.indexes idx
                JOIN sys.index_columns idx_col
                  ON idx.object_id = idx_col.object_id
                 AND idx.index_id = idx_col.index_id
                JOIN sys.columns col
                  ON idx.object_id = col.object_id
                 AND idx_col.column_id = col.column_id
                WHERE idx.object_id = OBJECT_ID(%s)
                  AND idx.is_unique = 1
                  AND col.name = 'id'
                ORDER BY idx.is_primary_key DESC, idx.index_id ASC
                """,
                [f"dbo.{table_name}"],
            )
            key_index_row = cursor.fetchone()
            if key_index_row is None:
                continue

            fulltext_columns = ", ".join(f"[{column_name}] LANGUAGE 1033" for column_name in columns)
            cursor.execute(
                f"""
                CREATE FULLTEXT INDEX ON dbo.{table_name}
                (
                    {fulltext_columns}
                )
                KEY INDEX [{key_index_row[0]}]
                ON [{FULLTEXT_CATALOG}]
                WITH CHANGE_TRACKING AUTO
                """
            )


def disable_sql_server_fts(apps, schema_editor) -> None:
    if schema_editor.connection.vendor != "microsoft":
        return

    with schema_editor.connection.cursor() as cursor:
        for table_name in FULLTEXT_TABLES:
            cursor.execute(
                """
                SELECT 1
                FROM sys.fulltext_indexes
                WHERE object_id = OBJECT_ID(%s)
                """,
                [f"dbo.{table_name}"],
            )
            if cursor.fetchone() is None:
                continue
            cursor.execute(f"DROP FULLTEXT INDEX ON dbo.{table_name}")

        cursor.execute(
            """
            SELECT 1
            FROM sys.fulltext_catalogs
            WHERE name = %s
            """,
            [FULLTEXT_CATALOG],
        )
        if cursor.fetchone() is not None:
            cursor.execute(f"DROP FULLTEXT CATALOG [{FULLTEXT_CATALOG}]")


class Migration(migrations.Migration):
    dependencies = [
        ("safety", "0014_phase_log_shape_final"),
    ]

    operations = [
        migrations.RunPython(enable_sql_server_fts, disable_sql_server_fts),
    ]
