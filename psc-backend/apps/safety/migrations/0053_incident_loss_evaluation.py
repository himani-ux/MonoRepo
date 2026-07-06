from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ("safety", "0052_incident_office_comment"),
    ]

    operations = [
        migrations.CreateModel(
            name="IncidentLossEvaluation",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("consequence", models.CharField(blank=True, choices=[("MINOR", "Minor"), ("APPRECIABLE", "Appreciable"), ("MAJOR", "Major"), ("SEVERE", "Severe"), ("CATASTROPHIC", "Catastrophic")], max_length=32, null=True)),
                ("likelihood", models.CharField(blank=True, choices=[("REMOTE", "Remote"), ("UNLIKELY", "Unlikely"), ("POSSIBLE", "Possible"), ("LIKELY", "Likely"), ("ALMOST_CERTAIN", "Almost certain")], max_length=32, null=True)),
                ("risk_level", models.CharField(blank=True, choices=[("VERY_LOW", "Very low"), ("LOW", "Low"), ("MEDIUM", "Medium"), ("HIGH", "High"), ("VERY_HIGH", "Very high")], max_length=32, null=True)),
                ("name_of_master", models.CharField(blank=True, max_length=128, null=True)),
                ("name_of_chief_engineer", models.CharField(blank=True, max_length=128, null=True)),
                ("repair_type", models.CharField(blank=True, choices=[("TEMPORARY", "Temporary"), ("PERMANENT", "Permanent")], max_length=32, null=True)),
                ("repair_details", models.TextField(blank=True, null=True)),
                ("last_overhaul_maintenance_survey_details", models.TextField(blank=True, null=True)),
                ("safe_working_practice", models.CharField(blank=True, max_length=255, null=True)),
                ("man_hours_worked", models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ("hours_worked_previous_day", models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ("hours_rest_last_96_hours", models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ("delay_to_vessel", models.TextField(blank=True, null=True)),
                ("delay_reason", models.TextField(blank=True, null=True)),
                ("repair_man_hours_lost", models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ("materials_used_repairs_onboard", models.TextField(blank=True, null=True)),
                ("materials_specify_details", models.TextField(blank=True, null=True)),
                ("materials_reason", models.TextField(blank=True, null=True)),
                ("deviation", models.BooleanField(blank=True, null=True)),
                ("off_hire", models.BooleanField(blank=True, null=True)),
                ("injury_man_hours_lost", models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ("injury_reasons", models.TextField(blank=True, null=True)),
                ("repatriation", models.BooleanField(blank=True, null=True)),
                ("hospitalization", models.BooleanField(blank=True, null=True)),
                ("evacuation", models.BooleanField(blank=True, null=True)),
                ("estimated_cost_off_hire", models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ("estimated_cost_delay", models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ("estimated_cost_man_hours", models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ("estimated_cost_deviation", models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ("estimated_cost_materials", models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ("estimated_cost_miscellaneous", models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ("total_estimated_cost", models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ("miscellaneous_expenses_reason", models.TextField(blank=True, null=True)),
                ("cost_medicines_onboard", models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ("cost_doctor_visits", models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ("cost_repatriation", models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ("cost_evacuation", models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ("cost_injury_delay", models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ("cost_injury_man_hours", models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ("cost_injury_deviation", models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ("cost_injury_miscellaneous", models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ("injury_total_estimated_cost", models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ("injury_miscellaneous_expenses_reason", models.TextField(blank=True, null=True)),
                ("schema_version", models.PositiveIntegerField(default=1)),
                ("created_by", models.CharField(max_length=128)),
                ("created_date", models.DateTimeField(auto_now_add=True)),
                ("updated_by", models.CharField(blank=True, max_length=128, null=True)),
                ("updated_date", models.DateTimeField(blank=True, null=True)),
                ("incident", models.OneToOneField(db_column="incident_id", db_constraint=False, on_delete=django.db.models.deletion.DO_NOTHING, related_name="loss_evaluation", to="safety.incident")),
            ],
            options={
                "db_table": "vims_safety_incident_loss_evaluation",
                "ordering": ("incident_id", "id"),
            },
        ),
    ]
