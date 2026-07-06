from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("safety", "0053_incident_loss_evaluation"),
    ]

    operations = [
        migrations.AlterField(
            model_name="injurydropdownoption",
            name="field_key",
            field=models.CharField(
                choices=[
                    ("NATURE_OF_INJURY", "Nature of Injury"),
                    ("SOURCE_OF_INJURY", "Source of Injury"),
                    ("AFFECTED_BODY_AREA", "Affected Areas of the Body"),
                    ("TYPE_OF_ACTIVITY", "Type of Activity"),
                    ("SAFE_WORKING_PRACTICE", "Code of Safe Working Practices"),
                ],
                db_index=True,
                max_length=32,
            ),
        ),
    ]
