# Generated manually for VIMS Audit Phase 1 Step 1.4 on 2026-07-29.

import uuid

from django.db import migrations, models
from django.utils import timezone


CREATE_AUDIT_LEGACY_INSPECTION_TAG_SQL = r"""
IF OBJECT_ID('dbo.audit_legacy_inspection_tag', 'U') IS NOT NULL
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM sys.columns c
        JOIN sys.types ty ON ty.user_type_id = c.user_type_id
        WHERE c.object_id = OBJECT_ID(N'dbo.audit_legacy_inspection_tag')
          AND c.name = N'id'
          AND ty.name = N'uniqueidentifier'
          AND c.is_identity = 0
    )
    OR NOT EXISTS (
        SELECT 1
        FROM sys.default_constraints dc
        JOIN sys.columns c ON c.object_id = dc.parent_object_id
                          AND c.column_id = dc.parent_column_id
        WHERE dc.parent_object_id = OBJECT_ID(N'dbo.audit_legacy_inspection_tag')
          AND c.name = N'id'
          AND LOWER(dc.definition) LIKE N'%(newsequentialid())%'
    )
    OR NOT EXISTS (
        SELECT 1
        FROM sys.key_constraints kc
        JOIN sys.index_columns ic ON ic.object_id = kc.parent_object_id
                                 AND ic.index_id = kc.unique_index_id
        JOIN sys.columns c ON c.object_id = ic.object_id
                          AND c.column_id = ic.column_id
        WHERE kc.parent_object_id = OBJECT_ID(N'dbo.audit_legacy_inspection_tag')
          AND kc.type = N'PK'
          AND c.name = N'id'
    )
    OR NOT EXISTS (
        SELECT 1
        FROM sys.columns c
        JOIN sys.types ty ON ty.user_type_id = c.user_type_id
        WHERE c.object_id = OBJECT_ID(N'dbo.audit_legacy_inspection_tag')
          AND c.name = N'psc_inspection_id'
          AND ty.name = N'char'
          AND c.max_length = 32
          AND c.is_nullable = 0
    )
    OR NOT EXISTS (
        SELECT 1
        FROM sys.columns c
        JOIN sys.types ty ON ty.user_type_id = c.user_type_id
        WHERE c.object_id = OBJECT_ID(N'dbo.audit_legacy_inspection_tag')
          AND c.name = N'is_legacy'
          AND ty.name = N'bit'
          AND c.is_nullable = 0
    )
    OR NOT EXISTS (
        SELECT 1
        FROM sys.columns c
        JOIN sys.types ty ON ty.user_type_id = c.user_type_id
        WHERE c.object_id = OBJECT_ID(N'dbo.audit_legacy_inspection_tag')
          AND c.name = N'tagged_at'
          AND ty.name = N'datetimeoffset'
          AND c.is_nullable = 0
    )
    OR NOT EXISTS (
        SELECT 1
        FROM sys.columns c
        JOIN sys.types ty ON ty.user_type_id = c.user_type_id
        WHERE c.object_id = OBJECT_ID(N'dbo.audit_legacy_inspection_tag')
          AND c.name = N'tagged_by'
          AND ty.name = N'nvarchar'
          AND c.max_length = 200
          AND c.is_nullable = 0
    )
    OR NOT EXISTS (
        SELECT 1
        FROM sys.columns c
        JOIN sys.types ty ON ty.user_type_id = c.user_type_id
        WHERE c.object_id = OBJECT_ID(N'dbo.audit_legacy_inspection_tag')
          AND c.name = N'tag_reason'
          AND ty.name = N'nvarchar'
          AND c.max_length = 800
          AND c.is_nullable = 1
    )
    OR EXISTS (
        SELECT 1
        FROM sys.foreign_keys
        WHERE parent_object_id = OBJECT_ID(N'dbo.audit_legacy_inspection_tag')
    )
    BEGIN
        THROW 51021, 'audit_legacy_inspection_tag exists with an incompatible schema.', 1;
    END;
END
ELSE
BEGIN
    CREATE TABLE dbo.audit_legacy_inspection_tag (
        id uniqueidentifier NOT NULL PRIMARY KEY DEFAULT NEWSEQUENTIALID(),
        psc_inspection_id char(32) NOT NULL,
        is_legacy bit NOT NULL DEFAULT 1,
        tagged_at datetimeoffset NOT NULL DEFAULT SYSDATETIMEOFFSET(),
        tagged_by nvarchar(100) NOT NULL,
        tag_reason nvarchar(400) NULL
    );
END;

IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = N'UX_audit_legacy_inspection_tag_insp'
      AND object_id = OBJECT_ID(N'dbo.audit_legacy_inspection_tag')
)
BEGIN
    CREATE UNIQUE INDEX UX_audit_legacy_inspection_tag_insp
        ON dbo.audit_legacy_inspection_tag(psc_inspection_id);
END;
"""


DROP_AUDIT_LEGACY_INSPECTION_TAG_SQL = r"""
DROP TABLE IF EXISTS dbo.audit_legacy_inspection_tag;
"""


def uuid_pk():
    return models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)


class Migration(migrations.Migration):
    dependencies = [
        ("inspection", "0021_audit_detail_scope_columns_and_indexes"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql=CREATE_AUDIT_LEGACY_INSPECTION_TAG_SQL,
                    reverse_sql=DROP_AUDIT_LEGACY_INSPECTION_TAG_SQL,
                ),
            ],
            state_operations=[
                migrations.CreateModel(
                    name="AuditLegacyInspectionTag",
                    fields=[
                        ("id", uuid_pk()),
                        ("psc_inspection_id", models.CharField(max_length=32, unique=True)),
                        ("is_legacy", models.BooleanField(default=True)),
                        ("tagged_at", models.DateTimeField(default=timezone.now)),
                        ("tagged_by", models.CharField(max_length=100)),
                        ("tag_reason", models.CharField(blank=True, max_length=400, null=True)),
                    ],
                    options={"db_table": "audit_legacy_inspection_tag"},
                ),
            ],
        )
    ]

