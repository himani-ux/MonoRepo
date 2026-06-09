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
    "READY_FOR_OFFICE_COMMENTS",
    "REWORK_REQUIRED",
    "OFFICE_COMMENTS_COMPLETED",
    "SUPERSEDED",
)


def rename_near_miss_states(apps, schema_editor):
    Incident = apps.get_model("safety", "Incident")
    Incident.objects.filter(state="READY_FOR_DPA_TRIAGE").update(state="READY_FOR_OFFICE_COMMENTS")
    Incident.objects.filter(state="TRIAGED").update(state="OFFICE_COMMENTS_COMPLETED")


def restore_near_miss_states(apps, schema_editor):
    Incident = apps.get_model("safety", "Incident")
    Incident.objects.filter(state="READY_FOR_OFFICE_COMMENTS").update(state="READY_FOR_DPA_TRIAGE")
    Incident.objects.filter(state="OFFICE_COMMENTS_COMPLETED").update(state="TRIAGED")


class Migration(migrations.Migration):

    dependencies = [
        ("safety", "0035_scm_closed_state"),
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
                    ("READY_FOR_OFFICE_COMMENTS", "Ready for Office Comments"),
                    ("REWORK_REQUIRED", "Rework Required"),
                    ("OFFICE_COMMENTS_COMPLETED", "Office Comments Completed"),
                    ("SUPERSEDED", "Superseded"),
                ],
                db_index=True,
                default="DRAFT",
                max_length=48,
            ),
        ),
        migrations.RunPython(rename_near_miss_states, restore_near_miss_states),
        migrations.AddConstraint(
            model_name="incident",
            constraint=models.CheckConstraint(
                condition=models.Q(state__in=ACTIVE_STATES) | models.Q(schema_version__lt=2),
                name="ck_vims_safety_incident_state_schema_v2",
            ),
        ),
    ]
