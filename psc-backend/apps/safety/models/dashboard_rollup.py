from __future__ import annotations

from django.db import models

from .base import PublicIdMixin


class SafetyDashboardRollup(PublicIdMixin):
    class ScopeType(models.TextChoices):
        FLEET = "FLEET", "Fleet"
        VESSEL = "VESSEL", "Vessel"

    class PeriodCode(models.TextChoices):
        DAYS_90 = "90D", "90 days"
        MONTHS_12 = "12M", "12 months"
        YEARS_3 = "3Y", "3 years"

    scope_type = models.CharField(max_length=16, choices=ScopeType.choices, default=ScopeType.FLEET)
    scope_id = models.CharField(max_length=64, blank=True, default="")
    period_code = models.CharField(max_length=8, choices=PeriodCode.choices, default=PeriodCode.YEARS_3)
    window_start = models.DateField()
    window_end = models.DateField()
    composite_score = models.PositiveSmallIntegerField()
    score_status = models.CharField(max_length=8)
    open_incident_count = models.PositiveIntegerField(default=0)
    open_near_miss_count = models.PositiveIntegerField(default=0)
    open_finding_count = models.PositiveIntegerField(default=0)
    overdue_ca_count = models.PositiveIntegerField(default=0)
    soi_compliance_percent = models.PositiveSmallIntegerField(null=True, blank=True)
    component_scores = models.JSONField(default=dict, blank=True)
    calculated_at = models.DateTimeField()
    schema_version = models.PositiveIntegerField(default=1)
    is_deleted = models.BooleanField(default=False)
    created_by = models.CharField(max_length=128, default="dashboard_rollup")
    created_date = models.DateTimeField(auto_now_add=True)
    updated_by = models.CharField(max_length=128, null=True, blank=True, default="dashboard_rollup")
    updated_date = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "vims_safety_dashboard_rollup"
        constraints = [
            models.UniqueConstraint(
                fields=("scope_type", "scope_id", "period_code"),
                name="uq_vims_safety_dashboard_rollup_scope_period",
            ),
        ]
        indexes = [
            models.Index(fields=("scope_type", "scope_id"), name="ix_safe_dash_scope"),
            models.Index(fields=("period_code", "window_end"), name="ix_safe_dash_period"),
        ]
