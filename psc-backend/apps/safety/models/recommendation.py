from __future__ import annotations

from django.db import models

from .base import PublicIdMixin
from .incident import Incident


class Recommendation(PublicIdMixin):
    class Tier(models.TextChoices):
        CORRECTIVE = "CORRECTIVE", "Corrective"
        PREVENTIVE = "PREVENTIVE", "Preventive"
        LESSONS_LEARNT = "LESSONS_LEARNT", "Lessons Learnt"

    class LikelihoodReduction(models.TextChoices):
        LOW = "LOW", "Low"
        MED = "MED", "Medium"
        HIGH = "HIGH", "High"
        QUANTIFIED = "QUANTIFIED", "Quantified"

    incident = models.ForeignKey(
        Incident,
        on_delete=models.CASCADE,
        related_name="recommendations",
        db_column="incident_id",
    )
    tier = models.CharField(max_length=16, choices=Tier.choices)
    theme_code = models.CharField(max_length=32, null=True, blank=True)
    title = models.CharField(max_length=256)
    description = models.TextField()
    rationale = models.TextField(null=True, blank=True)
    estimated_effort = models.TextField(null=True, blank=True)
    estimated_likelihood_reduction = models.CharField(
        max_length=24,
        choices=LikelihoodReduction.choices,
        null=True,
        blank=True,
    )
    residual_risk_statement = models.TextField(null=True, blank=True)
    alarp_attested = models.BooleanField(default=False)
    tolerable_failure_filter = models.BooleanField(default=False)
    linked_ca_ids = models.TextField(null=True, blank=True)
    schema_version = models.PositiveIntegerField(default=1)
    is_deleted = models.BooleanField(default=False)
    created_by = models.CharField(max_length=128)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_by = models.CharField(max_length=128, null=True, blank=True)
    updated_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "vims_safety_recommendation"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(tier__in=["CORRECTIVE", "PREVENTIVE", "LESSONS_LEARNT"]),
                name="ck_vims_safety_recommendation_tier",
            ),
        ]
        indexes = [
            models.Index(fields=("incident", "tier"), name="ix_safe_rec_inc"),
            models.Index(
                fields=("theme_code",),
                name="ix_safe_rec_theme",
                condition=models.Q(theme_code__isnull=False),
            ),
            models.Index(fields=("alarp_attested",), name="ix_safe_rec_alarp"),
        ]


class CorrectiveAction(PublicIdMixin):
    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        PENDING_VERIFY = "PENDING_VERIFY", "Pending Verify"
        CLOSED = "CLOSED", "Closed"
        REOPENED = "REOPENED", "Reopened"

    source_table = models.CharField(max_length=64)
    source_id = models.UUIDField()
    recommendation = models.ForeignKey(
        Recommendation,
        on_delete=models.SET_NULL,
        related_name="corrective_actions",
        db_column="recommendation_id",
        null=True,
        blank=True,
    )
    title = models.CharField(max_length=256)
    description = models.TextField()
    assigned_crew_id = models.CharField(max_length=64, null=True, blank=True)
    assigned_office_user_id = models.CharField(max_length=64, null=True, blank=True)
    verifier_user_id = models.CharField(max_length=64, null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=24, choices=Status.choices)
    purchase_req_id = models.BigIntegerField(null=True, blank=True)
    physical_verification_done = models.BooleanField(default=False)
    physical_verification_at = models.DateTimeField(null=True, blank=True)
    physical_verification_by = models.CharField(max_length=64, null=True, blank=True)
    physical_verification_note = models.TextField(null=True, blank=True)
    aging_bucket = models.CharField(max_length=16, null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    closed_by = models.CharField(max_length=64, null=True, blank=True)
    schema_version = models.PositiveIntegerField(default=1)
    is_deleted = models.BooleanField(default=False)
    created_by = models.CharField(max_length=128)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_by = models.CharField(max_length=128, null=True, blank=True)
    updated_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "vims_safety_corrective_action"
        indexes = [
            models.Index(fields=("source_table", "source_id"), name="ix_safe_ca_source"),
            models.Index(
                fields=("status",),
                name="ix_safe_ca_status",
                condition=models.Q(is_deleted=False),
            ),
            models.Index(fields=("due_date", "status"), name="ix_safe_ca_due"),
            models.Index(
                fields=("purchase_req_id",),
                name="ix_safe_ca_purchase",
                condition=models.Q(purchase_req_id__isnull=False),
            ),
            models.Index(fields=("aging_bucket",), name="ix_safe_ca_aging"),
        ]
