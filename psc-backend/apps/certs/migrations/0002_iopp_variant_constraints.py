from __future__ import annotations

from django.db import migrations


CONSTRAINT_SQL = (
    (
        "vims_certs_tracked_item",
        "ck_vims_certs_tracked_item_form_variant",
        """
        ALTER TABLE dbo.vims_certs_tracked_item
        ADD CONSTRAINT ck_vims_certs_tracked_item_form_variant
        CHECK (form_variant IS NULL OR form_variant IN (N'A', N'B', N'n/a'))
        """,
    ),
    (
        "vims_certs_catalog_row",
        "ck_vims_certs_catalog_row_no_iopp_variant_code",
        """
        ALTER TABLE dbo.vims_certs_catalog_row
        ADD CONSTRAINT ck_vims_certs_catalog_row_no_iopp_variant_code
        CHECK (
            UPPER(canonical_code) NOT IN (N'IOPP-A', N'IOPP-B')
            AND UPPER(canonical_code) NOT LIKE N'%-IOPP-A'
            AND UPPER(canonical_code) NOT LIKE N'%-IOPP-B'
        )
        """,
    ),
)


def _table_exists(cursor, table_name: str) -> bool:
    cursor.execute(
        """
        SELECT COUNT(*)
        FROM sys.tables
        WHERE object_id = OBJECT_ID(%s)
        """,
        [f"dbo.{table_name}"],
    )
    return int(cursor.fetchone()[0] or 0) > 0


def _constraint_exists(cursor, table_name: str, constraint_name: str) -> bool:
    cursor.execute(
        """
        SELECT COUNT(*)
        FROM sys.objects
        WHERE parent_object_id = OBJECT_ID(%s)
          AND name = %s
        """,
        [f"dbo.{table_name}", constraint_name],
    )
    return int(cursor.fetchone()[0] or 0) > 0


def add_iopp_variant_constraints(apps, schema_editor) -> None:
    if schema_editor.connection.vendor != "microsoft":
        return

    with schema_editor.connection.cursor() as cursor:
        for table_name, constraint_name, statement in CONSTRAINT_SQL:
            if _table_exists(cursor, table_name) and not _constraint_exists(cursor, table_name, constraint_name):
                cursor.execute(statement)


def drop_iopp_variant_constraints(apps, schema_editor) -> None:
    if schema_editor.connection.vendor != "microsoft":
        return

    with schema_editor.connection.cursor() as cursor:
        for table_name, constraint_name, _statement in reversed(CONSTRAINT_SQL):
            if _constraint_exists(cursor, table_name, constraint_name):
                cursor.execute(f"ALTER TABLE dbo.{table_name} DROP CONSTRAINT {constraint_name}")


class Migration(migrations.Migration):
    dependencies = [
        ("certs", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(add_iopp_variant_constraints, drop_iopp_variant_constraints),
    ]
