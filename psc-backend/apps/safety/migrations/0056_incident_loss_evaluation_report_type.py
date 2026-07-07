from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("safety", "0055_seed_safe_working_practice_options"),
    ]

    operations = [
        migrations.AddField(
            model_name="incidentlossevaluation",
            name="report_type",
            field=models.CharField(
                blank=True,
                choices=[("INCIDENT", "Incident Report"), ("INJURY", "Injury Report")],
                max_length=16,
                null=True,
            ),
        ),
    ]
