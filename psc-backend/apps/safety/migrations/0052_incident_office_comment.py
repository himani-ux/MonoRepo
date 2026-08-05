from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("safety", "0051_replace_incident_type_master_list"),
    ]

    operations = [
        migrations.AddField(
            model_name="incident",
            name="office_comment",
            field=models.TextField(blank=True, null=True),
        ),
    ]
