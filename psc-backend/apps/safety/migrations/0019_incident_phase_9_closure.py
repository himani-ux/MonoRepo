from __future__ import annotations

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):
    dependencies = [
        ("safety", "0018_widen_incident_type_code"),
    ]

    operations = [
        migrations.AlterField(
            model_name="incident",
            name="phase",
            field=models.PositiveSmallIntegerField(
                default=1,
                validators=[MinValueValidator(0), MaxValueValidator(9)],
            ),
        ),
        migrations.RemoveConstraint(
            model_name="incident",
            name="ck_vims_safety_incident_phase",
        ),
        migrations.AddConstraint(
            model_name="incident",
            constraint=models.CheckConstraint(
                condition=(
                    Q(schema_version__lt=2)
                    & Q(phase__gte=0)
                    & Q(phase__lte=9)
                )
                | (
                    Q(schema_version__gte=2)
                    & Q(phase__gte=1)
                    & Q(phase__lte=9)
                ),
                name="ck_vims_safety_incident_phase",
            ),
        ),
        migrations.AlterField(
            model_name="incidentphaselog",
            name="phase_from",
            field=models.PositiveSmallIntegerField(
                blank=True,
                choices=[
                    (1, "Phase 1"),
                    (2, "Phase 2"),
                    (3, "Phase 3"),
                    (4, "Phase 4"),
                    (5, "Phase 5"),
                    (6, "Phase 6"),
                    (7, "Phase 7"),
                    (8, "Phase 8"),
                    (9, "Phase 9"),
                ],
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="incidentphaselog",
            name="phase_to",
            field=models.PositiveSmallIntegerField(
                choices=[
                    (1, "Phase 1"),
                    (2, "Phase 2"),
                    (3, "Phase 3"),
                    (4, "Phase 4"),
                    (5, "Phase 5"),
                    (6, "Phase 6"),
                    (7, "Phase 7"),
                    (8, "Phase 8"),
                    (9, "Phase 9"),
                ],
            ),
        ),
        migrations.RemoveConstraint(
            model_name="incidentphaselog",
            name="ck_vims_safety_incident_phase_log_phase_from_range",
        ),
        migrations.RemoveConstraint(
            model_name="incidentphaselog",
            name="ck_vims_safety_incident_phase_log_phase_to_range",
        ),
        migrations.AddConstraint(
            model_name="incidentphaselog",
            constraint=models.CheckConstraint(
                condition=Q(phase_from__isnull=True) | (Q(phase_from__gte=1) & Q(phase_from__lte=9)),
                name="ck_vims_safety_incident_phase_log_phase_from_range",
            ),
        ),
        migrations.AddConstraint(
            model_name="incidentphaselog",
            constraint=models.CheckConstraint(
                condition=Q(phase_to__gte=1) & Q(phase_to__lte=9),
                name="ck_vims_safety_incident_phase_log_phase_to_range",
            ),
        ),
    ]
