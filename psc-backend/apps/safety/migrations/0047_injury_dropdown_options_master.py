from __future__ import annotations

import uuid

from django.db import migrations, models


INJURY_DROPDOWN_OPTIONS = [
    ("NATURE_OF_INJURY", "Amputation"),
    ("NATURE_OF_INJURY", "Asphyxia"),
    ("NATURE_OF_INJURY", "Burn (chemical)"),
    ("NATURE_OF_INJURY", "Burn (heat/cold)"),
    ("NATURE_OF_INJURY", "Concussion / Brain injury"),
    ("NATURE_OF_INJURY", "Crushing / Bruises"),
    ("NATURE_OF_INJURY", "Cuts / Lacerations"),
    ("NATURE_OF_INJURY", "Dislocation"),
    ("NATURE_OF_INJURY", "Drowning"),
    ("NATURE_OF_INJURY", "Effects of chemicals"),
    ("NATURE_OF_INJURY", "Electric shock"),
    ("NATURE_OF_INJURY", "Foreign body (eye)"),
    ("NATURE_OF_INJURY", "Fracture"),
    ("NATURE_OF_INJURY", "Heat stroke"),
    ("NATURE_OF_INJURY", "Hypothermia"),
    ("NATURE_OF_INJURY", "Inflammation"),
    ("NATURE_OF_INJURY", "Internal injury"),
    ("NATURE_OF_INJURY", "Loss of consciousness"),
    ("NATURE_OF_INJURY", "Loss of sight"),
    ("NATURE_OF_INJURY", "Scratches / Abrasions"),
    ("NATURE_OF_INJURY", "Sprains and strains"),
    ("NATURE_OF_INJURY", "Other (specify)"),
    ("SOURCE_OF_INJURY", "Contact with chemicals"),
    ("SOURCE_OF_INJURY", "Contact with heat"),
    ("SOURCE_OF_INJURY", "Contact with cold"),
    ("SOURCE_OF_INJURY", "Pressure release"),
    ("SOURCE_OF_INJURY", "Electricity"),
    ("SOURCE_OF_INJURY", "Slip, trip, fall (same level)"),
    ("SOURCE_OF_INJURY", "Fall from height (>1.8m)"),
    ("SOURCE_OF_INJURY", "Fire, explosion"),
    ("SOURCE_OF_INJURY", "Hand tools"),
    ("SOURCE_OF_INJURY", "Immersion in water"),
    ("SOURCE_OF_INJURY", "Radiation"),
    ("SOURCE_OF_INJURY", "Struck by / against"),
    ("SOURCE_OF_INJURY", "Manual handling"),
    ("SOURCE_OF_INJURY", "Mechanical lifting"),
    ("SOURCE_OF_INJURY", "Pollution"),
    ("SOURCE_OF_INJURY", "Falling object"),
    ("SOURCE_OF_INJURY", "Cut by sharp instruments"),
    ("SOURCE_OF_INJURY", "Inhalation of toxic or corrosive substances"),
    ("SOURCE_OF_INJURY", "Lack of O2"),
    ("SOURCE_OF_INJURY", "Caught in / on / in between objects"),
    ("SOURCE_OF_INJURY", "Over exposure to cold"),
    ("SOURCE_OF_INJURY", "Over exposure to heat"),
    ("SOURCE_OF_INJURY", "Other (specify)"),
    ("AFFECTED_BODY_AREA", "Abdomen"),
    ("AFFECTED_BODY_AREA", "Arm(s)"),
    ("AFFECTED_BODY_AREA", "Back"),
    ("AFFECTED_BODY_AREA", "Chest"),
    ("AFFECTED_BODY_AREA", "Eye(s)"),
    ("AFFECTED_BODY_AREA", "Feet"),
    ("AFFECTED_BODY_AREA", "Fingers"),
    ("AFFECTED_BODY_AREA", "Hand(s)"),
    ("AFFECTED_BODY_AREA", "Head"),
    ("AFFECTED_BODY_AREA", "Internal"),
    ("AFFECTED_BODY_AREA", "Leg(s)"),
    ("AFFECTED_BODY_AREA", "Neck"),
    ("AFFECTED_BODY_AREA", "Toes"),
    ("AFFECTED_BODY_AREA", "Other (specify)"),
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
        ("safety", "0046_enhance_injury_record_for_crew"),
    ]

    operations = [
        migrations.CreateModel(
            name="InjuryDropdownOption",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                (
                    "field_key",
                    models.CharField(
                        choices=[
                            ("NATURE_OF_INJURY", "Nature of Injury"),
                            ("SOURCE_OF_INJURY", "Source of Injury"),
                            ("AFFECTED_BODY_AREA", "Affected Areas of the Body"),
                        ],
                        db_index=True,
                        max_length=32,
                    ),
                ),
                ("option_label", models.CharField(max_length=255)),
                ("display_order", models.PositiveSmallIntegerField(default=0)),
                ("active", models.BooleanField(default=True)),
                ("created_by", models.CharField(default="system", max_length=128)),
                ("created_date", models.DateTimeField(auto_now_add=True)),
                ("updated_by", models.CharField(blank=True, max_length=128, null=True)),
                ("updated_date", models.DateTimeField(blank=True, null=True)),
            ],
            options={
                "db_table": "vims_safety_injury_dropdown_option",
                "ordering": ("field_key", "display_order", "option_label"),
            },
        ),
        migrations.AddConstraint(
            model_name="injurydropdownoption",
            constraint=models.UniqueConstraint(
                fields=("field_key", "option_label"),
                name="uq_injury_dropdown_field_label",
            ),
        ),
        migrations.AddIndex(
            model_name="injurydropdownoption",
            index=models.Index(
                fields=("active", "field_key", "display_order"),
                name="ix_injury_dropdown_lookup",
            ),
        ),
        migrations.RunPython(seed_injury_dropdown_options, migrations.RunPython.noop),
    ]
