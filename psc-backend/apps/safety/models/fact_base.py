from __future__ import annotations

from django.db import models

from .base import PublicIdMixin
from .incident import Incident


class IncidentFact(PublicIdMixin):
    class Confidence(models.TextChoices):
        LOW = "LOW", "Low"
        MEDIUM = "MEDIUM", "Medium"
        HIGH = "HIGH", "High"

    incident = models.ForeignKey(Incident, on_delete=models.CASCADE, related_name="facts")
    sequence_index = models.PositiveIntegerField(default=1)
    fact_text = models.TextField()
    fact_timestamp = models.DateTimeField(blank=True, null=True)
    source_evidence_id = models.UUIDField()
    confidence = models.CharField(
        max_length=16,
        choices=Confidence.choices,
        default=Confidence.MEDIUM,
    )
    contradicts_fact = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="contradicted_by",
    )
    hindsight_guard_triggered = models.BooleanField(default=False)
    hindsight_override_reason = models.TextField(blank=True, null=True)
    schema_version = models.PositiveIntegerField(default=1)
    created_by = models.CharField(max_length=128)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_by = models.CharField(max_length=128, blank=True, null=True)
    updated_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "vims_safety_fact"
        ordering = ("sequence_index", "id")
        constraints = [
            models.UniqueConstraint(
                fields=("incident", "sequence_index"),
                name="uq_vims_safety_fact_sequence",
            ),
        ]
        indexes = [
            models.Index(fields=("incident", "sequence_index"), name="ix_vims_safety_fact_incident"),
            models.Index(
                fields=("contradicts_fact",),
                name="ix_safe_fact_contra",
            ),
        ]
