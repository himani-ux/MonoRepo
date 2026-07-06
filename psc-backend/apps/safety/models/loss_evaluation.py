from __future__ import annotations

from django.db import models

from .base import PublicIdMixin


class IncidentLossEvaluation(PublicIdMixin):
    class Consequence(models.TextChoices):
        MINOR = "MINOR", "Minor"
        APPRECIABLE = "APPRECIABLE", "Appreciable"
        MAJOR = "MAJOR", "Major"
        SEVERE = "SEVERE", "Severe"
        CATASTROPHIC = "CATASTROPHIC", "Catastrophic"

    class Likelihood(models.TextChoices):
        REMOTE = "REMOTE", "Remote"
        UNLIKELY = "UNLIKELY", "Unlikely"
        POSSIBLE = "POSSIBLE", "Possible"
        LIKELY = "LIKELY", "Likely"
        ALMOST_CERTAIN = "ALMOST_CERTAIN", "Almost certain"

    class RiskLevel(models.TextChoices):
        VERY_LOW = "VERY_LOW", "Very low"
        LOW = "LOW", "Low"
        MEDIUM = "MEDIUM", "Medium"
        HIGH = "HIGH", "High"
        VERY_HIGH = "VERY_HIGH", "Very high"

    class RepairType(models.TextChoices):
        TEMPORARY = "TEMPORARY", "Temporary"
        PERMANENT = "PERMANENT", "Permanent"

    incident = models.OneToOneField(
        "safety.Incident",
        db_column="incident_id",
        db_constraint=False,
        on_delete=models.DO_NOTHING,
        related_name="loss_evaluation",
    )

    consequence = models.CharField(max_length=32, choices=Consequence.choices, null=True, blank=True)
    likelihood = models.CharField(max_length=32, choices=Likelihood.choices, null=True, blank=True)
    risk_level = models.CharField(max_length=32, choices=RiskLevel.choices, null=True, blank=True)

    name_of_master = models.CharField(max_length=128, null=True, blank=True)
    name_of_chief_engineer = models.CharField(max_length=128, null=True, blank=True)

    repair_type = models.CharField(max_length=32, choices=RepairType.choices, null=True, blank=True)
    repair_details = models.TextField(null=True, blank=True)
    last_overhaul_maintenance_survey_details = models.TextField(null=True, blank=True)

    safe_working_practice = models.CharField(max_length=255, null=True, blank=True)
    man_hours_worked = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    hours_worked_previous_day = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    hours_rest_last_96_hours = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    delay_to_vessel = models.TextField(null=True, blank=True)
    delay_reason = models.TextField(null=True, blank=True)
    repair_man_hours_lost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    materials_used_repairs_onboard = models.TextField(null=True, blank=True)
    materials_specify_details = models.TextField(null=True, blank=True)
    materials_reason = models.TextField(null=True, blank=True)
    deviation = models.BooleanField(null=True, blank=True)
    off_hire = models.BooleanField(null=True, blank=True)

    injury_man_hours_lost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    injury_reasons = models.TextField(null=True, blank=True)
    repatriation = models.BooleanField(null=True, blank=True)
    hospitalization = models.BooleanField(null=True, blank=True)
    evacuation = models.BooleanField(null=True, blank=True)

    estimated_cost_off_hire = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    estimated_cost_delay = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    estimated_cost_man_hours = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    estimated_cost_deviation = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    estimated_cost_materials = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    estimated_cost_miscellaneous = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    total_estimated_cost = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    miscellaneous_expenses_reason = models.TextField(null=True, blank=True)

    cost_medicines_onboard = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    cost_doctor_visits = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    cost_repatriation = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    cost_evacuation = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    cost_injury_delay = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    cost_injury_man_hours = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    cost_injury_deviation = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    cost_injury_miscellaneous = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    injury_total_estimated_cost = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    injury_miscellaneous_expenses_reason = models.TextField(null=True, blank=True)

    schema_version = models.PositiveIntegerField(default=1)
    created_by = models.CharField(max_length=128)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_by = models.CharField(max_length=128, null=True, blank=True)
    updated_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "vims_safety_incident_loss_evaluation"
        ordering = ("incident_id", "id")
