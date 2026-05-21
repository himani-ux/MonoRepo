from __future__ import annotations

from django.db import migrations, models
from django.db.models import Q


def normalize_legacy_in_progress_rows(apps, schema_editor) -> None:
    VimsSafetySoiFinding = apps.get_model("safety", "VimsSafetySoiFinding")
    VimsSafetySoiFinding.objects.filter(status="IN_PROGRESS").update(status="OPEN")


class Migration(migrations.Migration):
    dependencies = [
        ("safety", "0012_recommendation_cardinality"),
    ]

    operations = [
        migrations.RunPython(normalize_legacy_in_progress_rows, migrations.RunPython.noop),
        migrations.RemoveConstraint(
            model_name="vimssafetysoifinding",
            name="ck_vims_safety_soi_finding_status",
        ),
        migrations.AddConstraint(
            model_name="vimssafetysoifinding",
            constraint=models.CheckConstraint(
                condition=Q(
                    status__in=[
                        "OPEN",
                        "PENDING_CLOSURE",
                        "MASTER_APPROVED",
                        "CLOSED",
                        "CARRIED_FORWARD",
                    ]
                ),
                name="ck_vims_safety_soi_finding_status",
            ),
        ),
    ]
