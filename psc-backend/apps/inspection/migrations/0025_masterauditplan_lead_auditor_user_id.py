from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("inspection", "0024_audit_car_status_choices"),
    ]

    operations = [
        migrations.AddField(
            model_name="masterauditplan",
            name="lead_auditor_user_id",
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
