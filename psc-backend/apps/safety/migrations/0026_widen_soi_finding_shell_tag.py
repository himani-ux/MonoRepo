from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("safety", "0025_alter_incident_options_alter_incidentfact_options_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="soifinding",
            name="shell_tag",
            field=models.CharField(blank=True, max_length=32, null=True),
        ),
    ]
