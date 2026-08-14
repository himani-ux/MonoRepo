# Generated manually for VIMS Audit Phase 2 Step 2.2 Debug Step 4 on 2026-07-29.

from django.db import migrations, models


WIDEN_AUDIT_SEED_TEXT_COLUMNS_SQL = r"""
ALTER TABLE dbo.master_audit_checklist_item
    ALTER COLUMN location_code varchar(200) NULL;

ALTER TABLE dbo.master_audit_checklist_item
    ALTER COLUMN regulation_ref nvarchar(500) NULL;

ALTER TABLE dbo.master_stcw_section
    ALTER COLUMN code_version varchar(100) NOT NULL;
"""


NARROW_AUDIT_SEED_TEXT_COLUMNS_SQL = r"""
ALTER TABLE dbo.master_audit_checklist_item
    ALTER COLUMN location_code varchar(20) NULL;

ALTER TABLE dbo.master_audit_checklist_item
    ALTER COLUMN regulation_ref nvarchar(200) NULL;

ALTER TABLE dbo.master_stcw_section
    ALTER COLUMN code_version varchar(40) NOT NULL;
"""


class Migration(migrations.Migration):
    dependencies = [
        ("inspection", "0022_audit_legacy_inspection_tag"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql=WIDEN_AUDIT_SEED_TEXT_COLUMNS_SQL,
                    reverse_sql=NARROW_AUDIT_SEED_TEXT_COLUMNS_SQL,
                ),
            ],
            state_operations=[
                migrations.AlterField(
                    model_name="masterauditchecklistitem",
                    name="location_code",
                    field=models.CharField(blank=True, max_length=200, null=True),
                ),
                migrations.AlterField(
                    model_name="masterauditchecklistitem",
                    name="regulation_ref",
                    field=models.CharField(blank=True, max_length=500, null=True),
                ),
                migrations.AlterField(
                    model_name="masterstcwsection",
                    name="code_version",
                    field=models.CharField(max_length=100),
                ),
            ],
        ),
    ]

