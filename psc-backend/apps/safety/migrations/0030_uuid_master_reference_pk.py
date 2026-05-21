from __future__ import annotations

import uuid

from django.db import migrations, models


MASTER_REFERENCE_TABLES = (
    "master_mscat_taxonomy",
    "master_immediate_causes",
    "master_loss_types",
    "master_soi_area",
    "master_soi_area_item",
    "master_soi_checklist_version",
    "master_safety_incident_type",
    "master_safety_bias_guard",
    "master_safety_case_study",
)


def _column_exists(cursor, table_name: str, column_name: str) -> bool:
    cursor.execute(
        """
        SELECT COUNT(*)
        FROM sys.columns
        WHERE object_id = OBJECT_ID(%s)
          AND name = %s
        """,
        [f"dbo.{table_name}", column_name],
    )
    return int(cursor.fetchone()[0] or 0) > 0


def _primary_key_column(cursor, table_name: str) -> str | None:
    cursor.execute(
        """
        SELECT TOP 1 c.name
        FROM sys.key_constraints kc
        JOIN sys.index_columns ic
          ON ic.object_id = kc.parent_object_id
         AND ic.index_id = kc.unique_index_id
        JOIN sys.columns c
          ON c.object_id = ic.object_id
         AND c.column_id = ic.column_id
        WHERE kc.parent_object_id = OBJECT_ID(%s)
          AND kc.type = 'PK'
        ORDER BY ic.key_ordinal
        """,
        [f"dbo.{table_name}"],
    )
    row = cursor.fetchone()
    return str(row[0]) if row else None


def _convert_table(cursor, table_name: str) -> None:
    if not _column_exists(cursor, table_name, "id"):
        return

    # Already converted.
    if _column_exists(cursor, table_name, "legacy_int_id"):
        return

    quoted_table = f"[dbo].[{table_name}]"
    pk_name = f"pk_{table_name}"
    legacy_unique_name = f"uq_{table_name}_legacy_int_id"
    default_name = f"df_{table_name}_id_uuid"

    if not _column_exists(cursor, table_name, "id_uuid"):
        cursor.execute(f"ALTER TABLE {quoted_table} ADD [id_uuid] char(32) NULL")

    cursor.execute(
        f"""
        UPDATE {quoted_table}
           SET [id_uuid] = LOWER(REPLACE(CONVERT(char(36), NEWID()), '-', ''))
         WHERE [id_uuid] IS NULL
        """
    )
    cursor.execute(f"ALTER TABLE {quoted_table} ALTER COLUMN [id_uuid] char(32) NOT NULL")

    cursor.execute(
        f"""
        DECLARE @pk_name sysname;
        SELECT @pk_name = kc.name
        FROM sys.key_constraints kc
        WHERE kc.parent_object_id = OBJECT_ID(N'dbo.{table_name}')
          AND kc.type = 'PK';
        IF @pk_name IS NOT NULL
            EXEC('ALTER TABLE [dbo].[{table_name}] DROP CONSTRAINT [' + @pk_name + ']');
        """,
    )

    cursor.execute(f"EXEC sp_rename 'dbo.{table_name}.id', 'legacy_int_id', 'COLUMN'")
    cursor.execute(f"EXEC sp_rename 'dbo.{table_name}.id_uuid', 'id', 'COLUMN'")

    cursor.execute(
        f"""
        IF NOT EXISTS (
            SELECT 1
            FROM sys.key_constraints
            WHERE parent_object_id = OBJECT_ID(N'dbo.{table_name}')
              AND type = 'PK'
        )
            ALTER TABLE {quoted_table} ADD CONSTRAINT [{pk_name}] PRIMARY KEY CLUSTERED ([id])
        """
    )
    cursor.execute(
        f"""
        IF NOT EXISTS (
            SELECT 1
            FROM sys.indexes
            WHERE object_id = OBJECT_ID(N'dbo.{table_name}')
              AND name = N'{legacy_unique_name}'
        )
            ALTER TABLE {quoted_table} ADD CONSTRAINT [{legacy_unique_name}] UNIQUE ([legacy_int_id])
        """
    )
    cursor.execute(
        f"""
        IF NOT EXISTS (
            SELECT 1
            FROM sys.default_constraints dc
            JOIN sys.columns c
              ON c.object_id = dc.parent_object_id
             AND c.column_id = dc.parent_column_id
            WHERE dc.parent_object_id = OBJECT_ID(N'dbo.{table_name}')
              AND c.name = N'id'
        )
            ALTER TABLE {quoted_table}
              ADD CONSTRAINT [{default_name}]
              DEFAULT LOWER(REPLACE(CONVERT(char(36), NEWID()), '-', '')) FOR [id]
        """
    )

    pk_column = _primary_key_column(cursor, table_name)
    if pk_column != "id":
        raise RuntimeError(f"{table_name} UUID primary-key conversion failed.")


