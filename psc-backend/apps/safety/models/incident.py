from __future__ import annotations

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q

from .base import BaseSafetyRecord

INCIDENT_ENUM_TIGHTENED_SCHEMA_VERSION = 2
INCIDENT_RECORD_TYPES = ("INCIDENT", "NEAR_MISS")
INCIDENT_ACTIVE_STATES = (
    "DRAFT",
    "SUBMITTED",
    "IN_PROGRESS",
    "UNDER_REVIEW",
    "APPROVED",
    "SENT_BACK",
    "REOPENED",
    "CLOSED",
    "PENDING_VESSEL_REVIEW",
    "READY_FOR_OFFICE_COMMENTS",
    "REWORK_REQUIRED",
    "OFFICE_COMMENTS_COMPLETED",
    "SUPERSEDED",
)
INCIDENT_RISK_BANDS = ("GREEN", "YELLOW", "RED")
INCIDENT_IMO_CLASSIFIERS = ("SMC", "MC", "MI", "NOT_APPLICABLE")
INCIDENT_INVESTIGATION_DEPTHS = ("SHALLOW", "MEDIUM", "DEEP")
NEAR_MISS_SEVERITIES = ("HIGH", "MED", "LOW")
NEAR_MISS_PLACES = ("AT_ANCHOR", "AT_SEA", "AT_PORT")


