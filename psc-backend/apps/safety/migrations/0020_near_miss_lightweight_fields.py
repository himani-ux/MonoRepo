from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):
    dependencies = [
        ("safety", "0019_incident_phase_9_closure"),
    ]

    operations = [
        migrations.AddField(
            model_name="incident",
            name="near_miss_immediate_action",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="incident",
            name="near_miss_mscat_category_id",
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="incident",
            name="near_miss_mscat_subcode_id",
            field=models.CharField(blank=True, max_length=16, null=True),
        ),
        migrations.AddField(
            model_name="incident",
            name="near_miss_severity",
            field=models.CharField(blank=True, max_length=8, null=True),
        ),
        migrations.AddField(
            model_name="incident",
            name="near_miss_shell_tag",
            field=models.CharField(blank=True, max_length=32, null=True),
        ),
        migrations.AddField(
            model_name="incident",
            name="near_miss_suggestion",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddConstraint(
            model_name="incident",
            constraint=models.CheckConstraint(
                condition=Q(near_miss_severity__isnull=True)
                | Q(near_miss_severity__in=("HIGH", "MED", "LOW")),
                name="ck_vims_safety_incident_nm_severity",
            ),
        ),
    ]
