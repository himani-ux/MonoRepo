from __future__ import annotations

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("safety", "0006_add_purchase_fk_constraint"),
    ]

    operations = [
        migrations.CreateModel(
            name="SafetyDashboardRollup",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("scope_type", models.CharField(choices=[("FLEET", "Fleet"), ("VESSEL", "Vessel")], default="FLEET", max_length=16)),
                ("scope_id", models.CharField(blank=True, default="", max_length=64)),
                ("period_code", models.CharField(choices=[("90D", "90 days"), ("12M", "12 months"), ("3Y", "3 years")], default="3Y", max_length=8)),
                ("window_start", models.DateField()),
                ("window_end", models.DateField()),
                ("composite_score", models.PositiveSmallIntegerField()),
                ("score_status", models.CharField(max_length=8)),
                ("open_incident_count", models.PositiveIntegerField(default=0)),
                ("open_near_miss_count", models.PositiveIntegerField(default=0)),
                ("open_finding_count", models.PositiveIntegerField(default=0)),
                ("overdue_ca_count", models.PositiveIntegerField(default=0)),
                ("soi_compliance_percent", models.PositiveSmallIntegerField(blank=True, null=True)),
                ("component_scores", models.JSONField(blank=True, default=dict)),
                ("calculated_at", models.DateTimeField()),
                ("schema_version", models.PositiveIntegerField(default=1)),
                ("is_deleted", models.BooleanField(default=False)),
                ("created_by", models.CharField(default="dashboard_rollup", max_length=128)),
                ("created_date", models.DateTimeField(auto_now_add=True)),
                ("updated_by", models.CharField(blank=True, default="dashboard_rollup", max_length=128, null=True)),
                ("updated_date", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "vims_safety_dashboard_rollup",
            },
        ),
        migrations.AddConstraint(
            model_name="safetydashboardrollup",
            constraint=models.UniqueConstraint(
                fields=("scope_type", "scope_id", "period_code"),
                name="uq_vims_safety_dashboard_rollup_scope_period",
            ),
        ),
        migrations.AddIndex(
            model_name="safetydashboardrollup",
            index=models.Index(fields=("scope_type", "scope_id"), name="ix_vims_safety_dashboard_rollup_scope"),
        ),
        migrations.AddIndex(
            model_name="safetydashboardrollup",
            index=models.Index(fields=("period_code", "window_end"), name="ix_vims_safety_dashboard_rollup_period"),
        ),
    ]
