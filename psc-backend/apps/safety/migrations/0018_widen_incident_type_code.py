from __future__ import annotations

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("safety", "0017_align_relation_state"),
    ]

    operations = [
        migrations.RunSQL(
            sql=(
                "ALTER TABLE master_safety_incident_type "
                "ALTER COLUMN type_code nvarchar(64) NOT NULL"
            ),
            reverse_sql=(
                "ALTER TABLE master_safety_incident_type "
                "ALTER COLUMN type_code nvarchar(32) NOT NULL"
            ),
        ),
    ]
