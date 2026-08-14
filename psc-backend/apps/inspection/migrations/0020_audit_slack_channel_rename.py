# Generated manually for VIMS Audit Phase 1 Step 1.2 repair on 2026-07-27.

import uuid

from django.db import migrations, models
from django.utils import timezone


CREATE_AUDIT_SLACK_CHANNEL_SQL = r"""
IF OBJECT_ID('dbo.master_audit_slack_channel', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.master_audit_slack_channel (
        id uniqueidentifier NOT NULL PRIMARY KEY DEFAULT NEWSEQUENTIALID(),
        channel_name nvarchar(80) NOT NULL,
        webhook_url nvarchar(500) NOT NULL,
        scope_type varchar(20) NOT NULL,
        scope_value nvarchar(100) NULL,
        notification_types_csv nvarchar(500) NOT NULL,
        is_active bit NOT NULL DEFAULT 1,
        created_by varchar(100) NULL,
        created_date datetimeoffset NOT NULL DEFAULT SYSDATETIMEOFFSET()
    );
END;
"""


DROP_AUDIT_SLACK_CHANNEL_SQL = r"""
DROP TABLE IF EXISTS dbo.master_audit_slack_channel;
"""


def uuid_pk():
    return models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)


def created_fields():
    return [
        ("created_by", models.CharField(blank=True, max_length=100, null=True)),
        ("created_date", models.DateTimeField(default=timezone.now)),
    ]


class Migration(migrations.Migration):
    dependencies = [
        ("inspection", "0019_audit_master_tables"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql=CREATE_AUDIT_SLACK_CHANNEL_SQL,
                    reverse_sql=DROP_AUDIT_SLACK_CHANNEL_SQL,
                ),
            ],
            state_operations=[
                migrations.CreateModel(
                    name="MasterSlackChannel",
                    fields=[
                        ("id", uuid_pk()),
                        ("channel_name", models.CharField(max_length=80)),
                        ("webhook_url", models.CharField(max_length=500)),
                        ("scope_type", models.CharField(max_length=20)),
                        ("scope_value", models.CharField(blank=True, max_length=100, null=True)),
                        ("notification_types_csv", models.CharField(max_length=500)),
                        ("is_active", models.BooleanField(default=True)),
                        *created_fields(),
                    ],
                    options={"db_table": "master_audit_slack_channel"},
                ),
            ],
        )
    ]

