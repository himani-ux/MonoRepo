from __future__ import annotations

from django.db import migrations


def remove_missing_vessel_incident_type(apps, schema_editor):
    MasterSafetyIncidentType = apps.get_model("safety", "MasterSafetyIncidentType")
    MasterSafetyIncidentType.objects.filter(type_code="IMO_MISSING_VESSEL").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("safety", "0048_add_type_of_activity_injury_dropdowns"),
    ]

    operations = [
        migrations.RunPython(remove_missing_vessel_incident_type, migrations.RunPython.noop),
    ]
