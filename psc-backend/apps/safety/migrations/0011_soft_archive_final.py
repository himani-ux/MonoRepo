from __future__ import annotations

from django.db import migrations, models
from django.db.models import Q


def backfill_archive_flags(apps, schema_editor):
    model_names = (
        "VimsSafetyIncident",
        "VimsSafetyScmMeeting",
        "VimsSafetySoiInspection",
    )

    for model_name in model_names:
        model = apps.get_model("safety", model_name)
        model.objects.filter(archived_at__isnull=False).update(is_archived=True)
        model.objects.filter(archived_at__isnull=True).update(is_archived=False)


class Migration(migrations.Migration):
    dependencies = [
        ("safety", "0010_field_history_shape"),
    ]

    operations = [
        migrations.AddField(
            model_name="vimssafetyincident",
            name="is_archived",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="vimssafetyscmmeeting",
            name="is_archived",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="vimssafetysoiinspection",
            name="is_archived",
            field=models.BooleanField(db_default=False, default=False),
        ),
        migrations.RunPython(backfill_archive_flags, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name="vimssafetyincident",
            constraint=models.CheckConstraint(
                condition=(Q(is_archived=False) & Q(archived_at__isnull=True))
                | (Q(is_archived=True) & Q(archived_at__isnull=False)),
                name="ck_vims_safety_incident_archive_pair",
            ),
        ),
        migrations.AddConstraint(
            model_name="vimssafetyscmmeeting",
            constraint=models.CheckConstraint(
                condition=(Q(is_archived=False) & Q(archived_at__isnull=True))
                | (Q(is_archived=True) & Q(archived_at__isnull=False)),
                name="ck_vims_safety_scm_meeting_archive_pair",
            ),
        ),
        migrations.AddConstraint(
            model_name="vimssafetysoiinspection",
            constraint=models.CheckConstraint(
                condition=(Q(is_archived=False) & Q(archived_at__isnull=True))
                | (Q(is_archived=True) & Q(archived_at__isnull=False)),
                name="ck_vims_safety_soi_inspection_archive_pair",
            ),
        ),
    ]
