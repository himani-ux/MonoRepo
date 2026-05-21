from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):
    dependencies = [
        ("safety", "0023_soi_officer_setting"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="soiinspection",
            name="uq_vims_safety_soi_checklist_unique_id",
        ),
        migrations.AlterField(
            model_name="soiinspection",
            name="checklist_unique_id",
            field=models.CharField(blank=True, max_length=32, null=True),
        ),
        migrations.AddConstraint(
            model_name="soiinspection",
            constraint=models.UniqueConstraint(
                fields=("checklist_unique_id",),
                condition=Q(checklist_unique_id__isnull=False),
                name="uq_vims_safety_soi_checklist_unique_id",
            ),
        ),
    ]
