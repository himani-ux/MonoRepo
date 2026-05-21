from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("safety", "0027_near_miss_review_states"),
    ]

    operations = [
        migrations.AddField(
            model_name="incidentphaselog",
            name="signature_valid",
            field=models.BooleanField(default=True),
        ),
    ]
