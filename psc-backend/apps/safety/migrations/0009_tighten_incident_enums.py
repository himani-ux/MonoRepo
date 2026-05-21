from __future__ import annotations

from django.db import migrations, models
from django.db.models import Q


SCHEMA_VERSION_TIGHT_ENUMS = 2
ACTIVE_STATES = (
    "DRAFT",
    "SUBMITTED",
    "IN_PROGRESS",
    "UNDER_REVIEW",
    "APPROVED",
    "SENT_BACK",
    "REOPENED",
    "CLOSED",
    "TRIAGED",
    "SUPERSEDED",
)
INVESTIGATION_DEPTHS = ("SHALLOW", "MEDIUM", "DEEP")


class Migration(migrations.Migration):
    dependencies = [
        ("safety", "0008_case_study_library"),
    ]

    operations = [
        migrations.AlterField(
            model_name="vimssafetyincident",
            name="state",
            field=models.CharField(default="DRAFT", max_length=48),
        ),
        migrations.AlterField(
            model_name="vimssafetyincident",
            name="schema_version",
            field=models.IntegerField(db_default=2, default=2),
        ),
        migrations.RemoveConstraint(
            model_name="vimssafetyincident",
            name="ck_vims_safety_incident_phase",
        ),
        migrations.AddConstraint(
            model_name="vimssafetyincident",
            constraint=models.CheckConstraint(
                condition=Q(state__in=ACTIVE_STATES) | Q(schema_version__lt=SCHEMA_VERSION_TIGHT_ENUMS),
                name="ck_vims_safety_incident_state_schema_v2",
            ),
        ),
        migrations.AddConstraint(
            model_name="vimssafetyincident",
            constraint=models.CheckConstraint(
                condition=(
                    Q(schema_version__lt=SCHEMA_VERSION_TIGHT_ENUMS)
                    & Q(phase__gte=0)
                    & Q(phase__lte=8)
                )
                | (
                    Q(schema_version__gte=SCHEMA_VERSION_TIGHT_ENUMS)
                    & Q(phase__gte=1)
                    & Q(phase__lte=8)
                ),
                name="ck_vims_safety_incident_phase",
            ),
        ),
        migrations.AddConstraint(
            model_name="vimssafetyincident",
            constraint=models.CheckConstraint(
                condition=Q(investigation_depth__isnull=True)
                | Q(investigation_depth__in=INVESTIGATION_DEPTHS)
                | Q(schema_version__lt=SCHEMA_VERSION_TIGHT_ENUMS),
                name="ck_vims_safety_incident_depth_schema_v2",
            ),
        ),
    ]
