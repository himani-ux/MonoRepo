from __future__ import annotations

from django.db import migrations


WEATHER_OPTIONS = [
    ("VISIBILITY", "Good: More than 5 nautical miles"),
    ("VISIBILITY", "Moderate: Between 2 and 5 nautical miles"),
    ("VISIBILITY", "Poor: Between 1000 meters and 2 nautical miles"),
    ("VISIBILITY", "Very Poor: Less than 1000 meters"),
    ("PRECIPITATION", "No Rain / Hail / Snow"),
    ("PRECIPITATION", "Rain Showers"),
    ("PRECIPITATION", "Light Rain"),
    ("PRECIPITATION", "Heavy Rain"),
    ("PRECIPITATION", "Rain Storm"),
    ("PRECIPITATION", "Light Hail"),
    ("PRECIPITATION", "Heavy Hail"),
    ("PRECIPITATION", "Hail Storm"),
    ("PRECIPITATION", "Light Snow"),
    ("PRECIPITATION", "Heavy Snow"),
    ("PRECIPITATION", "Snow Storm"),
    ("SEA_STATE", "0: Calm (Glassy)"),
    ("SEA_STATE", "1: Calm (Rippled)"),
    ("SEA_STATE", "2: Smooth"),
    ("SEA_STATE", "3: Slight"),
    ("SEA_STATE", "4: Moderate"),
    ("SEA_STATE", "5: Rough"),
    ("SEA_STATE", "6: Very Rough"),
    ("SEA_STATE", "7: High"),
    ("SEA_STATE", "8: Very High"),
    ("SEA_STATE", "9: Phenomenal"),
    ("WIND_SCALE", "0: Calm"),
    ("WIND_SCALE", "1: Light Air"),
    ("WIND_SCALE", "2: Light Breeze"),
    ("WIND_SCALE", "3: Gentle Breeze"),
    ("WIND_SCALE", "4: Moderate Breeze"),
    ("WIND_SCALE", "5: Fresh Breeze"),
    ("WIND_SCALE", "6: Strong Breeze"),
    ("WIND_SCALE", "7: High Wind / Moderate Gale / Near Gale"),
    ("WIND_SCALE", "8: Gale / Fresh Gale"),
    ("WIND_SCALE", "9: Strong Gale"),
    ("WIND_SCALE", "10: Storm / Whole Gale"),
    ("WIND_SCALE", "11: Violent Storm"),
    ("WIND_SCALE", "12: Hurricane Force"),
    ("WIND_DIRECTION", "N"),
    ("WIND_DIRECTION", "NE"),
    ("WIND_DIRECTION", "E"),
    ("WIND_DIRECTION", "SE"),
    ("WIND_DIRECTION", "S"),
    ("WIND_DIRECTION", "SW"),
    ("WIND_DIRECTION", "W"),
    ("WIND_DIRECTION", "NW"),
    ("CURRENT_DIRECTION", "N"),
    ("CURRENT_DIRECTION", "NE"),
    ("CURRENT_DIRECTION", "E"),
    ("CURRENT_DIRECTION", "SE"),
    ("CURRENT_DIRECTION", "S"),
    ("CURRENT_DIRECTION", "SW"),
    ("CURRENT_DIRECTION", "W"),
    ("CURRENT_DIRECTION", "NW"),
    ("LIGHTING_SOURCE", "Artificial"),
    ("LIGHTING_SOURCE", "Natural"),
    ("LIGHTING_SOURCE", "Darkness"),
    ("ICE_CONDITION_ONBOARD", "No ice"),
    ("ICE_CONDITION_ONBOARD", "Light"),
    ("ICE_CONDITION_ONBOARD", "Moderate"),
    ("ICE_CONDITION_ONBOARD", "Heavy"),
    ("ICE_CONDITION_AT_SEA", "Open Water"),
    ("ICE_CONDITION_AT_SEA", "Bergy Water"),
    ("ICE_CONDITION_AT_SEA", "Brash (ice fragments < 2 m)"),
    ("ICE_CONDITION_AT_SEA", "New Ice (N)"),
    ("ICE_CONDITION_AT_SEA", "Nilas, Ice Rind"),
    ("ICE_CONDITION_AT_SEA", "Grey Ice (G)"),
    ("ICE_CONDITION_AT_SEA", "Grey-White Ice (GW)"),
    ("ICE_CONDITION_AT_SEA", "Thin First-Year Ice - 1st Stage"),
    ("ICE_CONDITION_AT_SEA", "Thin First-Year Ice - 2nd Stage"),
    ("ICE_CONDITION_AT_SEA", "Thin First-Year Ice (FY)"),
    ("ICE_CONDITION_AT_SEA", "Medium First-Year Ice (MFY)"),
    ("ICE_CONDITION_AT_SEA", "Thick First-Year Ice (TFY)"),
    ("ICE_CONDITION_AT_SEA", "Second-Year Ice (SY)"),
    ("ICE_CONDITION_AT_SEA", "Old / Multi-Year Ice (MY)"),
    ("LIGHT_CONDITION", "Full light"),
    ("LIGHT_CONDITION", "Full dark"),
    ("LIGHT_CONDITION", "Dusk"),
    ("LIGHT_CONDITION", "Dawn"),
]


def seed_weather_options(apps, schema_editor):
    IncidentWeatherOption = apps.get_model("safety", "IncidentWeatherOption")
    for display_order, (field_key, option_label) in enumerate(WEATHER_OPTIONS, start=1):
        IncidentWeatherOption.objects.update_or_create(
            field_key=field_key,
            option_label=option_label,
            defaults={
                "display_order": display_order,
                "active": True,
                "created_by": "migration",
            },
        )


class Migration(migrations.Migration):

    dependencies = [
        ("safety", "0043_incident_weather_condition_fields"),
    ]

    operations = [
        migrations.RunPython(seed_weather_options, migrations.RunPython.noop),
    ]