def convert_master_reference_primary_keys(apps, schema_editor) -> None:
    if schema_editor.connection.vendor != "microsoft":
        return
    with schema_editor.connection.cursor() as cursor:
        for table_name in MASTER_REFERENCE_TABLES:
            _convert_table(cursor, table_name)


class Migration(migrations.Migration):
    dependencies = [
        ("safety", "0029_public_uuid_identity"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(convert_master_reference_primary_keys, migrations.RunPython.noop),
            ],
            state_operations=[
                migrations.AddField(
                    model_name="mastermscattaxonomy",
                    name="legacy_int_id",
                    field=models.BigIntegerField(editable=False, unique=True),
                ),
                migrations.AlterField(
                    model_name="mastermscattaxonomy",
                    name="id",
                    field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False),
                ),
                migrations.AddField(
                    model_name="masterimmediatecause",
                    name="legacy_int_id",
                    field=models.BigIntegerField(editable=False, unique=True),
                ),
                migrations.AlterField(
                    model_name="masterimmediatecause",
                    name="id",
                    field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False),
                ),
                migrations.AddField(
                    model_name="masterlosstype",
                    name="legacy_int_id",
                    field=models.BigIntegerField(editable=False, unique=True),
                ),
                migrations.AlterField(
                    model_name="masterlosstype",
                    name="id",
                    field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False),
                ),
                migrations.AddField(
                    model_name="mastersoiarea",
                    name="legacy_int_id",
                    field=models.BigIntegerField(editable=False, unique=True),
                ),
                migrations.AlterField(
                    model_name="mastersoiarea",
                    name="id",
                    field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False),
                ),
                migrations.AddField(
                    model_name="mastersoiareaitem",
                    name="legacy_int_id",
                    field=models.BigIntegerField(editable=False, unique=True),
                ),
                migrations.AlterField(
                    model_name="mastersoiareaitem",
                    name="id",
                    field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False),
                ),
                migrations.AddField(
                    model_name="soichecklistversion",
                    name="legacy_int_id",
                    field=models.BigIntegerField(editable=False, unique=True),
                ),
                migrations.AlterField(
                    model_name="soichecklistversion",
                    name="id",
                    field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False),
                ),
                migrations.AddField(
                    model_name="mastersafetyincidenttype",
                    name="legacy_int_id",
                    field=models.BigIntegerField(editable=False, unique=True),
                ),
                migrations.AlterField(
                    model_name="mastersafetyincidenttype",
                    name="id",
                    field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False),
                ),
                migrations.AddField(
                    model_name="mastersafetybiasguard",
                    name="legacy_int_id",
                    field=models.BigIntegerField(editable=False, unique=True),
                ),
                migrations.AlterField(
                    model_name="mastersafetybiasguard",
                    name="id",
                    field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False),
                ),
                migrations.AddField(
                    model_name="safetycasestudy",
                    name="legacy_int_id",
                    field=models.BigIntegerField(editable=False, unique=True),
                ),
                migrations.AlterField(
                    model_name="safetycasestudy",
                    name="id",
                    field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False),
                ),
            ],
        ),
    ]
