from __future__ import annotations

from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):
    dependencies = [
        ("safety", "0013_soi_finding_state_final"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="vimssafetyincidentphaselog",
            name="ck_vims_safety_incident_phase_log_loop_back_reason",
        ),
        migrations.AddConstraint(
            model_name="vimssafetyincidentphaselog",
            constraint=models.CheckConstraint(
                condition=~Q(transition_type="LOOP_BACK")
                | (Q(loop_back_reason__isnull=False) & ~Q(loop_back_reason="")),
                name="ck_vims_safety_incident_phase_log_loop_back_reason",
            ),
        ),
        migrations.AddConstraint(
            model_name="vimssafetyincidentphaselog",
            constraint=models.CheckConstraint(
                condition=Q(phase_from__isnull=True)
                | (Q(phase_from__gte=1) & Q(phase_from__lte=8)),
                name="ck_vims_safety_incident_phase_log_phase_from_range",
            ),
        ),
        migrations.AddConstraint(
            model_name="vimssafetyincidentphaselog",
            constraint=models.CheckConstraint(
                condition=Q(phase_to__gte=1) & Q(phase_to__lte=8),
                name="ck_vims_safety_incident_phase_log_phase_to_range",
            ),
        ),
    ]