class Incident(BaseSafetyRecord):
    ENUM_TIGHTENED_SCHEMA_VERSION = INCIDENT_ENUM_TIGHTENED_SCHEMA_VERSION

    class RecordType(models.TextChoices):
        INCIDENT = "INCIDENT", "Incident"
        NEAR_MISS = "NEAR_MISS", "Near Miss"

    class State(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        SUBMITTED = "SUBMITTED", "Submitted"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        UNDER_REVIEW = "UNDER_REVIEW", "Under Review"
        APPROVED = "APPROVED", "Approved"
        SENT_BACK = "SENT_BACK", "Sent Back"
        REOPENED = "REOPENED", "Reopened"
        CLOSED = "CLOSED", "Closed"
        PENDING_VESSEL_REVIEW = "PENDING_VESSEL_REVIEW", "Pending Vessel Review"
        READY_FOR_OFFICE_COMMENTS = "READY_FOR_OFFICE_COMMENTS", "Ready for Office Comments"
        REWORK_REQUIRED = "REWORK_REQUIRED", "Rework Required"
        OFFICE_COMMENTS_COMPLETED = "OFFICE_COMMENTS_COMPLETED", "Office Comments Completed"
        SUPERSEDED = "SUPERSEDED", "Superseded"

    class RiskBand(models.TextChoices):
        GREEN = "GREEN", "Green"
        YELLOW = "YELLOW", "Yellow"
        RED = "RED", "Red"

    class ImoClassifier(models.TextChoices):
        SMC = "SMC", "Serious Marine Casualty"
        MC = "MC", "Marine Casualty"
        MI = "MI", "Marine Incident"
        NOT_APPLICABLE = "NOT_APPLICABLE", "Not Applicable"

    class InvestigationDepth(models.TextChoices):
        SHALLOW = "SHALLOW", "Shallow"
        MEDIUM = "MEDIUM", "Medium"
        DEEP = "DEEP", "Deep"

    incident_number = models.CharField(max_length=32, unique=True)
    state = models.CharField(
        max_length=48,
        choices=State.choices,
        default=State.DRAFT,
        db_index=True,
    )
    record_type = models.CharField(
        max_length=16,
        choices=RecordType.choices,
        default=RecordType.INCIDENT,
    )
    current_phase = models.PositiveSmallIntegerField(
        db_column="phase",
        default=1,
        validators=[MinValueValidator(0), MaxValueValidator(9)],
    )
    risk_band = models.CharField(
        max_length=8,
        choices=RiskBand.choices,
        null=True,
        blank=True,
    )
    imo_classifier = models.CharField(
        max_length=16,
        choices=ImoClassifier.choices,
        null=True,
        blank=True,
    )
    incident_type_id = models.IntegerField(null=True, blank=True)
    loss_type_primary_id = models.IntegerField(null=True, blank=True)
    investigation_depth = models.CharField(
        max_length=8,
        choices=InvestigationDepth.choices,
        null=True,
        blank=True,
    )
    occurred_at = models.DateTimeField(null=True, blank=True)
    reported_at = models.DateTimeField(null=True, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    position_source = models.CharField(max_length=32, null=True, blank=True)
    position_daily_report_id = models.CharField(max_length=64, null=True, blank=True)
    narrative = models.TextField(null=True, blank=True)
    awaiting_daily_report_match = models.BooleanField(default=False)
    first_hour_checklist_done = models.BooleanField(default=False)
    slack_notified_at = models.DateTimeField(null=True, blank=True)
    notification_channel_count = models.IntegerField(default=0)
    resources_allocated = models.TextField(null=True, blank=True)
    pic_user_id = models.CharField(max_length=64, null=True, blank=True)
    dpa_notified_at = models.DateTimeField(null=True, blank=True)
    fm_notified_at = models.DateTimeField(null=True, blank=True)
    office_notified_at = models.DateTimeField(null=True, blank=True)
    near_miss_priority = models.CharField(max_length=8, null=True, blank=True)
    near_miss_severity = models.CharField(max_length=8, null=True, blank=True)
    near_miss_place = models.CharField(max_length=16, null=True, blank=True)
    near_miss_shell_tag = models.CharField(max_length=32, null=True, blank=True)
    near_miss_category_tags = models.TextField(null=True, blank=True)
    near_miss_incident_type_ids = models.TextField(null=True, blank=True)
    near_miss_mscat_category_id = models.IntegerField(null=True, blank=True)
    near_miss_mscat_subcode_id = models.CharField(max_length=16, null=True, blank=True)
    near_miss_mscat_subcode_ids = models.TextField(null=True, blank=True)
    near_miss_immediate_action = models.TextField(null=True, blank=True)
    near_miss_suggestion = models.TextField(null=True, blank=True)
    near_miss_root_cause_detail = models.TextField(null=True, blank=True)
    near_miss_corrective_action = models.TextField(null=True, blank=True)
    near_miss_weather_voyage_details = models.TextField(null=True, blank=True)
    near_miss_equipment_details = models.TextField(null=True, blank=True)
    near_miss_lessons_learned = models.TextField(null=True, blank=True)
    reporter_id = models.CharField(max_length=64, null=True, blank=True)
    reporter_name = models.CharField(max_length=128, null=True, blank=True)
    reporter_rank = models.CharField(max_length=64, null=True, blank=True)
    reporter_email = models.CharField(max_length=128, null=True, blank=True)
    reporter_department = models.CharField(max_length=64, null=True, blank=True)
    reporter_device_fingerprint = models.CharField(max_length=256, null=True, blank=True)
    chain_of_custody_ok = models.BooleanField(default=False)
    marine_docs_checklist_done = models.BooleanField(default=False)
    cargo_evidence_applicable = models.BooleanField(default=False)
    health_fatigue_applicable = models.BooleanField(default=False)
    causal_layering_complete = models.BooleanField(default=False)
    alarp_attested = models.BooleanField(default=False)
    bias_guard_attestations = models.CharField(max_length=64, default="")
    blame_fixation_override_by = models.CharField(max_length=64, null=True, blank=True)
    dpa_accepted_at = models.DateTimeField(null=True, blank=True)
    dpa_accepted_by = models.CharField(max_length=64, null=True, blank=True)
    fm_approved_at = models.DateTimeField(null=True, blank=True)
    fm_approved_by = models.CharField(max_length=64, null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    closure_reason = models.TextField(null=True, blank=True)
    linked_incident_id = models.UUIDField(null=True, blank=True)
    superseded_by_id = models.UUIDField(null=True, blank=True)
    schema_version = models.PositiveIntegerField(
        default=INCIDENT_ENUM_TIGHTENED_SCHEMA_VERSION,
        db_default=INCIDENT_ENUM_TIGHTENED_SCHEMA_VERSION,
    )

    class Meta:
        db_table = "vims_safety_incident"
        ordering = ("-created_date", "-id")
        constraints = [
            models.CheckConstraint(
                condition=Q(record_type__in=INCIDENT_RECORD_TYPES),
                name="ck_vims_safety_incident_record_type",
            ),
            models.CheckConstraint(
                condition=Q(state__in=INCIDENT_ACTIVE_STATES)
                | Q(schema_version__lt=INCIDENT_ENUM_TIGHTENED_SCHEMA_VERSION),
                name="ck_vims_safety_incident_state_schema_v2",
            ),
            models.CheckConstraint(
                condition=Q(risk_band__isnull=True) | Q(risk_band__in=INCIDENT_RISK_BANDS),
                name="ck_vims_safety_incident_risk_band",
            ),
            models.CheckConstraint(
                condition=Q(imo_classifier__isnull=True)
                | Q(imo_classifier__in=INCIDENT_IMO_CLASSIFIERS),
                name="ck_vims_safety_incident_imo_classifier",
            ),
            models.CheckConstraint(
                condition=(
                    Q(schema_version__lt=INCIDENT_ENUM_TIGHTENED_SCHEMA_VERSION)
                    & Q(current_phase__gte=0)
                    & Q(current_phase__lte=9)
                )
                | (
                    Q(schema_version__gte=INCIDENT_ENUM_TIGHTENED_SCHEMA_VERSION)
                    & Q(current_phase__gte=1)
                    & Q(current_phase__lte=9)
                ),
                name="ck_vims_safety_incident_phase",
            ),
            models.CheckConstraint(
                condition=Q(investigation_depth__isnull=True)
                | Q(investigation_depth__in=INCIDENT_INVESTIGATION_DEPTHS)
                | Q(schema_version__lt=INCIDENT_ENUM_TIGHTENED_SCHEMA_VERSION),
                name="ck_vims_safety_incident_depth_schema_v2",
            ),
            models.CheckConstraint(
                condition=Q(near_miss_severity__isnull=True) | Q(near_miss_severity__in=NEAR_MISS_SEVERITIES),
                name="ck_vims_safety_incident_nm_severity",
            ),
            models.CheckConstraint(
                condition=Q(near_miss_place__isnull=True) | Q(near_miss_place__in=NEAR_MISS_PLACES),
                name="ck_vims_safety_incident_nm_place",
            ),
            models.CheckConstraint(
                condition=(Q(is_archived=False) & Q(archived_at__isnull=True))
                | (Q(is_archived=True) & Q(archived_at__isnull=False)),
                name="ck_vims_safety_incident_archive_pair",
            ),
        ]

    @property
    def draft_reference(self) -> str | None:
        if self.incident_number.startswith("DRAFT-"):
            return self.incident_number
        return None
