from __future__ import annotations

import uuid

from django.db import migrations, models


NEAR_MISS_CATEGORIES = [
    "PPE",
    "Fire Safety",
    "LSA",
    "Safety Awareness",
    "Work Routines",
    "Maintenance",
    "Machinery",
    "Housekeeping",
    "Seamanship",
    "Pollution",
    "Communication/Instructions",
    "Navigation",
    "Leadership",
    "Structural",
    "Cargo Operation",
    "Other",
]


def seed_near_miss_categories(apps, schema_editor):
    NearMissCategory = apps.get_model("safety", "NearMissCategory")
    for display_order, category_name in enumerate(NEAR_MISS_CATEGORIES, start=1):
        NearMissCategory.objects.update_or_create(
            category_name=category_name,
            defaults={
                "display_order": display_order,
                "active": True,
                "created_by": "migration",
            },
        )


class Migration(migrations.Migration):

    dependencies = [
        ("safety", "0039_near_miss_factor_causes"),
    ]

    operations = [
        migrations.CreateModel(
            name="NearMissCategory",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("category_name", models.CharField(max_length=64, unique=True)),
                ("display_order", models.PositiveSmallIntegerField(default=0)),
                ("active", models.BooleanField(default=True)),
                ("created_by", models.CharField(default="system", max_length=128)),
                ("created_date", models.DateTimeField(auto_now_add=True)),
                ("updated_by", models.CharField(blank=True, max_length=128, null=True)),
                ("updated_date", models.DateTimeField(blank=True, null=True)),
            ],
            options={
                "db_table": "vims_safety_NM_categories",
                "ordering": ("display_order", "category_name"),
                "indexes": [models.Index(fields=["active", "display_order"], name="ix_nm_category_active_order")],
            },
        ),
        migrations.RunPython(seed_near_miss_categories, migrations.RunPython.noop),
    ]
