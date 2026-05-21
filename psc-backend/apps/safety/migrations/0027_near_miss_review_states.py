from django.db import migrations, models


ACTIVE_STATES = (
    "DRAFT",
    "SUBMITTED",
    "IN_PROGRESS",
    "UNDER_REVIEW",
    "APPROVED",
    "SENT_BACK",
    "REOPENED",
    "CLOSED",
    "PENDING_VESSEL_REVIEW",
    "READY_FOR_DPA_TRIAGE",
    "REWORK_REQUIRED",
    "TRIAGED",
    "SUPERSEDED",
)


class Migration(migrations.Migration):

    dependencies = [
        ("safety", "0026_widen_soi_finding_shell_tag"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="incident",
            name="ck_vims_safety_incident_state_schema_v2",
        ),
        migrations.AlterField(
            model_name="incident",
            name="state",
            field=models.CharField(
                choices=[
                    ("DRAFT", "Draft"),
                    ("SUBMITTED", "Submitted"),
                    ("IN_PROGRESS", "In Progress"),
                    ("UNDER_REVIEW", "Under Review"),
                    ("APPROVED", "Approved"),
                    ("SENT_BACK", "Sent Back"),
                    ("REOPENED", "Reopened"),
                    ("CLOSED", "Closed"),
                    ("PENDING_VESSEL_REVIEW", "Pending Vessel Review"),
                    ("READY_FOR_DPA_TRIAGE", "Ready for DPA Triage"),
                    ("REWORK_REQUIRED", "Rework Required"),
                    ("TRIAGED", "Triaged"),
                    ("SUPERSEDED", "Superseded"),
                ],
                db_index=True,
                default="DRAFT",
                max_length=48,
            ),
        ),
        migrations.AddConstraint(
            model_name="incident",
            constraint=models.CheckConstraint(
                condition=models.Q(state__in=ACTIVE_STATES) | models.Q(schema_version__lt=2),
                name="ck_vims_safety_incident_state_schema_v2",
            ),
        ),
    ]
