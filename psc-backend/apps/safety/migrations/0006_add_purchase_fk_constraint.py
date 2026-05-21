from __future__ import annotations

from django.db import migrations


CONSTRAINT_NAME = "FK_vims_safety_corrective_action_purchase"


def add_purchase_fk_constraint(apps, schema_editor) -> None:
    if schema_editor.connection.vendor != "microsoft":
        return

    existing_tables = set(schema_editor.connection.introspection.table_names())
    if "vims_safety_corrective_action" not in existing_tables or "pur_requisition" not in existing_tables:
        return

    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            "SELECT 1 FROM sys.foreign_keys WHERE name = %s",
            [CONSTRAINT_NAME],
        )
        if cursor.fetchone() is not None:
            return

        cursor.execute(
            """
            ALTER TABLE dbo.vims_safety_corrective_action WITH CHECK
            ADD CONSTRAINT FK_vims_safety_corrective_action_purchase
            FOREIGN KEY (purchase_req_id) REFERENCES dbo.pur_requisition(id)
            """
        )


def drop_purchase_fk_constraint(apps, schema_editor) -> None:
    if schema_editor.connection.vendor != "microsoft":
        return

    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            "SELECT 1 FROM sys.foreign_keys WHERE name = %s",
            [CONSTRAINT_NAME],
        )
        if cursor.fetchone() is None:
            return

        cursor.execute(
            """
            ALTER TABLE dbo.vims_safety_corrective_action
            DROP CONSTRAINT FK_vims_safety_corrective_action_purchase
            """
        )


class Migration(migrations.Migration):
    dependencies = [
        ("safety", "0005_external_party_injury"),
    ]

    operations = [
        migrations.RunPython(add_purchase_fk_constraint, drop_purchase_fk_constraint),
    ]
