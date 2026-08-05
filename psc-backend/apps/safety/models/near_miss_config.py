from __future__ import annotations

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from .base import PublicIdMixin


class NearMissCategory(PublicIdMixin):
    category_name = models.CharField(max_length=64, unique=True)
    display_order = models.PositiveSmallIntegerField(default=0)
    active = models.BooleanField(default=True)
    created_by = models.CharField(max_length=128, default="system")
    created_date = models.DateTimeField(auto_now_add=True)
    updated_by = models.CharField(max_length=128, null=True, blank=True)
    updated_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "vims_safety_NM_categories"
        ordering = ("display_order", "category_name")
        indexes = [
            models.Index(fields=("active", "display_order"), name="ix_nm_category_active_order"),
        ]


class NearMissGuidancePrompt(PublicIdMixin):
    category_tag = models.CharField(max_length=32, null=True, blank=True, db_index=True)
    incident_type_id = models.IntegerField(null=True, blank=True, db_index=True)
    prompt_text = models.TextField()
    display_order = models.PositiveSmallIntegerField(default=0)
    active = models.BooleanField(default=True)
    created_by = models.CharField(max_length=128, default="system")
    created_date = models.DateTimeField(auto_now_add=True)
    updated_by = models.CharField(max_length=128, null=True, blank=True)
    updated_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "vims_safety_near_miss_guidance_prompt"
        ordering = ("display_order", "category_tag", "incident_type_id")
        indexes = [
            models.Index(fields=("active", "category_tag"), name="ix_nm_guidance_category"),
            models.Index(fields=("active", "incident_type_id"), name="ix_nm_guidance_type"),
        ]


class NearMissKpiTarget(PublicIdMixin):
    vessel_id = models.CharField(max_length=64, db_index=True)
    year = models.PositiveSmallIntegerField(validators=[MinValueValidator(2000), MaxValueValidator(2100)])
    month = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(12)])
    target_count = models.PositiveSmallIntegerField(default=0)
    active = models.BooleanField(default=True)
    created_by = models.CharField(max_length=128, default="system")
    created_date = models.DateTimeField(auto_now_add=True)
    updated_by = models.CharField(max_length=128, null=True, blank=True)
    updated_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "vims_safety_near_miss_kpi_target"
        ordering = ("vessel_id", "year", "month")
        constraints = [
            models.UniqueConstraint(
                fields=("vessel_id", "year", "month"),
                name="uq_vims_safety_nm_kpi_target_period",
            ),
        ]
        indexes = [
            models.Index(fields=("vessel_id", "year", "month"), name="ix_nm_kpi_target_period"),
        ]


class NearMissCauseOption(PublicIdMixin):
    class Factor(models.TextChoices):
        HUMAN = "HUMAN", "Human Factors"
        VESSEL = "VESSEL", "Vessel Factors"
        MANAGEMENT = "MANAGEMENT", "Management Factors"
        OTHER = "OTHER", "Other Factors"

    class CauseStage(models.TextChoices):
        IMMEDIATE = "IMMEDIATE", "Immediate Cause"
        ROOT = "ROOT", "Root Cause"

    factor = models.CharField(max_length=16, choices=Factor.choices, db_index=True)
    cause_stage = models.CharField(max_length=16, choices=CauseStage.choices, db_index=True)
    option_code = models.CharField(max_length=64, db_index=True)
    option_text = models.TextField()
    display_order = models.PositiveSmallIntegerField(default=0)
    active = models.BooleanField(default=True)
    created_by = models.CharField(max_length=128, default="system")
    created_date = models.DateTimeField(auto_now_add=True)
    updated_by = models.CharField(max_length=128, null=True, blank=True)
    updated_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "vims_safety_near_miss_cause_option"
        ordering = ("factor", "cause_stage", "display_order", "option_text")
        constraints = [
            models.UniqueConstraint(
                fields=("factor", "cause_stage", "option_code"),
                name="uq_nm_cause_option_factor_stage_code",
            ),
        ]
        indexes = [
            models.Index(fields=("active", "factor", "cause_stage"), name="ix_nm_cause_option_lookup"),
        ]
