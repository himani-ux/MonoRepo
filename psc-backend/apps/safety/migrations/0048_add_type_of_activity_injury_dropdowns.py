from __future__ import annotations

import uuid

from django.db import migrations, models


INJURY_DROPDOWN_OPTIONS = [
    ("TYPE_OF_ACTIVITY", "Anchoring"),
    ("TYPE_OF_ACTIVITY", "Ballast operations"),
    ("TYPE_OF_ACTIVITY", "Bunkering"),
    ("TYPE_OF_ACTIVITY", "Cargo operations"),
    ("TYPE_OF_ACTIVITY", "Cold work"),
    ("TYPE_OF_ACTIVITY", "Derusting"),
    ("TYPE_OF_ACTIVITY", "Drills & Exercises"),
    ("TYPE_OF_ACTIVITY", "Enclosed space entry"),
    ("TYPE_OF_ACTIVITY", "Handling of chemicals"),
    ("TYPE_OF_ACTIVITY", "Helicopter operations"),
    ("TYPE_OF_ACTIVITY", "Hot work"),
    ("TYPE_OF_ACTIVITY", "In Dry Dock"),
    ("TYPE_OF_ACTIVITY", "Lifting operations (mechanical)"),
    ("TYPE_OF_ACTIVITY", "Manual handling"),
    ("TYPE_OF_ACTIVITY", "Mooring / Unmooring – tugs used"),
    ("TYPE_OF_ACTIVITY", "Mooring / Unmooring – no tugs"),
    ("TYPE_OF_ACTIVITY", "Navigation – Pilot onboard"),
    ("TYPE_OF_ACTIVITY", "Navigation – without Pilot"),
    ("TYPE_OF_ACTIVITY", "Overhauling machinery"),
    ("TYPE_OF_ACTIVITY", "Painting"),
    ("TYPE_OF_ACTIVITY", "STS operations"),
    ("TYPE_OF_ACTIVITY", "Transfer of personnel by ladder"),
    ("TYPE_OF_ACTIVITY", "Transfer of personnel by basket"),
    ("TYPE_OF_ACTIVITY", "Use of power tools"),
    ("TYPE_OF_ACTIVITY", "Use of stairs"),
    ("TYPE_OF_ACTIVITY", "Walking on same level"),
    ("TYPE_OF_ACTIVITY", "Work aloft"),
    ("TYPE_OF_ACTIVITY", "Work in pressurised piping or equipment"),
    ("TYPE_OF_ACTIVITY", "Work outboard"),
    ("TYPE_OF_ACTIVITY", "Working in electrical equipment"),
    ("TYPE_OF_ACTIVITY", "Working in galley"),
    ("TYPE_OF_ACTIVITY", "Others(Specify)"),
]


def seed_injury_dropdown_options(apps, schema_editor):
    InjuryDropdownOption = apps.get_model("safety", "InjuryDropdownOption")
    order_by_field: dict[str, int] = {}
    for field_key, option_label in INJURY_DROPDOWN_OPTIONS:
        order_by_field[field_key] = order_by_field.get(field_key, 0) + 1
        InjuryDropdownOption.objects.update_or_create(
            field_key=field_key,
            option_label=option_label,
            defaults={
                "display_order": order_by_field[field_key],
                "active": True,
                "created_by": "migration",
            },
        )


class Migration(migrations.Migration):
    dependencies = [
        ("safety", "0047_injury_dropdown_options_master"),
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
                ],
                db_index=True,
                max_length=32,
            ),
        ),
        migrations.RunPython(seed_injury_dropdown_options, migrations.RunPython.noop),
    ]
