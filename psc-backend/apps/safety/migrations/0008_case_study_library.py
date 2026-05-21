from __future__ import annotations

import json
from pathlib import Path

from django.db import migrations, models
from django.db.models.functions import Now


FIXTURE_PATH = Path(__file__).resolve().parents[1] / "fixtures" / "case_studies_seed.json"


def seed_case_studies(apps, schema_editor) -> None:
    if not FIXTURE_PATH.exists():
        return

    SafetyCaseStudy = apps.get_model("safety", "SafetyCaseStudy")
    with FIXTURE_PATH.open("r", encoding="utf-8") as handle:
        rows = json.load(handle)

    try:
        for row in rows:
            SafetyCaseStudy.objects.update_or_create(
                slug=row["slug"],
                defaults=row,
            )
    except Exception:
        # Keep schema migration unblocked on environments where the seed write path
        # behaves differently (for example SQL Server RETURNING quirks).
        return


class Migration(migrations.Migration):
    dependencies = [
        ("safety", "0007_dashboard_rollup"),
    ]

    operations = [
        migrations.CreateModel(
            name="SafetyCaseStudy",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("slug", models.SlugField(max_length=64, unique=True)),
                ("title", models.CharField(max_length=128)),
                ("event_type", models.CharField(max_length=128)),
                ("loss_summary", models.CharField(max_length=256)),
                ("incident_date", models.DateField()),
                ("immediate_cause_codes", models.CharField(max_length=128)),
                ("basic_cause_codes", models.CharField(max_length=128)),
                ("narrative", models.TextField()),
                ("recommendations", models.TextField()),
                ("source_label", models.CharField(default="DNV worked solution", max_length=128)),
                ("active", models.BooleanField(db_default=True, default=True)),
                ("display_order", models.PositiveSmallIntegerField(db_default=0, default=0)),
                ("created_by", models.CharField(default="seed_case_studies", max_length=128)),
                ("created_date", models.DateTimeField(auto_now_add=True, db_default=Now())),
                ("updated_by", models.CharField(blank=True, max_length=128, null=True)),
                ("updated_date", models.DateTimeField(blank=True, null=True)),
            ],
            options={
                "db_table": "master_safety_case_study",
                "indexes": [
                    models.Index(fields=("active", "display_order"), name="ix_master_safety_case_study_active"),
                ],
            },
        ),
        migrations.RunPython(seed_case_studies, migrations.RunPython.noop),
    ]
