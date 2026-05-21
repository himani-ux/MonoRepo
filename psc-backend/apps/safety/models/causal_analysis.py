from __future__ import annotations

from django.db import models

from .base import PublicIdMixin
from .fact_base import IncidentFact
from .incident import Incident


class IncidentPhase5Assessment(PublicIdMixin):
    class AnalysisTool(models.TextChoices):
        STEP = "STEP", "STEP"
        FACT_TREE = "FACT_TREE", "Fact Tree"
        ECF = "ECF", "ECF"
        BARRIER = "BARRIER", "Barrier"
        CHANGE = "CHANGE", "Change"

    incident = models.OneToOneField(Incident, on_delete=models.CASCADE, related_name="phase5_assessment")
    people_contribution_text = models.TextField(blank=True, default="")
    process_gap_text = models.TextField(blank=True, default="")
    plant_failure_text = models.TextField(blank=True, default="")
    analysis_tools_used = models.JSONField(default=list, blank=True)
    human_factors_payload = models.JSONField(default=dict, blank=True)
    confirmation_override_reason = models.TextField(blank=True, null=True)
    monocausal_justification = models.TextField(blank=True, null=True)
    schema_version = models.PositiveIntegerField(default=1)
    created_by = models.CharField(max_length=128)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_by = models.CharField(max_length=128, blank=True, null=True)
    updated_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "vims_safety_incident_phase5_assessment"


class IncidentCauseTag(PublicIdMixin):
    class CausalLayer(models.TextChoices):
        IMMEDIATE = "IMMEDIATE", "Immediate"
        INTERMEDIATE = "INTERMEDIATE", "Intermediate"
        ROOT = "ROOT", "Root"

    class AnalysisTool(models.TextChoices):
        STEP = IncidentPhase5Assessment.AnalysisTool.STEP
        FACT_TREE = IncidentPhase5Assessment.AnalysisTool.FACT_TREE
        ECF = IncidentPhase5Assessment.AnalysisTool.ECF
        BARRIER = IncidentPhase5Assessment.AnalysisTool.BARRIER
        CHANGE = IncidentPhase5Assessment.AnalysisTool.CHANGE

    incident = models.ForeignKey(Incident, on_delete=models.CASCADE, related_name="cause_tags")
    source_fact = models.ForeignKey(IncidentFact, on_delete=models.CASCADE, related_name="cause_tags")
    mscat_subcode_id = models.CharField(max_length=16)
    causal_layer = models.CharField(max_length=16, choices=CausalLayer.choices)
    analysis_tool = models.CharField(max_length=16, choices=AnalysisTool.choices)
    rationale = models.TextField()
    schema_version = models.PositiveIntegerField(default=1)
    created_by = models.CharField(max_length=128)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_by = models.CharField(max_length=128, blank=True, null=True)
    updated_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "vims_safety_cause_tag"
        indexes = [
            models.Index(fields=("incident", "causal_layer"), name="ix_vims_safety_cause_tag_layer"),
            models.Index(fields=("incident", "analysis_tool"), name="ix_vims_safety_cause_tag_tool"),
            models.Index(fields=("mscat_subcode_id",), name="ix_safe_cause_subcode"),
        ]


class IncidentSafeguardFailure(PublicIdMixin):
    incident = models.ForeignKey(Incident, on_delete=models.CASCADE, related_name="safeguard_failures")
    safeguard_name = models.CharField(max_length=256)
    design_mscat_subcode_id = models.CharField(max_length=16)
    installation_mscat_subcode_id = models.CharField(max_length=16)
    maintenance_mscat_subcode_id = models.CharField(max_length=16)
    operation_mscat_subcode_id = models.CharField(max_length=16)
    testing_mscat_subcode_id = models.CharField(max_length=16)
    override_mscat_subcode_id = models.CharField(max_length=16)
    notes = models.TextField(blank=True, default="")
    schema_version = models.PositiveIntegerField(default=1)
    created_by = models.CharField(max_length=128)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_by = models.CharField(max_length=128, blank=True, null=True)
    updated_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "vims_safety_safeguard_failure"
        indexes = [
            models.Index(fields=("incident",), name="ix_safe_sg_inc"),
        ]


class IncidentBiasGuardResponse(PublicIdMixin):
    class EvaluationState(models.TextChoices):
        UNCHECKED = "UNCHECKED", "Unchecked"
        PASSED = "PASSED", "Passed"
        WARNED = "WARNED", "Warned"
        BLOCKED = "BLOCKED", "Blocked"
        OVERRIDE = "OVERRIDE", "Override"
        JUSTIFIED = "JUSTIFIED", "Justified"
        SOFTWARN_OVERRIDE = "SOFTWARN_OVERRIDE", "Soft Warn Override"

    incident = models.ForeignKey(Incident, on_delete=models.CASCADE, related_name="bias_guard_responses")
    guard_code = models.CharField(max_length=32)
    acknowledged = models.BooleanField(default=False)
    evaluation_state = models.CharField(
        max_length=24,
        choices=EvaluationState.choices,
        default=EvaluationState.UNCHECKED,
    )
    justification = models.TextField(blank=True, null=True)
    acknowledged_by = models.CharField(max_length=128, blank=True, null=True)
    acknowledged_at = models.DateTimeField(blank=True, null=True)
    schema_version = models.PositiveIntegerField(default=1)
    created_by = models.CharField(max_length=128)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_by = models.CharField(max_length=128, blank=True, null=True)
    updated_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "vims_safety_bias_guard_response"
        constraints = [
            models.UniqueConstraint(
                fields=("incident", "guard_code"),
                name="uq_vims_safety_bias_guard_response",
            ),
        ]
        indexes = [
            models.Index(fields=("incident", "guard_code"), name="ix_safe_bias_resp"),
        ]


class IncidentBlameOverride(PublicIdMixin):
    incident = models.OneToOneField(Incident, on_delete=models.CASCADE, related_name="blame_override")
    justification = models.TextField()
    approved_by = models.CharField(max_length=128)
    approved_role = models.CharField(max_length=64)
    approved_at = models.DateTimeField()
    schema_version = models.PositiveIntegerField(default=1)
    created_by = models.CharField(max_length=128)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_by = models.CharField(max_length=128, blank=True, null=True)
    updated_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "vims_safety_blame_override"
