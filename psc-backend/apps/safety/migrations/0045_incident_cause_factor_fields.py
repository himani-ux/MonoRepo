from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("safety", "0044_seed_incident_weather_options"),
    ]

    operations = [
        migrations.AddField(
            model_name="incidentcausetag",
            name="cause_factor",
            field=models.CharField(blank=True, max_length=16, null=True),
        ),
        migrations.AddField(
            model_name="incidentcausetag",
            name="cause_option_id",
            field=models.UUIDField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="incidentcausetag",
            name="cause_option_text",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="incidentcausetag",
            name="cause_other_text",
            field=models.TextField(blank=True, default=""),
        ),
    ]
