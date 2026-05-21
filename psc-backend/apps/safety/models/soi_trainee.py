from __future__ import annotations

from django.db import models
from django.db.models import Q

from .base import PublicIdMixin


class SOITrainee(PublicIdMixin):
    inspection_id = models.BigIntegerField()
    crew_id = models.CharField(max_length=64)
    trainee_slot = models.PositiveSmallIntegerField()
    schema_version = models.IntegerField(default=1, db_default=1)

    class Meta:
        db_table = "vims_safety_soi_trainee"
        ordering = ("inspection_id", "trainee_slot", "id")
        constraints = [
            models.UniqueConstraint(
                fields=("inspection_id", "crew_id"),
                name="uq_vims_safety_soi_trainee_crew",
            ),
            models.UniqueConstraint(
                fields=("inspection_id", "trainee_slot"),
                name="uq_vims_safety_soi_trainee_slot",
            ),
            models.CheckConstraint(
                condition=Q(trainee_slot__gte=1) & Q(trainee_slot__lte=3),
                name="ck_vims_safety_soi_trainee_slot",
            ),
        ]
        indexes = [
            models.Index(fields=("crew_id",), name="ix_safe_soit_crew"),
        ]
