import uuid

from django.db import migrations, models
from django.utils import timezone


CREATE_QUALIFYING_BODY_SQL = r"""
IF OBJECT_ID('dbo.aud_master_qual_body', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.aud_master_qual_body (
        id uniqueidentifier NOT NULL PRIMARY KEY DEFAULT NEWSEQUENTIALID(),
        body_name varchar(200) NOT NULL,
        is_active bit NOT NULL DEFAULT 1,
        is_deleted bit NOT NULL DEFAULT 0,
        created_by varchar(100) NULL,
        created_date datetimeoffset NOT NULL DEFAULT SYSDATETIMEOFFSET(),
        updated_by varchar(100) NULL,
        updated_date datetimeoffset NULL,
        CONSTRAINT UQ_aud_master_qual_body_name UNIQUE (body_name)
    );
END;
"""


DROP_QUALIFYING_BODY_SQL = r"""
IF OBJECT_ID('dbo.aud_master_qual_body', 'U') IS NOT NULL
BEGIN
    DROP TABLE dbo.aud_master_qual_body;
END;
"""


DEFAULT_QUALIFYING_BODIES = (
    "KSM",
    "KSM Academy",
    "Company Approved",
    "Internal Training",
    "IRCA",
    "DNV",
    "ABS",
    "Bureau Veritas",
    "ClassNK",
    "Korean Register",
    "Lloyds Register",
    "RINA",
    "Other",
)


def seed_qualifying_bodies(apps, schema_editor):
    names = list(DEFAULT_QUALIFYING_BODIES)

    if schema_editor.connection.vendor == "sqlite":
        AuditQualifyingBody = apps.get_model("inspection", "AuditQualifyingBody")
        MasterAuditQualifiedAuditor = apps.get_model("inspection", "MasterAuditQualifiedAuditor")
        existing_bodies = MasterAuditQualifiedAuditor.objects.exclude(qualifying_body__isnull=True).values_list(
            "qualifying_body",
            flat=True,
        )
        for row in existing_bodies:
            name = str(row or "").strip()
            if name and name not in names:
                names.append(name)
        for name in names:
            AuditQualifyingBody.objects.get_or_create(
                body_name=name,
                defaults={
                    "is_active": True,
                    "is_deleted": False,
                    "created_by": "migration.0026",
                },
            )
        return

    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT DISTINCT qualifying_body
            FROM dbo.master_audit_qualified_auditor
            WHERE qualifying_body IS NOT NULL
              AND LTRIM(RTRIM(qualifying_body)) <> ''
            """
        )
        for row in cursor.fetchall():
            name = str(row[0] or "").strip()
            if name and name not in names:
                names.append(name)

        for name in names:
            cursor.execute(
                """
                IF NOT EXISTS (
                    SELECT 1
                    FROM dbo.aud_master_qual_body
                    WHERE body_name = %s
                )
                BEGIN
                    INSERT INTO dbo.aud_master_qual_body (
                        body_name,
                        is_active,
                        is_deleted,
                        created_by,
                        created_date
                    )
                    VALUES (%s, 1, 0, %s, SYSDATETIMEOFFSET());
                END;
                """,
                [name, name, "migration.0026"],
            )


class Migration(migrations.Migration):

    dependencies = [
        ("inspection", "0025_masterauditplan_lead_auditor_user_id"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql=CREATE_QUALIFYING_BODY_SQL,
                    reverse_sql=DROP_QUALIFYING_BODY_SQL,
                )
            ],
            state_operations=[
                migrations.CreateModel(
                    name="AuditQualifyingBody",
                    fields=[
                        (
                            "id",
                            models.UUIDField(
                                default=uuid.uuid4,
                                editable=False,
                                primary_key=True,
                                serialize=False,
                            ),
                        ),
                        ("created_by", models.CharField(blank=True, max_length=100, null=True)),
                        ("created_date", models.DateTimeField(default=timezone.now)),
                        ("updated_by", models.CharField(blank=True, max_length=100, null=True)),
                        ("updated_date", models.DateTimeField(blank=True, null=True)),
                        ("body_name", models.CharField(max_length=200, unique=True)),
                        ("is_active", models.BooleanField(default=True)),
                        ("is_deleted", models.BooleanField(default=False)),
                    ],
                    options={
                        "db_table": "aud_master_qual_body",
                    },
                ),
            ],
        ),
        migrations.RunPython(seed_qualifying_bodies, migrations.RunPython.noop),
    ]
