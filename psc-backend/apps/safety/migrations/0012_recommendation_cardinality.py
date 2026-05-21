from __future__ import annotations

from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):
    dependencies = [
        ("safety", "0011_soft_archive_final"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="vimssafetyrecommendation",
            constraint=models.UniqueConstraint(
                fields=("incident_id", "tier"),
                condition=Q(is_deleted=False),
                name="uq_vims_safety_recommendation_incident_tier_active",
            ),
        ),
    ]
