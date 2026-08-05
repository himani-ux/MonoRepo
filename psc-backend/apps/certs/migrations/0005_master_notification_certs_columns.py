from __future__ import annotations

from django.db import migrations


MASTER_NOTIFICATION_CERTS_COLUMNS = (
    ("module_code", "NVARCHAR(32) NULL"),
    ("record_id", "NVARCHAR(128) NULL"),
    ("recipient_ref", "NVARCHAR(128) NULL"),
    ("notification_kind", "NVARCHAR(64) NULL"),
    ("title", "NVARCHAR(256) NULL"),
    ("message", "NVARCHAR(MAX) NULL"),
    ("delivery_channel", "NVARCHAR(32) NULL"),
    ("payload_json", "NVARCHAR(MAX) NULL"),
    ("created_at", "DATETIME2(7) NULL"),
)


def add_master_notification_certs_columns(apps, schema_editor) -> None:
    if schema_editor.connection.vendor != "microsoft":
        return

    with schema_editor.connection.cursor() as cursor:
        for column_name, column_type in MASTER_NOTIFICATION_CERTS_COLUMNS:
            cursor.execute(
                f"""
                IF OBJECT_ID(N'dbo.master_notification', N'U') IS NOT NULL
                   AND COL_LENGTH(N'dbo.master_notification', %s) IS NULL
                BEGIN
                    ALTER TABLE dbo.master_notification ADD {column_name} {column_type}
                END
                """,
                [column_name],
            )


def noop_reverse(apps, schema_editor) -> None:
    return


class Migration(migrations.Migration):
    dependencies = [
        ("certs", "0004_initial"),
    ]

    operations = [
        migrations.RunPython(add_master_notification_certs_columns, noop_reverse),
    ]
