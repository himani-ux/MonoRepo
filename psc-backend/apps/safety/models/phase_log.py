from __future__ import annotations

from django.db import IntegrityError, models
from django.db.models import Q

from .base import PublicIdMixin

MAX_ACTOR_ID_LENGTH = 64
MAX_ACTOR_ROLE_CODE_LENGTH = 16
MAX_DEVICE_FINGERPRINT_LENGTH = 256


def _fit_char(value, max_length: int):
    if value in (None, ""):
        return value
    return str(value).strip()[:max_length]


class IncidentPhaseLog(PublicIdMixin):
    class PhaseNumber(models.IntegerChoices):
        PHASE_1 = 1, "Phase 1"
        PHASE_2 = 2, "Phase 2"
        PHASE_3 = 3, "Phase 3"
        PHASE_4 = 4, "Phase 4"
        PHASE_5 = 5, "Phase 5"
        PHASE_6 = 6, "Phase 6"
        PHASE_7 = 7, "Phase 7"
        PHASE_8 = 8, "Phase 8"
        PHASE_9 = 9, "Phase 9"

    class TransitionType(models.TextChoices):
        FORWARD = "FORWARD", "Forward"
        LOOP_BACK = "LOOP_BACK", "Loop Back"
        REWORK = "REWORK", "Rework"
        REOPEN = "REOPEN", "Reopen"
        CLOSE = "CLOSE", "Close"

    incident = models.ForeignKey(
        "safety.Incident",
        db_column="incident_id",
        db_constraint=False,
        on_delete=models.DO_NOTHING,
        related_name="phase_logs",
    )
    phase_from = models.PositiveSmallIntegerField(
        choices=PhaseNumber.choices,
        null=True,
        blank=True,
    )
    phase_to = models.PositiveSmallIntegerField(choices=PhaseNumber.choices)
    transition_type = models.CharField(max_length=24, choices=TransitionType.choices)
    loop_back_reason = models.TextField(null=True, blank=True)
    actor_user_id = models.CharField(max_length=64)
    actor_role_code = models.CharField(max_length=16)
    occurred_at = models.DateTimeField(auto_now_add=True)
    device_fingerprint = models.CharField(max_length=256, null=True, blank=True)
    signature_valid = models.BooleanField(default=True)
    schema_version = models.PositiveIntegerField(default=1)

    class Meta:
        db_table = "vims_safety_incident_phase_log"
        ordering = ("occurred_at", "id")
        constraints = [
            models.CheckConstraint(
                condition=Q(
                    transition_type__in=[
                        "FORWARD",
                        "LOOP_BACK",
                        "REWORK",
                        "REOPEN",
                        "CLOSE",
                    ]
                ),
                name="ck_vims_safety_incident_phase_log_transition",
            ),
            models.CheckConstraint(
                condition=~Q(transition_type="LOOP_BACK")
                | (Q(loop_back_reason__isnull=False) & ~Q(loop_back_reason="")),
                name="ck_vims_safety_incident_phase_log_loop_back_reason",
            ),
            models.CheckConstraint(
                condition=Q(phase_from__isnull=True)
                | (Q(phase_from__gte=1) & Q(phase_from__lte=9)),
                name="ck_vims_safety_incident_phase_log_phase_from_range",
            ),
            models.CheckConstraint(
                condition=Q(phase_to__gte=1) & Q(phase_to__lte=9),
                name="ck_vims_safety_incident_phase_log_phase_to_range",
            ),
        ]
        indexes = [
            models.Index(fields=("incident_id", "occurred_at"), name="ix_safe_phase_inc"),
            models.Index(fields=("actor_user_id", "occurred_at"), name="ix_safe_phase_actor"),
        ]

    def save(self, *args, **kwargs):
        if self.pk is not None and not self._state.adding:
            raise IntegrityError("Incident phase log rows are append-only.")
        self.actor_user_id = _fit_char(self.actor_user_id, MAX_ACTOR_ID_LENGTH) or "system"
        self.actor_role_code = _fit_char(self.actor_role_code, MAX_ACTOR_ROLE_CODE_LENGTH) or "SYSTEM"
        self.device_fingerprint = _fit_char(self.device_fingerprint, MAX_DEVICE_FINGERPRINT_LENGTH)
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise IntegrityError("Incident phase log rows are append-only.")
