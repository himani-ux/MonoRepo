from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("safety", "0036_rename_near_miss_office_comment_states"),
    ]

    operations = [
        migrations.AddField(
            model_name="incident",
            name="office_notified",
            field=models.BooleanField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="incident",
            name="office_notification_mode",
            field=models.CharField(
                blank=True,
                choices=[
                    ("ON_CALL", "On call"),
                    ("WHATSAPP", "On WhatsApp"),
                    ("EMAIL", "On email"),
                ],
                max_length=16,
                null=True,
            ),
        ),
        migrations.AddConstraint(
            model_name="incident",
            constraint=models.CheckConstraint(
                condition=models.Q(office_notification_mode__isnull=True)
                | models.Q(office_notification_mode__in=("ON_CALL", "WHATSAPP", "EMAIL")),
                name="ck_vims_safety_incident_office_notification_mode",
            ),
        ),
    ]
