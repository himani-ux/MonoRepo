from __future__ import annotations

from django.db import models

from .base import PublicIdMixin
from .recommendation import Recommendation


class RecommendationVerification(PublicIdMixin):
    recommendation = models.ForeignKey(
        Recommendation,
        on_delete=models.CASCADE,
        related_name="verifications",
        db_column="recommendation_id",
    )
    is_effective = models.BooleanField()
    residual_risk = models.CharField(max_length=32)
    verified_at = models.DateTimeField(auto_now_add=True)
    verified_by = models.CharField(max_length=64)
    notes = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "vims_safety_recommendation_verification"
        ordering = ("verified_at", "id")
        indexes = [
            models.Index(
                fields=("recommendation", "verified_at"),
                name="ix_safe_recv_rec",
            ),
            models.Index(
                fields=("is_effective",),
                name="ix_safe_recv_eff",
            ),
        ]
