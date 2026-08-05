from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("safety", "0049_remove_missing_vessel_incident_type"),
    ]

    operations = [
        migrations.AddField(
            model_name="incident",
            name="shore_assistance_required",
            field=models.BooleanField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="incident",
            name="vessel_location",
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.AddField(
            model_name="incident",
            name="onboard_location",
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.AddField(
            model_name="incident",
            name="last_port",
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.AddField(
            model_name="incident",
            name="departure_date",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="incident",
            name="vessel_condition",
            field=models.CharField(
                blank=True,
                choices=[("LOADED", "Loaded"), ("BALLAST", "Ballast")],
                max_length=16,
                null=True,
            ),
        ),
    ]
