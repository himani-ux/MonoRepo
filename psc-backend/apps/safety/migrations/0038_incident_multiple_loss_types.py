from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("safety", "0037_incident_office_notification_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="incident",
            name="loss_type_secondary_id",
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="incident",
            name="loss_type_tertiary_id",
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="incident",
            name="loss_type_other",
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
    ]
