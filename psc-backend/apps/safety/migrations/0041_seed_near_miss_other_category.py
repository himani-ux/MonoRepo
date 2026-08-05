from __future__ import annotations

from django.db import migrations


def seed_other_category(apps, schema_editor):
    NearMissCategory = apps.get_model("safety", "NearMissCategory")
    NearMissCategory.objects.update_or_create(
        category_name="Other",
        defaults={
            "display_order": 16,
            "active": True,
            "created_by": "migration",
        },
    )


class Migration(migrations.Migration):

    dependencies = [
        ("safety", "0040_near_miss_categories_master"),
    ]

    operations = [
        migrations.RunPython(seed_other_category, migrations.RunPython.noop),
    ]
